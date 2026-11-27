"""
EchoMind Memory Engine
Classifies, scores, retrieves, and manages long-term memories.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.ai.llm import llm_client
from app.ai.text_utils import parse_llm_json


class MemoryEngine:
    """
    Long-term memory system with five memory types.
    
    Memory Types:
    - Semantic: Facts, knowledge, concepts
    - Episodic: Personal events, experiences
    - Behavioral: Actions, decisions, habits
    - Preference: Likes, dislikes, opinions
    - Emotional: Feelings, moods, emotional reactions
    """

    def __init__(self):
        self._llm = None

    async def initialize(self):
        """Initialize LLM for memory processing."""
        llm_client.initialize()
        if llm_client.available:
            self._llm = llm_client

    async def classify_memory(self, content: str) -> Dict[str, Any]:
        """Classify content into memory type and extract metadata."""
        if self._llm:
            return await self._llm_classify(content)
        return self._heuristic_classify(content)

    def _heuristic_classify(self, content: str) -> Dict[str, Any]:
        """Heuristic memory classification."""
        lower = content.lower()

        # Detect memory type based on keywords
        emotional_words = {"feel", "felt", "happy", "sad", "angry", "excited", "frustrated", "anxious",
                          "love", "hate", "scared", "joy", "grief", "proud", "ashamed", "grateful"}
        preference_words = {"like", "prefer", "enjoy", "favorite", "dislike", "love", "hate",
                           "best", "worst", "rather", "choose", "pick"}
        behavioral_words = {"decided", "chose", "did", "went", "started", "stopped", "habit",
                           "always", "never", "routine", "practice", "action", "behave"}
        episodic_words = {"remember", "yesterday", "last", "when", "once", "happened",
                         "event", "experience", "story", "time", "met", "visited"}

        words = set(lower.split())

        scores = {
            "emotional": len(words & emotional_words),
            "preference": len(words & preference_words),
            "behavioral": len(words & behavioral_words),
            "episodic": len(words & episodic_words),
            "semantic": 1,  # Default
        }

        memory_type = max(scores, key=scores.get)
        
        # Importance scoring
        importance = self._calculate_importance(content, memory_type)
        
        # Emotional valence
        positive_words = {"happy", "joy", "love", "excited", "grateful", "proud", "wonderful", "great", "amazing"}
        negative_words = {"sad", "angry", "hate", "frustrated", "anxious", "scared", "terrible", "awful", "depressed"}
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count
        emotional_valence = ((pos_count - neg_count) / total) if total > 0 else 0.0

        # Extract tags
        tags = self._extract_tags(content)

        return {
            "memory_type": memory_type,
            "importance_score": importance,
            "emotional_valence": round(emotional_valence, 3),
            "summary": content[:200] + "..." if len(content) > 200 else content,
            "tags": tags,
        }

    async def _llm_classify(self, content: str) -> Dict[str, Any]:
        """Use LLM for accurate memory classification."""
        prompt = f"""Classify this content as a memory. Return JSON:

{{
    "memory_type": "semantic|episodic|behavioral|preference|emotional",
    "importance_score": <float 0-1, how important is this memory>,
    "emotional_valence": <float -1 to 1, negative to positive>,
    "summary": "brief summary of the memory",
    "tags": ["relevant", "tags"],
    "entities": ["people", "places", "things mentioned"],
    "time_reference": "when this occurred if mentioned, else null"
}}

CONTENT:
{content[:3000]}

Return ONLY JSON."""

        try:
            response = await self._llm.complete(
                prompt,
                max_tokens=400,
                temperature=0.2,
            )
            return parse_llm_json(response, text_fields=("summary", "content"))
        except Exception:
            return self._heuristic_classify(content)

    def _calculate_importance(self, content: str, memory_type: str) -> float:
        """Calculate importance score for a memory."""
        base_scores = {
            "emotional": 0.7,
            "episodic": 0.6,
            "behavioral": 0.65,
            "preference": 0.5,
            "semantic": 0.4,
        }
        base = base_scores.get(memory_type, 0.5)

        # Boost for longer, more detailed content
        length_boost = min(len(content) / 1000, 0.2)
        
        # Boost for strong language
        strong_words = {"critical", "important", "crucial", "never", "always", "changed",
                       "transformed", "breakthrough", "milestone", "turning point", "life-changing"}
        strong_count = sum(1 for w in strong_words if w in content.lower())
        strong_boost = min(strong_count * 0.05, 0.2)

        return min(round(base + length_boost + strong_boost, 3), 1.0)

    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content."""
        # Simple keyword extraction
        tag_categories = {
            "work": {"work", "job", "career", "project", "meeting", "deadline", "boss", "team", "office"},
            "personal": {"family", "friend", "home", "relationship", "partner", "parent", "child"},
            "learning": {"learn", "study", "course", "book", "skill", "knowledge", "university", "school"},
            "health": {"health", "exercise", "workout", "diet", "sleep", "mental", "stress", "doctor"},
            "finance": {"money", "invest", "save", "spend", "budget", "salary", "debt", "financial"},
            "travel": {"travel", "trip", "visit", "country", "city", "flight", "vacation"},
            "creativity": {"create", "design", "build", "art", "write", "music", "paint"},
            "technology": {"code", "software", "app", "tech", "computer", "programming", "ai", "data"},
        }

        words = set(content.lower().split())
        tags = []
        for category, keywords in tag_categories.items():
            if words & keywords:
                tags.append(category)

        return tags[:5]

    async def summarize_memories(self, memories: List[Dict]) -> str:
        """Generate a summary across multiple memories."""
        if not memories:
            return "No memories to summarize."

        if self._llm:
            memory_texts = [m.get("content", m.get("summary", ""))[:200] for m in memories[:20]]
            prompt = f"""Summarize these memories into a coherent narrative about the person:

{chr(10).join(f'- {t}' for t in memory_texts)}

Write a brief, insightful summary (2-3 paragraphs) that captures the key themes, patterns, and personality traits revealed by these memories."""

            try:
                response = await self._llm.complete(
                prompt,
                max_tokens=500,
                temperature=0.5,
            )
                return response
            except Exception:
                pass

        return f"Collection of {len(memories)} memories spanning various topics and experiences."


memory_engine = MemoryEngine()
