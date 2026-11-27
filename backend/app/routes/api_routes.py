"""
EchoMind Memory, Personality, Behavior, Prediction, Simulation, Knowledge Graph, and Analytics Routes
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, delete
from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.memory import Memory, MemoryType
from app.models.personality import PersonalityProfile, BehaviorProfile
from app.models.prediction import Prediction, Simulation
from app.models.document import Document
from app.models.analytics import Analytics, MetricType
from app.models.knowledge_graph import KnowledgeGraphNode, KnowledgeGraphEdge
from app.schemas.schemas import (
    MemoryResponse, MemorySearch, MemoryStats,
    PersonalityResponse, BehaviorResponse,
    PredictionRequest, PredictionResponse, PredictionValidation,
    SimulationRequest, SimulationResponse,
    DashboardMetrics, GraphVisualization, GraphNodeResponse, GraphEdgeResponse,
)
from app.ai.prediction_engine import prediction_engine
from app.ai.simulation_engine import simulation_engine
from app.ai.embeddings import embedding_engine
from app.core.vector_store import vector_store
from app.core.neo4j import neo4j_client

# ─── Memory Routes ──────────────────────────────────────────────────────

memory_router = APIRouter(prefix="/memory", tags=["Memory Vault"])


@memory_router.get("/search")
async def search_memories(
    query: str = Query(...),
    memory_type: Optional[str] = None,
    top_k: int = 10,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Search memories using vector similarity."""
    try:
        query_embedding = await embedding_engine.generate_embedding(query)
        results = await vector_store.search_similar(user_id, query_embedding, top_k=top_k)
        return {"results": results, "query": query, "count": len(results)}
    except Exception as e:
        # Fallback to text search
        stmt = select(Memory).where(
            Memory.user_id == user_id,
            Memory.content.ilike(f"%{query}%"),
        ).limit(top_k)
        if memory_type:
            stmt = stmt.where(Memory.memory_type == memory_type)
        result = await db.execute(stmt)
        memories = result.scalars().all()
        results = [{"id": str(m.id), "content": m.content, "type": m.memory_type.value} for m in memories]
        return {"results": results, "query": query, "count": len(results)}


@memory_router.get("/timeline")
async def get_memory_timeline(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get memories as a timeline."""
    result = await db.execute(
        select(Memory)
        .where(Memory.user_id == user_id)
        .order_by(desc(Memory.created_at))
        .limit(limit)
    )
    memories = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "type": m.memory_type.value,
            "summary": m.summary or m.content[:200],
            "importance": m.importance_score,
            "emotional_valence": m.emotional_valence,
            "tags": m.tags or [],
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in memories
    ]


@memory_router.get("/stats", response_model=MemoryStats)
async def get_memory_stats(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get memory statistics."""
    total = await db.execute(
        select(func.count(Memory.id)).where(Memory.user_id == user_id)
    )
    total_count = total.scalar() or 0

    # Count by type
    by_type = {}
    for mt in MemoryType:
        count = await db.execute(
            select(func.count(Memory.id)).where(
                Memory.user_id == user_id,
                Memory.memory_type == mt,
            )
        )
        by_type[mt.value] = count.scalar() or 0

    avg_imp = await db.execute(
        select(func.avg(Memory.importance_score)).where(Memory.user_id == user_id)
    )

    return MemoryStats(
        total_memories=total_count,
        by_type=by_type,
        avg_importance=round(avg_imp.scalar() or 0, 3),
        total_access_count=0,
        oldest_memory=None,
        newest_memory=None,
    )


@memory_router.delete("/{memory_id}")
async def delete_memory(
    memory_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a memory (user-controlled)."""
    result = await db.execute(
        select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id)
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Delete from vector store if has embedding
    if memory.embedding_id:
        try:
            await vector_store.delete_embedding(user_id, memory.embedding_id)
        except Exception:
            pass

    await db.delete(memory)
    return {"status": "deleted", "id": str(memory_id)}


# ─── Personality Routes ─────────────────────────────────────────────────

personality_router = APIRouter(prefix="/personality", tags=["Personality Engine"])


@personality_router.get("/profile")
async def get_personality_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current personality profile."""
    result = await db.execute(
        select(PersonalityProfile)
        .where(PersonalityProfile.user_id == user_id)
        .order_by(desc(PersonalityProfile.version))
        .limit(1)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return {
            "status": "no_profile",
            "message": "Upload documents or conversations to build your personality profile.",
            "openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5,
            "agreeableness": 0.5, "neuroticism": 0.5,
            "tone_profile": {}, "beliefs": [], "interests": [], "values": [],
            "confidence_score": 0, "data_points_count": 0,
        }

    return {
        "id": str(profile.id),
        "version": profile.version,
        "openness": profile.openness,
        "conscientiousness": profile.conscientiousness,
        "extraversion": profile.extraversion,
        "agreeableness": profile.agreeableness,
        "neuroticism": profile.neuroticism,
        "formality_score": profile.formality_score,
        "complexity_score": profile.complexity_score,
        "vocabulary_richness": profile.vocabulary_richness,
        "tone_profile": profile.tone_profile,
        "beliefs": profile.beliefs,
        "interests": profile.interests,
        "values": profile.values,
        "communication_patterns": profile.communication_patterns,
        "confidence_score": profile.confidence_score,
        "data_points_count": profile.data_points_count,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
    }


@personality_router.get("/evolution")
async def get_personality_evolution(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get personality evolution over time."""
    result = await db.execute(
        select(PersonalityProfile)
        .where(PersonalityProfile.user_id == user_id)
        .order_by(PersonalityProfile.version)
    )
    profiles = result.scalars().all()

    return {
        "timeline": [
            {
                "version": p.version,
                "openness": p.openness,
                "conscientiousness": p.conscientiousness,
                "extraversion": p.extraversion,
                "agreeableness": p.agreeableness,
                "neuroticism": p.neuroticism,
                "confidence_score": p.confidence_score,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in profiles
        ],
        "total_versions": len(profiles),
    }


# ─── Behavior Routes ────────────────────────────────────────────────────

behavior_router = APIRouter(prefix="/behavior", tags=["Behavior Analytics"])


@behavior_router.get("/profile")
async def get_behavior_profile(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get current behavior profile."""
    result = await db.execute(
        select(BehaviorProfile)
        .where(BehaviorProfile.user_id == user_id)
        .order_by(desc(BehaviorProfile.version))
        .limit(1)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return {
            "status": "no_profile",
            "message": "Upload data to build your behavior profile.",
            "risk_tolerance": 0.5, "decisiveness": 0.5,
            "adaptability": 0.5, "persistence": 0.5, "creativity": 0.5,
            "decision_style": "unknown", "problem_solving_style": "unknown",
            "habits": [], "confidence_score": 0, "data_points_count": 0,
        }

    return {
        "id": str(profile.id),
        "version": profile.version,
        "risk_tolerance": profile.risk_tolerance,
        "decisiveness": profile.decisiveness,
        "adaptability": profile.adaptability,
        "persistence": profile.persistence,
        "creativity": profile.creativity,
        "decision_style": profile.decision_style,
        "decision_speed": profile.decision_speed,
        "problem_solving_style": profile.problem_solving_style,
        "habits": profile.habits,
        "productivity_patterns": profile.productivity_patterns,
        "work_preferences": profile.work_preferences,
        "confidence_score": profile.confidence_score,
        "data_points_count": profile.data_points_count,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
    }


# ─── Prediction Routes ──────────────────────────────────────────────────

prediction_router = APIRouter(prefix="/predict", tags=["Decision Prediction"])


@prediction_router.post("/decision")
async def predict_decision(
    data: PredictionRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Predict how the user would decide in a scenario."""
    # Load profiles
    p_result = await db.execute(
        select(PersonalityProfile).where(PersonalityProfile.user_id == user_id)
        .order_by(desc(PersonalityProfile.version))
        .limit(1)
    )
    personality = p_result.scalar_one_or_none()
    personality_dict = {
        "openness": personality.openness if personality else 0.5,
        "conscientiousness": personality.conscientiousness if personality else 0.5,
        "extraversion": personality.extraversion if personality else 0.5,
        "agreeableness": personality.agreeableness if personality else 0.5,
        "neuroticism": personality.neuroticism if personality else 0.5,
        "beliefs": personality.beliefs if personality else [],
        "values": personality.values if personality else [],
    }

    b_result = await db.execute(
        select(BehaviorProfile).where(BehaviorProfile.user_id == user_id)
        .order_by(desc(BehaviorProfile.version))
        .limit(1)
    )
    behavior = b_result.scalar_one_or_none()
    behavior_dict = {
        "risk_tolerance": behavior.risk_tolerance if behavior else 0.5,
        "decisiveness": behavior.decisiveness if behavior else 0.5,
        "decision_style": behavior.decision_style if behavior else "unknown",
    }

    prediction_result = await prediction_engine.predict_decision(
        scenario=data.scenario,
        personality=personality_dict,
        behavior=behavior_dict,
    )

    # Save prediction
    prediction = Prediction(
        user_id=user_id,
        scenario=data.scenario,
        prediction_text=prediction_result.get("prediction_text", ""),
        confidence_pct=prediction_result.get("confidence_pct", 50.0),
        reasoning=prediction_result.get("reasoning", ""),
        personality_factors=prediction_result.get("personality_factors", {}),
        behavior_factors=prediction_result.get("behavior_factors", {}),
    )
    db.add(prediction)
    await db.flush()

    return {
        "id": str(prediction.id),
        **prediction_result,
        "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
    }


@prediction_router.get("/history")
async def get_prediction_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get past predictions."""
    result = await db.execute(
        select(Prediction)
        .where(Prediction.user_id == user_id)
        .order_by(desc(Prediction.created_at))
        .limit(limit)
    )
    predictions = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "scenario": p.scenario,
            "prediction_text": p.prediction_text,
            "confidence_pct": p.confidence_pct,
            "was_accurate": p.was_accurate,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in predictions
    ]


# ─── Simulation Routes ──────────────────────────────────────────────────

simulation_router = APIRouter(prefix="/simulate", tags=["Future Simulator"])


@simulation_router.post("/future")
async def run_simulation(
    data: SimulationRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Run a future-self simulation."""
    # Load profiles
    p_result = await db.execute(
        select(PersonalityProfile).where(PersonalityProfile.user_id == user_id)
        .order_by(desc(PersonalityProfile.version))
        .limit(1)
    )
    personality = p_result.scalar_one_or_none()
    personality_dict = {
        "openness": personality.openness if personality else 0.5,
        "conscientiousness": personality.conscientiousness if personality else 0.5,
        "extraversion": personality.extraversion if personality else 0.5,
        "agreeableness": personality.agreeableness if personality else 0.5,
        "neuroticism": personality.neuroticism if personality else 0.5,
    }

    b_result = await db.execute(
        select(BehaviorProfile).where(BehaviorProfile.user_id == user_id)
        .order_by(desc(BehaviorProfile.version))
        .limit(1)
    )
    behavior = b_result.scalar_one_or_none()
    behavior_dict = {
        "risk_tolerance": behavior.risk_tolerance if behavior else 0.5,
        "decisiveness": behavior.decisiveness if behavior else 0.5,
    }

    sim_result = await simulation_engine.run_simulation(
        simulation_type=data.simulation_type,
        params=data.params,
        personality=personality_dict,
        behavior=behavior_dict,
    )

    sim = Simulation(
        user_id=user_id,
        simulation_type=data.simulation_type,
        title=data.title,
        input_params=data.params,
        outcomes=sim_result.get("outcomes", []),
        risk_analysis=sim_result.get("risk_analysis", {}),
        timeline=sim_result.get("timeline", []),
        summary=sim_result.get("summary", ""),
    )
    db.add(sim)
    await db.flush()

    return {
        "id": str(sim.id),
        **sim_result,
        "created_at": sim.created_at.isoformat() if sim.created_at else None,
    }


@simulation_router.get("/history")
async def get_simulation_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get past simulations."""
    result = await db.execute(
        select(Simulation)
        .where(Simulation.user_id == user_id)
        .order_by(desc(Simulation.created_at))
        .limit(limit)
    )
    sims = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "type": s.simulation_type.value if hasattr(s.simulation_type, 'value') else s.simulation_type,
            "title": s.title,
            "summary": s.summary,
            "outcomes_count": len(s.outcomes) if s.outcomes else 0,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sims
    ]


# ─── Knowledge Graph Routes ─────────────────────────────────────────────

graph_router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@graph_router.get("/visualization")
async def get_graph_visualization(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get graph data for visualization."""
    nodes_result = await db.execute(
        select(KnowledgeGraphNode).where(KnowledgeGraphNode.user_id == user_id).limit(200)
    )
    nodes = nodes_result.scalars().all()

    edges_result = await db.execute(
        select(KnowledgeGraphEdge).where(KnowledgeGraphEdge.user_id == user_id).limit(500)
    )
    edges = edges_result.scalars().all()

    return {
        "nodes": [
            {
                "id": str(n.id),
                "label": n.label,
                "node_type": n.node_type.value,
                "properties": n.properties,
                "importance": n.importance_score,
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": str(e.id),
                "source": str(e.source_node_id),
                "target": str(e.target_node_id),
                "relationship_type": e.relationship_type,
                "weight": e.weight,
            }
            for e in edges
        ],
    }


@graph_router.get("/search")
async def search_graph(
    query: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Search the knowledge graph."""
    result = await db.execute(
        select(KnowledgeGraphNode)
        .where(
            KnowledgeGraphNode.user_id == user_id,
            KnowledgeGraphNode.label.ilike(f"%{query}%"),
        )
        .limit(50)
    )
    nodes = result.scalars().all()
    return [
        {"id": str(n.id), "label": n.label, "type": n.node_type.value, "importance": n.importance_score}
        for n in nodes
    ]


# ─── Analytics Routes ───────────────────────────────────────────────────

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics Dashboard"])


@analytics_router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get all dashboard metrics."""

    # Count entities
    memory_count = (await db.execute(
        select(func.count(Memory.id)).where(Memory.user_id == user_id)
    )).scalar() or 0

    doc_count = (await db.execute(
        select(func.count(Document.id)).where(Document.user_id == user_id)
    )).scalar() or 0

    prediction_count = (await db.execute(
        select(func.count(Prediction.id)).where(Prediction.user_id == user_id)
    )).scalar() or 0

    simulation_count = (await db.execute(
        select(func.count(Simulation.id)).where(Simulation.user_id == user_id)
    )).scalar() or 0

    node_count = (await db.execute(
        select(func.count(KnowledgeGraphNode.id)).where(KnowledgeGraphNode.user_id == user_id)
    )).scalar() or 0

    # Get personality profile scores
    p_result = await db.execute(
        select(PersonalityProfile).where(PersonalityProfile.user_id == user_id)
        .order_by(desc(PersonalityProfile.version))
        .limit(1)
    )
    personality = p_result.scalar_one_or_none()

    b_result = await db.execute(
        select(BehaviorProfile).where(BehaviorProfile.user_id == user_id)
        .order_by(desc(BehaviorProfile.version))
        .limit(1)
    )
    behavior = b_result.scalar_one_or_none()

    # Prediction accuracy
    accurate_predictions = (await db.execute(
        select(func.count(Prediction.id)).where(
            Prediction.user_id == user_id,
            Prediction.was_accurate == True,
        )
    )).scalar() or 0
    validated_predictions = (await db.execute(
        select(func.count(Prediction.id)).where(
            Prediction.user_id == user_id,
            Prediction.was_accurate.isnot(None),
        )
    )).scalar() or 0

    decision_accuracy = (accurate_predictions / validated_predictions * 100) if validated_predictions > 0 else 0.0

    twin_accuracy = (personality.confidence_score if personality else 0) * 50 + \
                    (behavior.confidence_score if behavior else 0) * 50

    return DashboardMetrics(
        twin_accuracy=round(twin_accuracy, 1),
        decision_accuracy=round(decision_accuracy, 1),
        personality_match=round((personality.confidence_score if personality else 0) * 100, 1),
        behavior_similarity=round((behavior.confidence_score if behavior else 0) * 100, 1),
        communication_similarity=0.0,
        total_memories=memory_count,
        total_documents=doc_count,
        total_predictions=prediction_count,
        total_simulations=simulation_count,
        knowledge_nodes=node_count,
        emotional_trend=[],
        knowledge_growth=[],
        memory_growth=[],
        recent_activity=[],
    )


# ─── Emotional Insights ─────────────────────────────────────────────────

# Dimensions the emotional engine scores; fixed order keeps the radar stable
# across refreshes instead of jumping as new emotions appear.
EMOTION_DIMENSIONS = [
    "stress", "motivation", "confidence", "frustration",
    "excitement", "contentment", "anxiety", "sadness",
]

POSITIVE_EMOTIONS = {"motivation", "confidence", "excitement", "contentment"}


@analytics_router.get("/emotions")
async def get_emotional_insights(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Emotional profile and mood timeline derived from real ingested data.

    Emotions come from `Document.extracted_emotions` (written by the ingestion
    pipeline); the mood timeline comes from memory valence over time.
    """
    docs_result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(desc(Document.uploaded_at))
        .limit(100)
    )
    docs = docs_result.scalars().all()

    # Average each emotion across every document that scored it.
    totals: dict = {k: 0.0 for k in EMOTION_DIMENSIONS}
    counts: dict = {k: 0 for k in EMOTION_DIMENSIONS}
    for doc in docs:
        emotions = (doc.extracted_emotions or {}).get("emotions", doc.extracted_emotions or {})
        if not isinstance(emotions, dict):
            continue
        for key in EMOTION_DIMENSIONS:
            value = emotions.get(key)
            if isinstance(value, (int, float)):
                totals[key] += float(value)
                counts[key] += 1

    emotion_profile = [
        {
            "emotion": key.capitalize(),
            "value": round((totals[key] / counts[key]) * 100, 1) if counts[key] else 0.0,
        }
        for key in EMOTION_DIMENSIONS
    ]

    # Mood timeline: memory valence in chronological order.
    mem_result = await db.execute(
        select(Memory)
        .where(Memory.user_id == user_id)
        .order_by(Memory.created_at)
        .limit(60)
    )
    memories = mem_result.scalars().all()

    mood_timeline = [
        {
            # Include the time: several memories usually land on the same day,
            # and a run of identical "Aug 22" ticks reads as a broken axis.
            "date": m.created_at.strftime("%b %d %H:%M") if m.created_at else f"#{i + 1}",
            "valence": round(((m.emotional_valence or 0.0) + 1) / 2, 3),  # -1..1 → 0..1
            "intensity": round(m.importance_score or 0.0, 3),
        }
        for i, m in enumerate(memories)
    ]

    positive = sum(totals[k] for k in POSITIVE_EMOTIONS)
    negative = sum(totals[k] for k in totals if k not in POSITIVE_EMOTIONS)
    scored = sum(counts.values())

    if not scored:
        mood, trend = "unknown", "insufficient data"
    elif positive > negative * 1.2:
        mood, trend = "positive", "improving"
    elif negative > positive * 1.2:
        mood, trend = "strained", "needs attention"
    else:
        mood, trend = "balanced", "steady"

    def level(value: float) -> str:
        return "high" if value > 0.6 else "moderate" if value > 0.3 else "low"

    stress_avg = (totals["stress"] / counts["stress"]) if counts["stress"] else 0.0
    energy_avg = (totals["motivation"] / counts["motivation"]) if counts["motivation"] else 0.0

    return {
        "emotion_profile": emotion_profile,
        "mood_timeline": mood_timeline,
        "current_mood": mood,
        "stress_level": level(stress_avg),
        "energy_level": level(energy_avg),
        "trend": trend,
        "documents_analyzed": len(docs),
        "data_points": scored,
    }


# ─── Life Timeline ──────────────────────────────────────────────────────

def _enum_value(value) -> str:
    """SQLAlchemy Enum columns render as 'DocumentType.NOTE'; we want 'note'."""
    return str(getattr(value, "value", value) or "")


@analytics_router.get("/timeline")
async def get_life_timeline(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Real chronological history of the twin, assembled from stored records."""
    events: List[dict] = []

    docs = (await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(desc(Document.uploaded_at))
        .limit(40)
    )).scalars().all()
    for doc in docs:
        events.append({
            "date": doc.uploaded_at,
            "title": doc.title,
            "desc": f"Ingested {doc.word_count or 0} words as {_enum_value(doc.doc_type) or 'document'}.",
            "category": "learning",
            "icon": "📄",
        })

    memories = (await db.execute(
        select(Memory)
        .where(Memory.user_id == user_id)
        .order_by(desc(Memory.created_at))
        .limit(40)
    )).scalars().all()
    for mem in memories:
        events.append({
            "date": mem.created_at,
            "title": mem.summary or "Memory stored",
            "desc": f"{_enum_value(mem.memory_type).capitalize()} memory at {round((mem.importance_score or 0) * 100)}% importance.",
            "category": "knowledge",
            "icon": "◉",
        })

    predictions = (await db.execute(
        select(Prediction)
        .where(Prediction.user_id == user_id)
        .order_by(desc(Prediction.created_at))
        .limit(20)
    )).scalars().all()
    for pred in predictions:
        events.append({
            "date": pred.created_at,
            "title": (pred.scenario or "Decision predicted")[:90],
            "desc": f"Predicted with {round(pred.confidence_pct or 0)}% confidence.",
            "category": "prediction",
            "icon": "🔮",
        })

    simulations = (await db.execute(
        select(Simulation)
        .where(Simulation.user_id == user_id)
        .order_by(desc(Simulation.created_at))
        .limit(20)
    )).scalars().all()
    for sim in simulations:
        events.append({
            "date": sim.created_at,
            "title": sim.title or "Future simulated",
            "desc": f"Ran a {_enum_value(sim.simulation_type)} simulation.",
            "category": "personal",
            "icon": "🚀",
        })

    # Personality milestones: only the first and every 5th version, so a long
    # history does not drown the timeline in near-identical entries.
    profiles = (await db.execute(
        select(PersonalityProfile)
        .where(PersonalityProfile.user_id == user_id)
        .order_by(PersonalityProfile.version)
    )).scalars().all()
    for prof in profiles:
        if prof.version == 1 or prof.version % 5 == 0:
            events.append({
                "date": prof.created_at,
                "title": f"Personality profile v{prof.version}",
                "desc": f"Rebuilt from {prof.data_points_count} data points at {round((prof.confidence_score or 0) * 100)}% confidence.",
                "category": "system",
                "icon": "🧠",
            })

    events = [e for e in events if e["date"] is not None]
    events.sort(key=lambda e: e["date"], reverse=True)

    return [
        {
            "date": e["date"].strftime("%Y-%m-%d"),
            "time": e["date"].strftime("%H:%M"),
            "title": e["title"],
            "desc": e["desc"],
            "category": e["category"],
            "icon": e["icon"],
        }
        for e in events[:60]
    ]


# ─── LLM Status ─────────────────────────────────────────────────────────

@analytics_router.get("/llm-status")
async def get_llm_status(user_id: str = Depends(get_current_user_id)):
    """Which LLM provider is serving requests, and whether Ollama is up.

    Lets the UI say "running on Ollama" or "running on local heuristics"
    instead of leaving the user guessing why answers look basic.
    """
    from app.ai.llm import llm_client

    status = await llm_client.health()
    status["mode"] = "llm" if status["active_provider"] else "heuristics"
    return status
