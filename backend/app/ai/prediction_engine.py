"""
EchoMind Decision Prediction Engine
Predicts decisions based on personality, behavior, and past patterns.
"""

import json
from typing import Any, Dict, List
from app.core.config import settings
from app.ai.llm import llm_client
from app.ai.text_utils import parse_llm_json


class PredictionEngine:
    """
    Predicts how the user would decide in a given scenario.
    
    Uses:
    - Personality profile (Big Five, beliefs, values)
    - Behavioral patterns (risk tolerance, decision style)
    - Past decisions and their outcomes
    - Relevant memories
    """

    def __init__(self):
        self._llm = None

    async def initialize(self):
        llm_client.initialize()
        if llm_client.available:
            self._llm = llm_client

    async def predict_decision(
        self,
        scenario: str,
        personality: Dict,
        behavior: Dict,
        past_decisions: List[Dict] = None,
        relevant_memories: List[Dict] = None,
    ) -> Dict[str, Any]:
        """Predict how the user would decide in a given scenario."""

        if self._llm:
            return await self._llm_predict(scenario, personality, behavior, past_decisions, relevant_memories)
        return self._heuristic_predict(scenario, personality, behavior)

    def _heuristic_predict(self, scenario: str, personality: Dict, behavior: Dict) -> Dict[str, Any]:
        """Heuristic prediction when LLM is unavailable."""
        risk_tolerance = behavior.get("risk_tolerance", 0.5) if behavior else 0.5
        decisiveness = behavior.get("decisiveness", 0.5) if behavior else 0.5
        openness = personality.get("openness", 0.5) if personality else 0.5

        # Simple heuristic: higher risk tolerance + openness = more likely to take risks
        risk_factor = (risk_tolerance + openness) / 2

        if "startup" in scenario.lower() or "risk" in scenario.lower():
            confidence = risk_factor * 100
            if risk_factor > 0.6:
                prediction = "Based on the personality profile, this person would likely take the risk and pursue this opportunity."
            else:
                prediction = "Based on the personality profile, this person would likely be cautious and decline or seek more information."
        else:
            confidence = 55.0
            prediction = "The prediction engine needs more data to make an accurate assessment."

        return {
            "prediction_text": prediction,
            "confidence_pct": round(confidence, 1),
            "reasoning": "Based on heuristic analysis of personality traits and behavioral patterns.",
            "personality_factors": {
                "openness": openness,
                "risk_tolerance": risk_tolerance,
                "decisiveness": decisiveness,
            },
            "behavior_factors": {
                "decision_style": behavior.get("decision_style", "unknown") if behavior else "unknown",
                "risk_tolerance": risk_tolerance,
            },
        }

    async def _llm_predict(
        self,
        scenario: str,
        personality: Dict,
        behavior: Dict,
        past_decisions: List[Dict] = None,
        relevant_memories: List[Dict] = None,
    ) -> Dict[str, Any]:
        """Use LLM for sophisticated decision prediction."""

        past_str = ""
        if past_decisions:
            past_str = "\nPast Decisions:\n" + "\n".join(
                [f"- {d.get('scenario', 'N/A')}: {d.get('outcome', 'N/A')}" for d in past_decisions[:10]]
            )

        memory_str = ""
        if relevant_memories:
            memory_str = "\nRelevant Memories:\n" + "\n".join(
                [f"- {m.get('content', m.get('summary', ''))[:150]}" for m in relevant_memories[:5]]
            )

        prompt = f"""You are a decision prediction AI. Based on the following personality and behavior profile, predict how this person would decide in the given scenario.

PERSONALITY PROFILE:
{json.dumps(personality, indent=2, default=str) if personality else "Limited data available"}

BEHAVIOR PROFILE:
{json.dumps(behavior, indent=2, default=str) if behavior else "Limited data available"}
{past_str}
{memory_str}

SCENARIO: {scenario}

Analyze deeply and return JSON:
{{
    "prediction_text": "Detailed prediction of what this person would decide and why",
    "confidence_pct": <float 0-100>,
    "reasoning": "Step-by-step reasoning explaining the prediction",
    "personality_factors": {{
        "key_trait_1": "how it influences this decision",
        "key_trait_2": "how it influences this decision"
    }},
    "behavior_factors": {{
        "key_pattern_1": "how it influences this decision",
        "key_pattern_2": "how it influences this decision"
    }},
    "alternative_outcomes": [
        {{"outcome": "description", "probability": <float 0-1>}}
    ]
}}

Return ONLY JSON."""

        try:
            response = await self._llm.complete(
                prompt,
                max_tokens=1000,
                temperature=0.4,
            )
            return parse_llm_json(response, text_fields=("prediction_text", "reasoning"))
        except Exception as e:
            print(f"LLM prediction failed: {e}")
            return self._heuristic_predict(scenario, personality, behavior)


prediction_engine = PredictionEngine()
