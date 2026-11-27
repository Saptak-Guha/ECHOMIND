"""
EchoMind Future Self Simulator
Simulates future outcomes based on personality, behavior, and chosen paths.
"""

import json
from typing import Any, Dict, List
from app.core.config import settings
from app.ai.llm import llm_client
from app.ai.text_utils import parse_llm_json


class SimulationEngine:
    """
    Creates future-self simulations with probabilistic outcomes.
    
    Simulation Types:
    - Career Path
    - Life Decision
    - Skill Growth
    - Startup Success
    - Relationship
    - Financial
    - Health
    """

    def __init__(self):
        self._llm = None

    async def initialize(self):
        llm_client.initialize()
        if llm_client.available:
            self._llm = llm_client

    async def run_simulation(
        self,
        simulation_type: str,
        params: Dict,
        personality: Dict,
        behavior: Dict,
        relevant_memories: List[Dict] = None,
    ) -> Dict[str, Any]:
        """Run a future simulation."""

        if self._llm:
            return await self._llm_simulate(simulation_type, params, personality, behavior, relevant_memories)
        return self._heuristic_simulate(simulation_type, params, personality, behavior)

    def _heuristic_simulate(self, sim_type: str, params: Dict, personality: Dict, behavior: Dict) -> Dict[str, Any]:
        """Heuristic simulation when LLM is unavailable."""
        risk_tolerance = behavior.get("risk_tolerance", 0.5) if behavior else 0.5
        openness = personality.get("openness", 0.5) if personality else 0.5
        conscientiousness = personality.get("conscientiousness", 0.5) if personality else 0.5

        base_success = (openness * 0.3 + conscientiousness * 0.4 + risk_tolerance * 0.3)

        return {
            "outcomes": [
                {
                    "outcome": f"Favorable outcome in {sim_type}",
                    "probability": round(base_success, 2),
                    "risk_level": "moderate",
                    "details": f"Based on personality alignment and behavioral patterns, there is a {base_success:.0%} probability of a favorable outcome.",
                },
                {
                    "outcome": f"Moderate outcome in {sim_type}",
                    "probability": round(0.3, 2),
                    "risk_level": "low",
                    "details": "A moderate outcome where partial goals are achieved.",
                },
                {
                    "outcome": f"Challenging outcome in {sim_type}",
                    "probability": round(1 - base_success - 0.3, 2),
                    "risk_level": "high",
                    "details": "Significant challenges that may require adaptation.",
                },
            ],
            "risk_analysis": {
                "overall_risk": "moderate",
                "key_risks": ["Insufficient data for comprehensive risk analysis"],
                "mitigation": ["Gather more behavioral data for accurate simulation"],
            },
            "timeline": [
                {"timepoint": "3 months", "event": "Initial adjustment period", "probability": 0.9},
                {"timepoint": "6 months", "event": "First milestone checkpoint", "probability": 0.7},
                {"timepoint": "1 year", "event": "Major progress evaluation", "probability": 0.5},
            ],
            "summary": f"Simulation for {sim_type} with limited data. Add more personality and behavioral data for richer simulations.",
            "personality_influence": {
                "openness": f"{'Enables' if openness > 0.5 else 'Limits'} exploration of new paths",
                "conscientiousness": f"{'Supports' if conscientiousness > 0.5 else 'May challenge'} consistent progress",
            },
            "behavior_influence": {
                "risk_tolerance": f"{'Comfortable' if risk_tolerance > 0.5 else 'Cautious'} with uncertainty",
            },
        }

    async def _llm_simulate(
        self,
        sim_type: str,
        params: Dict,
        personality: Dict,
        behavior: Dict,
        memories: List[Dict] = None,
    ) -> Dict[str, Any]:
        """Use LLM for detailed future simulation."""

        memory_str = ""
        if memories:
            memory_str = "\nRelevant Memories:\n" + "\n".join(
                [f"- {m.get('content', m.get('summary', ''))[:150]}" for m in memories[:5]]
            )

        prompt = f"""You are a Future Self Simulator. Based on the person's profile, simulate possible future outcomes for the given scenario.

SIMULATION TYPE: {sim_type}
PARAMETERS: {json.dumps(params, indent=2)}

PERSONALITY PROFILE:
{json.dumps(personality, indent=2, default=str) if personality else "Limited data"}

BEHAVIOR PROFILE:
{json.dumps(behavior, indent=2, default=str) if behavior else "Limited data"}
{memory_str}

Generate a detailed simulation with multiple possible outcomes. Return JSON:
{{
    "outcomes": [
        {{
            "outcome": "Description of this possible outcome",
            "probability": <float 0-1>,
            "risk_level": "low|moderate|high|critical",
            "details": "Detailed explanation of why this outcome is likely"
        }}
    ],
    "risk_analysis": {{
        "overall_risk": "low|moderate|high|critical",
        "key_risks": ["list of specific risks"],
        "mitigation": ["list of risk mitigation strategies"],
        "personality_risks": ["risks specific to this personality type"]
    }},
    "timeline": [
        {{"timepoint": "time period", "event": "what happens", "probability": <float 0-1>}}
    ],
    "summary": "Executive summary of the simulation",
    "personality_influence": {{
        "trait": "how it affects this simulation"
    }},
    "behavior_influence": {{
        "pattern": "how it affects this simulation"
    }},
    "recommendations": ["personalized recommendations based on their profile"]
}}

Make outcomes realistic and specific to this person's profile. Return ONLY JSON."""

        try:
            response = await self._llm.complete(
                prompt,
                max_tokens=1500,
                temperature=0.6,
            )
            return parse_llm_json(response, text_fields=("summary", "title"))
        except Exception as e:
            print(f"LLM simulation failed: {e}")
            return self._heuristic_simulate(sim_type, params, personality, behavior)


simulation_engine = SimulationEngine()
