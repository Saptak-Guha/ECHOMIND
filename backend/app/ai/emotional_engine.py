"""
EchoMind Emotional Intelligence Engine
Detects emotions, tracks mood, and identifies behavioral changes.
"""

import json
from typing import Any, Dict, List
from app.core.config import settings
from app.ai.llm import llm_client
from app.ai.text_utils import tokenize, token_set, parse_llm_json


class EmotionalEngine:
    """
    Emotional intelligence engine that detects and tracks emotional states.
    
    Detects: stress, motivation, confidence, frustration, excitement
    Generates: mood profiles, emotional timelines, behavioral change alerts
    """

    def __init__(self):
        self._llm = None

    async def initialize(self):
        llm_client.initialize()
        if llm_client.available:
            self._llm = llm_client

    async def analyze_emotion(self, text: str) -> Dict[str, Any]:
        """Analyze emotional content of text."""
        if self._llm:
            return await self._llm_analyze(text)
        return self._heuristic_analyze(text)

    def _heuristic_analyze(self, text: str) -> Dict[str, Any]:
        """Heuristic emotion detection."""
        lower = text.lower()
        words = token_set(text)

        emotion_lexicon = {
            "stress": {"stress", "overwhelmed", "pressure", "deadline", "exhausted", "burned", "burnout", "overworked", "tense"},
            "motivation": {"motivated", "inspired", "driven", "excited", "passionate", "determined", "energized", "ambitious", "eager"},
            "confidence": {"confident", "capable", "strong", "certain", "sure", "competent", "skilled", "proud", "accomplished"},
            "frustration": {"frustrated", "annoyed", "stuck", "blocked", "angry", "irritated", "disappointed", "failed", "struggling"},
            "excitement": {"excited", "thrilled", "amazing", "wonderful", "fantastic", "incredible", "awesome", "stoked", "pumped"},
            "sadness": {"sad", "depressed", "lonely", "loss", "grief", "crying", "hopeless", "empty", "heartbroken"},
            "anxiety": {"anxious", "worried", "nervous", "afraid", "panic", "dread", "uneasy", "uncertain", "fearful"},
            "contentment": {"content", "peaceful", "calm", "satisfied", "grateful", "blessed", "happy", "relaxed", "serene"},
        }

        emotions = {}
        for emotion, keywords in emotion_lexicon.items():
            matches = words & keywords
            score = min(len(matches) / 3, 1.0) if matches else 0.0
            emotions[emotion] = round(score, 3)

        # Overall valence
        positive = emotions.get("motivation", 0) + emotions.get("confidence", 0) + emotions.get("excitement", 0) + emotions.get("contentment", 0)
        negative = emotions.get("stress", 0) + emotions.get("frustration", 0) + emotions.get("sadness", 0) + emotions.get("anxiety", 0)
        total = positive + negative
        valence = ((positive - negative) / total) if total > 0 else 0.0

        # Dominant emotion
        dominant = max(emotions, key=emotions.get) if any(v > 0 for v in emotions.values()) else "neutral"

        return {
            "emotions": emotions,
            "dominant_emotion": dominant,
            "valence": round(valence, 3),
            "intensity": round(max(emotions.values()) if emotions else 0, 3),
            "mood_label": self._get_mood_label(dominant, valence),
        }

    def _get_mood_label(self, dominant: str, valence: float) -> str:
        """Get a human-readable mood label."""
        if valence > 0.5:
            return "Very Positive"
        elif valence > 0.2:
            return "Positive"
        elif valence > -0.2:
            return "Neutral"
        elif valence > -0.5:
            return "Negative"
        else:
            return "Very Negative"

    async def _llm_analyze(self, text: str) -> Dict[str, Any]:
        """Use LLM for nuanced emotion analysis."""
        prompt = f"""Analyze the emotional content of this text. Return JSON:

{{
    "emotions": {{
        "stress": <float 0-1>,
        "motivation": <float 0-1>,
        "confidence": <float 0-1>,
        "frustration": <float 0-1>,
        "excitement": <float 0-1>,
        "sadness": <float 0-1>,
        "anxiety": <float 0-1>,
        "contentment": <float 0-1>
    }},
    "dominant_emotion": "the strongest emotion detected",
    "valence": <float -1 to 1>,
    "intensity": <float 0-1>,
    "mood_label": "a human-readable mood label",
    "emotional_triggers": ["what caused these emotions"],
    "coping_indicators": ["any coping mechanisms observed"]
}}

TEXT: {text[:3000]}

Return ONLY JSON."""

        try:
            response = await self._llm.complete(
                prompt,
                max_tokens=500,
                temperature=0.3,
            )
            return parse_llm_json(response)
        except Exception:
            return self._heuristic_analyze(text)

    async def generate_mood_profile(self, emotion_history: List[Dict]) -> Dict[str, Any]:
        """Generate a mood profile from emotional history."""
        if not emotion_history:
            return {"current_mood": {}, "trend": "stable", "changes": []}

        # Average emotions across history
        avg_emotions = {}
        for entry in emotion_history:
            emotions = entry.get("emotions", {})
            for emotion, score in emotions.items():
                if emotion not in avg_emotions:
                    avg_emotions[emotion] = []
                avg_emotions[emotion].append(score)

        current_mood = {k: round(sum(v) / len(v), 3) for k, v in avg_emotions.items()}

        # Detect trend
        if len(emotion_history) >= 2:
            recent = emotion_history[-1].get("valence", 0)
            older = emotion_history[0].get("valence", 0)
            if recent - older > 0.2:
                trend = "improving"
            elif older - recent > 0.2:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "current_mood": current_mood,
            "trend": trend,
            "dominant_emotion": max(current_mood, key=current_mood.get) if current_mood else "neutral",
            "data_points": len(emotion_history),
        }


emotional_engine = EmotionalEngine()
