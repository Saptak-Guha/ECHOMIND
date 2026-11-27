"""
EchoMind Twin Chat Routes
Chat with the digital twin.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.redis import redis_client
from app.models.conversation import Conversation
from app.models.personality import PersonalityProfile, BehaviorProfile
from app.models.memory import Memory
from app.schemas.schemas import TwinMessage, TwinResponse, TwinProfile
from app.ai.twin_engine import twin_engine
from app.ai.embeddings import embedding_engine
from app.core.vector_store import vector_store

router = APIRouter(prefix="/twin", tags=["Digital Twin"])

# Words too common to identify a memory; matching on them returns noise.
_MEMORY_STOPWORDS = {
    "what", "when", "where", "which", "who", "whom", "why", "how", "the", "and",
    "for", "with", "about", "that", "this", "there", "here", "have", "has", "had",
    "did", "does", "do", "was", "were", "are", "is", "am", "been", "being", "should",
    "would", "could", "can", "will", "shall", "may", "might", "must", "from", "into",
    "over", "under", "again", "more", "most", "some", "any", "all", "you", "your",
    "me", "my", "mine", "i", "we", "our", "they", "them", "it", "its", "remember",
    "recall", "tell", "know", "think", "feel", "lately", "today", "now",
}


async def _keyword_memory_search(
    db: AsyncSession, user_id: str, message: str, limit: int = 5
) -> list:
    """Find memories by keyword when vector search yields nothing."""
    words = [
        w.strip(".,!?;:'\"()").lower()
        for w in message.split()
    ]
    terms = [w for w in words if len(w) > 3 and w not in _MEMORY_STOPWORDS][:5]

    stmt = select(Memory).where(Memory.user_id == user_id)
    if terms:
        from sqlalchemy import or_
        stmt = stmt.where(or_(*[Memory.content.ilike(f"%{t}%") for t in terms]))
    stmt = stmt.order_by(desc(Memory.importance_score)).limit(limit)

    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(m.id),
            "content": m.content,
            "summary": m.summary,
            "importance_score": m.importance_score,
            "emotional_valence": m.emotional_valence,
        }
        for m in rows
    ]


@router.post("/chat", response_model=TwinResponse)
async def chat_with_twin(
    data: TwinMessage,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Chat with the digital twin."""

    # Get or create conversation
    conversation = None
    if data.conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == data.conversation_id)
        )
        conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            user_id=user_id,
            title=data.message[:100],
            messages=[],
        )
        db.add(conversation)
        await db.flush()

    # Load personality profile
    personality_dict = {}
    if data.include_personality:
        # Try cache first
        cached = await redis_client.get_cached_personality(user_id)
        if cached:
            personality_dict = cached
        else:
            result = await db.execute(
                select(PersonalityProfile)
                .where(PersonalityProfile.user_id == user_id)
                .order_by(desc(PersonalityProfile.version))
        .limit(1)
            )
            personality = result.scalar_one_or_none()
            if personality:
                personality_dict = {
                    "openness": personality.openness,
                    "conscientiousness": personality.conscientiousness,
                    "extraversion": personality.extraversion,
                    "agreeableness": personality.agreeableness,
                    "neuroticism": personality.neuroticism,
                    "formality_score": personality.formality_score,
                    "complexity_score": personality.complexity_score,
                    "vocabulary_richness": personality.vocabulary_richness,
                    "tone_profile": personality.tone_profile,
                    "beliefs": personality.beliefs,
                    "interests": personality.interests,
                    "values": personality.values,
                    "communication_patterns": personality.communication_patterns,
                    "data_points_count": personality.data_points_count,
                    "confidence_score": personality.confidence_score,
                }
                await redis_client.cache_personality(user_id, personality_dict)

    # Load behavior profile
    behavior_dict = {}
    result = await db.execute(
        select(BehaviorProfile)
        .where(BehaviorProfile.user_id == user_id)
        .order_by(desc(BehaviorProfile.version))
        .limit(1)
    )
    behavior = result.scalar_one_or_none()
    if behavior:
        behavior_dict = {
            "risk_tolerance": behavior.risk_tolerance,
            "decisiveness": behavior.decisiveness,
            "decision_style": behavior.decision_style,
            "problem_solving_style": behavior.problem_solving_style,
            "habits": behavior.habits,
            "data_points_count": behavior.data_points_count,
            "confidence_score": behavior.confidence_score,
        }

    # Retrieve relevant memories
    relevant_memories = []
    if data.include_memory:
        try:
            query_embedding = await embedding_engine.generate_embedding(data.message)
            relevant_memories = await vector_store.search_similar(
                user_id, query_embedding, top_k=5
            )
        except Exception as e:
            print(f"Vector memory search failed: {e}")

        # Vector search returns nothing when the store is empty or its vectors
        # were written by a different embedding model. Fall back to keyword
        # matching so the twin can still ground answers in real memories.
        if not relevant_memories:
            relevant_memories = await _keyword_memory_search(db, user_id, data.message)

    # Generate twin response
    twin_result = await twin_engine.generate_response(
        message=data.message,
        personality_profile=personality_dict,
        behavior_profile=behavior_dict,
        relevant_memories=relevant_memories,
        conversation_history=conversation.messages,
    )

    # Update conversation
    conversation.messages.append({"role": "user", "content": data.message})
    conversation.messages.append({"role": "twin", "content": twin_result["response"]})
    conversation.twin_confidence_score = twin_result["twin_confidence_score"]
    conversation.personality_match_score = twin_result["personality_match_score"]
    conversation.behavior_similarity_score = twin_result["behavior_similarity_score"]
    conversation.message_count = len(conversation.messages)
    conversation.personality_context = personality_dict

    # Force update for JSON field
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(conversation, "messages")

    return TwinResponse(
        response=twin_result["response"],
        conversation_id=conversation.id,
        twin_confidence_score=twin_result["twin_confidence_score"],
        personality_match_score=twin_result["personality_match_score"],
        behavior_similarity_score=twin_result["behavior_similarity_score"],
        memories_used=twin_result.get("memories_used", []),
        personality_context=personality_dict,
    )


@router.get("/profile", response_model=TwinProfile)
async def get_twin_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get the digital twin's accuracy profile."""

    result = await db.execute(
        select(PersonalityProfile)
        .where(PersonalityProfile.user_id == user_id)
        .order_by(desc(PersonalityProfile.version))
        .limit(1)
    )
    personality = result.scalar_one_or_none()

    result = await db.execute(
        select(BehaviorProfile)
        .where(BehaviorProfile.user_id == user_id)
        .order_by(desc(BehaviorProfile.version))
        .limit(1)
    )
    behavior = result.scalar_one_or_none()

    return TwinProfile(
        overall_accuracy=max(
            (personality.confidence_score if personality else 0) * 0.5 +
            (behavior.confidence_score if behavior else 0) * 0.5,
            0.0,
        ),
        personality_match=personality.confidence_score if personality else 0,
        behavior_similarity=behavior.confidence_score if behavior else 0,
        communication_similarity=0.0,
        data_points=(personality.data_points_count if personality else 0) +
                    (behavior.data_points_count if behavior else 0),
        last_updated=personality.updated_at if personality else None,
    )


@router.get("/conversations")
async def get_conversations(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get recent conversations with the twin."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(desc(Conversation.created_at))
        .limit(limit)
    )
    conversations = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "title": c.title,
            "message_count": c.message_count,
            "twin_confidence_score": c.twin_confidence_score,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in conversations
    ]
