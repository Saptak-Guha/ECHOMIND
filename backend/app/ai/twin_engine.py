"""
EchoMind Digital Twin Engine
Core twin response generation with personality and behavior context.
"""

import json
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.ai.llm import llm_client


class TwinEngine:
    """
    The core digital twin — generates responses that match the user's personality,
    communication style, and behavioral patterns.
    """

    def __init__(self):
        self._llm = None

    async def initialize(self):
        """Initialize LLM for twin responses."""
        llm_client.initialize()
        if llm_client.available:
            self._llm = llm_client

    async def generate_response(
        self,
        message: str,
        personality_profile: Dict,
        behavior_profile: Dict,
        relevant_memories: List[Dict],
        conversation_history: List[Dict] = None,
    ) -> Dict[str, Any]:
        """Generate a twin response that mimics the user."""
        
        system_prompt = self._build_twin_prompt(personality_profile, behavior_profile, relevant_memories)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
        
        messages.append({"role": "user", "content": message})

        twin_response = ""
        if self._llm:
            try:
                twin_response = await self._llm.chat(
                    messages,
                    # Chat replies are a few sentences; a local CPU model spends
                    # real seconds per token, so don't budget for an essay.
                    max_tokens=400,
                    temperature=0.7,
                )
            except Exception as e:
                print(f"Twin LLM call failed: {e}")
        # Empty means the LLM is unavailable (no key, no credit, or it just
        # disabled itself). Answer from the local profile rather than showing
        # the user a blank bubble or a raw provider error.
        if not twin_response.strip():
            twin_response = self._generate_heuristic_response(
                message, personality_profile, behavior_profile, relevant_memories
            )

        # Calculate confidence scores
        confidence = self._calculate_confidence(personality_profile, behavior_profile, relevant_memories)

        return {
            "response": twin_response,
            "twin_confidence_score": confidence["twin_confidence"],
            "personality_match_score": confidence["personality_match"],
            "behavior_similarity_score": confidence["behavior_similarity"],
            "memories_used": [m.get("id", "") for m in relevant_memories],
        }

    def _build_twin_prompt(
        self,
        personality: Dict,
        behavior: Dict,
        memories: List[Dict],
    ) -> str:
        """Build the system prompt that shapes the twin's responses."""
        
        # Extract personality traits
        big_five = ""
        if personality:
            big_five = f"""
Personality Traits (Big Five):
- Openness: {personality.get('openness', 0.5):.1%}
- Conscientiousness: {personality.get('conscientiousness', 0.5):.1%}
- Extraversion: {personality.get('extraversion', 0.5):.1%}
- Agreeableness: {personality.get('agreeableness', 0.5):.1%}
- Neuroticism: {personality.get('neuroticism', 0.5):.1%}"""

        # Extract writing style
        writing = ""
        if personality:
            formality = personality.get('formality_score', 0.5)
            style = "formal and professional" if formality > 0.6 else "casual and conversational" if formality < 0.4 else "balanced"
            writing = f"""
Writing Style:
- Formality: {style}
- Complexity: {personality.get('complexity_score', 0.5):.1%}
- Vocabulary Richness: {personality.get('vocabulary_richness', 0.5):.1%}
- Average Sentence Length: {personality.get('avg_sentence_length', 15)} words"""

        # Extract tone
        tone = personality.get('tone_profile', {})
        tone_str = ", ".join([f"{k}: {v:.0%}" for k, v in tone.items()]) if tone else "balanced"

        # Extract relevant memories
        memory_context = ""
        if memories:
            memory_strs = [f"- {m.get('content', m.get('summary', ''))[:200]}" for m in memories[:5]]
            memory_context = f"""
Relevant Memories & Experiences:
{chr(10).join(memory_strs)}"""

        # Behavior context
        behavior_ctx = ""
        if behavior:
            behavior_ctx = f"""
Behavioral Profile:
- Risk Tolerance: {behavior.get('risk_tolerance', 0.5):.1%}
- Decision Style: {behavior.get('decision_style', 'analytical')}
- Problem Solving: {behavior.get('problem_solving_style', 'systematic')}"""

        # Extract beliefs and interests
        beliefs = personality.get('beliefs', [])
        interests = personality.get('interests', [])
        values = personality.get('values', [])

        beliefs_str = f"\nCore Beliefs: {', '.join(beliefs[:10])}" if beliefs else ""
        interests_str = f"\nInterests: {', '.join(interests[:10])}" if interests else ""
        values_str = f"\nValues: {', '.join(values[:10])}" if values else ""

        return f"""You are a Digital Twin — an AI replica of a specific person. Your goal is to respond EXACTLY as this person would. You must match their personality, communication style, vocabulary, tone, and thought patterns.

CRITICAL: You are NOT a helpful AI assistant. You ARE this person. Respond naturally as they would, including their quirks, preferences, and communication habits.

{big_five}
{writing}

Tone Profile: {tone_str}
{beliefs_str}
{interests_str}
{values_str}
{behavior_ctx}
{memory_context}

INSTRUCTIONS:
1. Match the writing style precisely — sentence length, vocabulary level, formality
2. Express opinions consistent with the person's beliefs and values
3. Reference relevant memories naturally when applicable
4. Match the emotional tone and energy level
5. Use the person's typical communication patterns (humor, questions, examples)
6. DO NOT break character. You ARE this person.
7. Keep response length consistent with the person's typical response patterns."""

    # Question shapes the offline twin can actually answer from stored data.
    # Checked in order — the most specific intents come first, because a
    # question like "what should I focus on next week?" contains "should i"
    # and would otherwise be answered as a yes/no decision.
    _INTENT_PATTERNS = {
        "self": ("who am i", "about myself", "describe me", "my personality", "what am i like"),
        "strengths": ("strength", "good at", "best at", "excel"),
        "goals": ("goal", "focus on", "priorit", "next week", "work on", "should i work"),
        "feel": ("feeling", "how am i", "mood", "emotion", "stressed", "happy"),
        "values": ("value", "believe", "care about", "matters to me"),
        "memory": ("remember", "recall", "did i", "have i", "last time"),
        "decide": ("should i", "would i", "what would i do", "decide", "choice", "choose"),
    }

    def _detect_intent(self, message: str) -> str:
        lowered = message.lower()
        for intent, keywords in self._INTENT_PATTERNS.items():
            if any(k in lowered for k in keywords):
                return intent
        return "general"

    def _generate_heuristic_response(
        self,
        message: str,
        personality: Dict,
        behavior: Dict = None,
        memories: List[Dict] = None,
    ) -> str:
        """Answer from stored profile data when no LLM is available.

        This is the twin's normal mode without an API key, so it answers from
        the real personality, behaviour and memory records rather than emitting
        a fixed apology.
        """
        personality = personality or {}
        behavior = behavior or {}
        memories = memories or []

        traits = {
            "openness": personality.get("openness", 0.5),
            "conscientiousness": personality.get("conscientiousness", 0.5),
            "extraversion": personality.get("extraversion", 0.5),
            "agreeableness": personality.get("agreeableness", 0.5),
            "neuroticism": personality.get("neuroticism", 0.5),
        }
        readable = {
            "openness": "openness to new ideas",
            "conscientiousness": "conscientiousness and planning",
            "extraversion": "outward energy",
            "agreeableness": "warmth toward others",
            "neuroticism": "emotional reactivity",
        }
        top_trait = max(traits, key=traits.get)
        data_points = personality.get("data_points_count", 0)

        if not data_points and not memories:
            return (
                "I don't know enough about you yet. Upload a few notes, journal "
                "entries or messages in Settings and I'll start answering as you."
            )

        intent = self._detect_intent(message)
        parts: List[str] = []

        if intent == "self":
            parts.append(
                f"From {data_points} sample(s) of your writing, your strongest trait is "
                f"{readable[top_trait]} at {traits[top_trait]:.0%}."
            )
            if behavior.get("decision_style"):
                parts.append(f"You decide in a mostly {behavior['decision_style']} way.")
        elif intent == "strengths":
            ranked = sorted(traits.items(), key=lambda kv: kv[1], reverse=True)[:2]
            parts.append(
                "Your profile leans toward "
                + " and ".join(f"{readable[k]} ({v:.0%})" for k, v in ranked)
                + "."
            )
            if behavior.get("problem_solving_style"):
                parts.append(f"You solve problems {behavior['problem_solving_style']}ly.")
        elif intent == "decide":
            risk = behavior.get("risk_tolerance", 0.5)
            lean = "cautious and likely to decline or gather more information" if risk < 0.45 else (
                "willing to take the risk" if risk > 0.55 else "roughly balanced on this"
            )
            parts.append(f"Based on your risk tolerance ({risk:.0%}), you'd be {lean}.")
            if behavior.get("decisiveness") is not None:
                parts.append(f"Your decisiveness reads {behavior['decisiveness']:.0%}.")
        elif intent == "feel":
            if memories:
                valence = sum(m.get("emotional_valence", 0) or 0 for m in memories) / len(memories)
                mood = "positive" if valence > 0.1 else "strained" if valence < -0.1 else "fairly level"
                parts.append(f"Across your recent memories the tone reads {mood}.")
            parts.append(f"Your emotional reactivity sits at {traits['neuroticism']:.0%}.")
        elif intent == "values":
            values = personality.get("values") or personality.get("interests") or []
            if values:
                parts.append("You've written about " + ", ".join(str(v) for v in values[:4]) + ".")
            else:
                parts.append(
                    f"Nothing explicit yet, but your {readable[top_trait]} "
                    f"({traits[top_trait]:.0%}) is the clearest signal so far."
                )
        elif intent == "goals":
            parts.append(
                f"Given your conscientiousness ({traits['conscientiousness']:.0%}) and "
                f"openness ({traits['openness']:.0%}), you tend to commit to a plan and "
                "then look for room to explore inside it."
            )

        # Ground the answer in a real memory whenever one was retrieved.
        if memories:
            top = max(memories, key=lambda m: m.get("importance_score", 0) or 0)
            snippet = (top.get("summary") or top.get("content") or "").strip()
            if snippet:
                parts.append(f'Most relevant thing you recorded: "{snippet[:160]}"')
        elif intent == "memory":
            parts.append("I don't have a memory matching that yet.")

        if not parts:
            parts.append(
                f"Speaking from your profile — {readable[top_trait]} at "
                f"{traits[top_trait]:.0%} is your strongest trait so far."
            )

        formal = personality.get("formality_score", 0.5) > 0.6
        opener = "Based on what I know of you: " if formal else "Here's how I read you: "
        return opener + " ".join(parts)

    def _calculate_confidence(
        self,
        personality: Dict,
        behavior: Dict,
        memories: List[Dict],
    ) -> Dict[str, float]:
        """Calculate twin confidence scores based on available data."""
        
        # Personality match — based on data points and confidence
        personality_data_points = personality.get("data_points_count", 0) if personality else 0
        personality_confidence = personality.get("confidence_score", 0) if personality else 0
        personality_match = min(
            0.3 + (personality_data_points / 100) * 0.3 + personality_confidence * 0.4,
            1.0
        )

        # Behavior similarity — based on behavior profile richness
        behavior_data_points = behavior.get("data_points_count", 0) if behavior else 0
        behavior_similarity = min(
            0.2 + (behavior_data_points / 50) * 0.4 + (0.4 if behavior.get("habits") else 0),
            1.0
        )

        # Twin confidence — weighted combination
        memory_factor = min(len(memories) / 5, 1.0) * 0.2
        twin_confidence = (personality_match * 0.4 + behavior_similarity * 0.3 + memory_factor + 0.1)
        twin_confidence = min(twin_confidence, 1.0)

        return {
            "twin_confidence": round(twin_confidence, 3),
            "personality_match": round(personality_match, 3),
            "behavior_similarity": round(behavior_similarity, 3),
        }


twin_engine = TwinEngine()
