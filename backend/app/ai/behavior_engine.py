"""
EchoMind Behavioral Modeling Engine
Learns decision patterns, habits, risk tolerance, and work preferences.
"""

import json
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.ai.llm import llm_client
from app.ai.text_utils import tokenize, token_set, parse_llm_json


class BehaviorEngine:
    """
    Analyzes behavior patterns from user data.
    
    Capabilities:
    - Decision pattern recognition
    - Risk tolerance scoring
    - Problem-solving style classification
    - Habit detection
    - Productivity pattern analysis
    """

    def __init__(self):
        self._llm = None

    async def initialize(self):
        """Initialize LLM for behavior analysis."""
        llm_client.initialize()
        if llm_client.available:
            self._llm = llm_client

    async def analyze_behavior(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """Run behavioral analysis on text data."""
        if self._llm:
            return await self._llm_behavior_analysis(text, context)
        return self._heuristic_behavior_analysis(text)

    def _heuristic_behavior_analysis(self, text: str) -> Dict[str, Any]:
        """Heuristic behavioral analysis when LLM is unavailable."""
        lower = text.lower()
        words = tokenize(text)

        # Risk tolerance
        risk_seeking = {"risk", "bold", "adventure", "chance", "bet", "dare", "ambitious", "gamble", "leap"}
        risk_averse = {"safe", "careful", "secure", "conservative", "cautious", "stable", "reliable", "proven"}
        risk_seek_count = sum(1 for w in words if w in risk_seeking)
        risk_averse_count = sum(1 for w in words if w in risk_averse)
        total_risk = risk_seek_count + risk_averse_count
        risk_tolerance = (risk_seek_count / total_risk) if total_risk > 0 else 0.5

        # Decisiveness
        decisive_words = {"decided", "chose", "committed", "determined", "resolved", "settled"}
        indecisive_words = {"maybe", "perhaps", "unsure", "considering", "debating", "uncertain", "hesitant"}
        dec_count = sum(1 for w in words if w in decisive_words)
        ind_count = sum(1 for w in words if w in indecisive_words)
        total_dec = dec_count + ind_count
        decisiveness = (dec_count / total_dec) if total_dec > 0 else 0.5

        # Problem-solving style
        analytical_words = {"analyze", "data", "research", "evidence", "logic", "systematic", "framework"}
        intuitive_words = {"feel", "sense", "gut", "instinct", "intuition", "hunch", "believe"}
        ana_count = sum(1 for w in words if w in analytical_words)
        int_count = sum(1 for w in words if w in intuitive_words)
        problem_solving = "analytical" if ana_count >= int_count else "intuitive"

        return {
            "risk_tolerance": round(risk_tolerance, 3),
            "decisiveness": round(decisiveness, 3),
            "adaptability": 0.5,
            "persistence": 0.5,
            "creativity": 0.5,
            "decision_style": "analytical" if ana_count > int_count else "intuitive",
            "problem_solving_style": problem_solving,
            "decision_speed": "moderate",
            "habits": [],
            "productivity_patterns": {},
            "work_preferences": {},
        }

    async def _llm_behavior_analysis(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """Use LLM for deep behavioral analysis."""
        context_str = json.dumps(context) if context else "No additional context"
        prompt = f"""Analyze the following text for behavioral patterns and decision-making style. Return a JSON object with these exact keys:

{{
    "risk_tolerance": <float 0-1, where 0=very risk-averse and 1=very risk-seeking>,
    "decisiveness": <float 0-1>,
    "adaptability": <float 0-1>,
    "persistence": <float 0-1>,
    "creativity": <float 0-1>,
    "decision_style": "<analytical|intuitive|collaborative|impulsive|deliberate>",
    "problem_solving_style": "<systematic|creative|practical|theoretical>",
    "decision_speed": "<fast|moderate|deliberate>",
    "habits": [
        {{"habit": "description", "frequency": "daily/weekly/occasional", "category": "work/personal/health"}}
    ],
    "productivity_patterns": {{
        "work_style": "<deep_focus|multitasker|sprint_rest>",
        "collaboration_preference": "<solo|pair|team>",
        "communication_style": "<async|sync|mixed>"
    }},
    "work_preferences": {{
        "environment": "<structured|flexible|chaotic>",
        "motivation": "<intrinsic|extrinsic|mixed>",
        "feedback_preference": "<frequent|periodic|minimal>"
    }}
}}

Context: {context_str}

TEXT TO ANALYZE:
{text[:4000]}

Return ONLY the JSON object."""

        try:
            response = await self._llm.complete(
                prompt,
                max_tokens=800,
                temperature=0.3,
            )
            return parse_llm_json(response, text_fields=("decision_style", "problem_solving_style"))
        except Exception as e:
            print(f"LLM behavior analysis failed: {e}")
            return self._heuristic_behavior_analysis(text)

    async def detect_decision_patterns(self, decisions: List[Dict]) -> Dict[str, Any]:
        """Analyze a list of past decisions to find patterns."""
        if not decisions:
            return {"patterns": [], "dominant_style": "unknown", "consistency": 0.0}

        if self._llm:
            prompt = f"""Analyze these decisions and identify patterns:

{json.dumps(decisions[:20], indent=2)}

Return JSON with:
{{
    "patterns": ["list of identified decision patterns"],
    "dominant_style": "the primary decision-making approach",
    "consistency": <float 0-1 how consistent the decisions are>,
    "risk_trend": "increasing/decreasing/stable",
    "decision_factors": ["what factors most influence decisions"]
}}

Return ONLY JSON."""

            try:
                response = await self._llm.complete(
                prompt,
                max_tokens=500,
                temperature=0.3,
            )
                return parse_llm_json(response, text_fields=("decision_style", "problem_solving_style"))
            except Exception:
                pass

        return {
            "patterns": ["Insufficient data for pattern detection"],
            "dominant_style": "unknown",
            "consistency": 0.5,
            "risk_trend": "stable",
            "decision_factors": [],
        }


behavior_engine = BehaviorEngine()
