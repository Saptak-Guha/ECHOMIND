"""
EchoMind Personality Learning Engine
Extracts and evolves personality profiles from user data.
"""

import json
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.ai.llm import llm_client
from app.ai.text_utils import parse_llm_json
from app.ai.text_utils import tokenize, token_set


class PersonalityEngine:
    """
    Analyzes text data to extract and evolve personality profiles.
    
    Capabilities:
    - Big Five personality scoring from text
    - Writing style extraction (sentence length, vocabulary, formality)
    - Tone classification
    - Belief/interest extraction
    - Continuous profile evolution with weighted updates
    """

    def __init__(self):
        self._llm = None

    async def initialize(self):
        """Initialize LLM for personality analysis."""
        llm_client.initialize()
        if llm_client.available:
            self._llm = llm_client

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """Run full personality analysis on a text sample."""
        writing_style = self._analyze_writing_style(text)
        
        llm_analysis = {}
        if self._llm:
            llm_analysis = await self._llm_personality_analysis(text)

        return {
            "writing_style": writing_style,
            "personality_traits": llm_analysis.get("big_five", self._heuristic_big_five(text)),
            "tone_profile": llm_analysis.get("tone_profile", self._heuristic_tone(text)),
            "beliefs": llm_analysis.get("beliefs", []),
            "interests": llm_analysis.get("interests", []),
            "values": llm_analysis.get("values", []),
            "communication_patterns": llm_analysis.get("communication_patterns", {}),
        }

    def _analyze_writing_style(self, text: str) -> Dict[str, Any]:
        """Extract writing style metrics from text."""
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        words = text.split()
        unique_words = set(w.lower() for w in words)

        avg_sentence_length = len(words) / max(len(sentences), 1)
        vocabulary_richness = len(unique_words) / max(len(words), 1)

        # Formality heuristic: ratio of formal indicators
        formal_indicators = ["therefore", "however", "furthermore", "consequently", "nevertheless",
                           "regarding", "concerning", "accordingly", "thus", "hence"]
        informal_indicators = ["like", "gonna", "wanna", "kinda", "yeah", "nah", "lol",
                             "omg", "btw", "tbh", "imo", "idk"]

        formal_count = sum(1 for w in words if w.lower() in formal_indicators)
        informal_count = sum(1 for w in words if w.lower() in informal_indicators)
        total_markers = formal_count + informal_count
        formality_score = (formal_count / total_markers) if total_markers > 0 else 0.5

        # Complexity score based on average word length
        avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
        complexity_score = min(avg_word_length / 10, 1.0)

        # Vocabulary fingerprint — top 20 most used words (excluding common stop words)
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "shall", "can", "to", "of", "in", "for",
                     "on", "with", "at", "by", "from", "it", "this", "that", "and", "or",
                     "but", "not", "i", "you", "he", "she", "we", "they", "my", "your"}
        word_freq = {}
        for w in words:
            w_lower = w.lower().strip(".,!?;:'\"")
            if w_lower and w_lower not in stop_words and len(w_lower) > 2:
                word_freq[w_lower] = word_freq.get(w_lower, 0) + 1

        top_words = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20])

        return {
            "avg_sentence_length": round(avg_sentence_length, 2),
            "vocabulary_richness": round(vocabulary_richness, 4),
            "formality_score": round(formality_score, 4),
            "complexity_score": round(complexity_score, 4),
            "avg_word_length": round(avg_word_length, 2),
            "total_words": len(words),
            "total_sentences": len(sentences),
            "unique_words": len(unique_words),
            "vocabulary_fingerprint": top_words,
        }

    def _heuristic_big_five(self, text: str) -> Dict[str, float]:
        """Heuristic Big Five scoring when LLM is not available."""
        words = tokenize(text)
        word_set = set(words)

        # Simple word-association heuristics
        openness_words = {"creative", "imagine", "idea", "explore", "curious", "novel", "innovative", "abstract", "philosophical"}
        conscientiousness_words = {"plan", "organize", "detail", "careful", "systematic", "discipline", "schedule", "efficient"}
        extraversion_words = {"people", "social", "fun", "party", "exciting", "adventure", "together", "group", "team"}
        agreeableness_words = {"help", "kind", "care", "support", "empathy", "compassion", "generous", "trust", "cooperate"}
        neuroticism_words = {"worry", "stress", "anxious", "nervous", "afraid", "upset", "frustrated", "overwhelmed", "fear"}

        def score(indicator_words):
            matches = word_set.intersection(indicator_words)
            return min(0.3 + (len(matches) / max(len(indicator_words), 1)) * 0.7, 1.0)

        return {
            "openness": round(score(openness_words), 3),
            "conscientiousness": round(score(conscientiousness_words), 3),
            "extraversion": round(score(extraversion_words), 3),
            "agreeableness": round(score(agreeableness_words), 3),
            "neuroticism": round(score(neuroticism_words), 3),
        }

    def _heuristic_tone(self, text: str) -> Dict[str, float]:
        """Heuristic tone profile when LLM is not available."""
        lower = text.lower()
        exclamation_ratio = text.count("!") / max(len(text), 1)
        question_ratio = text.count("?") / max(len(text), 1)

        return {
            "professional": 0.5,
            "casual": min(0.3 + exclamation_ratio * 100, 1.0),
            "humorous": 0.2,
            "empathetic": 0.3,
            "analytical": 0.4,
            "assertive": min(0.3 + exclamation_ratio * 50, 1.0),
            "inquisitive": min(0.2 + question_ratio * 50, 1.0),
        }

    async def _llm_personality_analysis(self, text: str) -> Dict[str, Any]:
        """Use LLM for deep personality analysis."""
        prompt = f"""Analyze the following text and extract a detailed personality profile. Return your analysis as a JSON object with these exact keys:

{{
    "big_five": {{
        "openness": <float 0-1>,
        "conscientiousness": <float 0-1>,
        "extraversion": <float 0-1>,
        "agreeableness": <float 0-1>,
        "neuroticism": <float 0-1>
    }},
    "tone_profile": {{
        "professional": <float 0-1>,
        "casual": <float 0-1>,
        "humorous": <float 0-1>,
        "empathetic": <float 0-1>,
        "analytical": <float 0-1>,
        "assertive": <float 0-1>,
        "inquisitive": <float 0-1>
    }},
    "beliefs": ["list of detected beliefs/worldviews"],
    "interests": ["list of detected interests/passions"],
    "values": ["list of detected core values"],
    "communication_patterns": {{
        "preferred_response_length": "short/medium/long",
        "uses_humor": <bool>,
        "asks_questions": <bool>,
        "uses_examples": <bool>,
        "emotion_expression": "low/moderate/high"
    }}
}}

TEXT TO ANALYZE:
{text[:4000]}

Return ONLY the JSON object, no other text."""

        try:
            response = await self._llm.complete(
                prompt,
                max_tokens=1000,
                temperature=0.3,
            )
            return parse_llm_json(
                response,
                text_fields=("decision_speed", "decision_style", "problem_solving_style"),
            )
        except Exception as e:
            print(f"LLM personality analysis failed: {e}")
            return {}

    def evolve_profile(self, current_profile: Dict, new_analysis: Dict, learning_rate: float = 0.1) -> Dict:
        """Update personality profile with new analysis using exponential moving average."""
        evolved = {}
        for key in current_profile:
            if isinstance(current_profile[key], (int, float)) and key in new_analysis:
                # Weighted average: more weight on existing profile for stability
                evolved[key] = current_profile[key] * (1 - learning_rate) + new_analysis[key] * learning_rate
            elif isinstance(current_profile[key], list) and key in new_analysis:
                # Merge lists, keeping unique items
                existing = set(current_profile[key])
                new_items = new_analysis.get(key, [])
                existing.update(new_items)
                evolved[key] = list(existing)
            elif isinstance(current_profile[key], dict) and key in new_analysis:
                # Recursively evolve nested dicts
                evolved[key] = self.evolve_profile(current_profile[key], new_analysis.get(key, {}), learning_rate)
            else:
                evolved[key] = current_profile[key]
        return evolved


personality_engine = PersonalityEngine()
