"""
EchoMind Communication Cloning Engine
Learns and replicates the user's unique communication style.
"""

import json
import re
from typing import Any, Dict, List
from app.core.config import settings
from app.ai.llm import llm_client


class CommunicationEngine:
    """
    Learns the user's communication fingerprint and generates style-matched text.
    
    Learns: writing style, language patterns, humor, response length, formality
    """

    def __init__(self):
        self._llm = None

    async def initialize(self):
        llm_client.initialize()
        if llm_client.available:
            self._llm = llm_client

    def extract_communication_fingerprint(self, texts: List[str]) -> Dict[str, Any]:
        """Extract a comprehensive communication fingerprint from multiple texts."""
        if not texts:
            return self._empty_fingerprint()

        all_words = []
        all_sentences = []
        total_exclamations = 0
        total_questions = 0
        total_emojis = 0
        total_contractions = 0
        total_uppercase_words = 0

        contraction_pattern = re.compile(r"\b\w+'\w+\b")
        emoji_pattern = re.compile(r"[\U0001f600-\U0001f650\U0001f680-\U0001f6ff\U0001f900-\U0001f9ff\u2600-\u26ff\u2700-\u27bf]")

        for text in texts:
            words = text.split()
            all_words.extend(words)
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            all_sentences.extend(sentences)
            total_exclamations += text.count("!")
            total_questions += text.count("?")
            total_emojis += len(emoji_pattern.findall(text))
            total_contractions += len(contraction_pattern.findall(text))
            total_uppercase_words += sum(1 for w in words if w.isupper() and len(w) > 1)

        total_words = len(all_words)
        total_sentences_count = len(all_sentences)

        # Response length patterns
        text_lengths = [len(t.split()) for t in texts]
        avg_response_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        length_category = "short" if avg_response_length < 30 else "long" if avg_response_length > 100 else "medium"

        # Sentence structure
        avg_sentence_length = total_words / max(total_sentences_count, 1)
        sentence_lengths = [len(s.split()) for s in all_sentences]
        sentence_length_variance = self._variance(sentence_lengths) if sentence_lengths else 0

        # Punctuation style
        exclamation_rate = total_exclamations / max(total_sentences_count, 1)
        question_rate = total_questions / max(total_sentences_count, 1)

        # Vocabulary analysis
        unique_words = set(w.lower().strip(".,!?;:'\"") for w in all_words)
        vocabulary_diversity = len(unique_words) / max(total_words, 1)

        # Common phrases (bigrams)
        bigrams = {}
        lower_words = [w.lower().strip(".,!?;:'\"") for w in all_words]
        for i in range(len(lower_words) - 1):
            bigram = f"{lower_words[i]} {lower_words[i+1]}"
            bigrams[bigram] = bigrams.get(bigram, 0) + 1
        top_phrases = dict(sorted(bigrams.items(), key=lambda x: x[1], reverse=True)[:15])

        return {
            "avg_response_length": round(avg_response_length, 1),
            "response_length_category": length_category,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "sentence_length_variance": round(sentence_length_variance, 2),
            "vocabulary_diversity": round(vocabulary_diversity, 4),
            "exclamation_rate": round(exclamation_rate, 3),
            "question_rate": round(question_rate, 3),
            "contraction_rate": round(total_contractions / max(total_words, 1), 4),
            "emoji_usage": total_emojis > 0,
            "emoji_rate": round(total_emojis / max(len(texts), 1), 3),
            "uppercase_emphasis": total_uppercase_words > 0,
            "formality_level": self._calculate_formality(total_contractions, total_words, avg_sentence_length),
            "top_phrases": top_phrases,
            "sample_count": len(texts),
            "total_words_analyzed": total_words,
        }

    def _calculate_formality(self, contractions: int, total_words: int, avg_sentence_length: float) -> str:
        """Calculate formality level."""
        contraction_rate = contractions / max(total_words, 1)
        if contraction_rate > 0.05 or avg_sentence_length < 10:
            return "informal"
        elif contraction_rate < 0.01 and avg_sentence_length > 20:
            return "formal"
        return "balanced"

    def _variance(self, values: List[float]) -> float:
        """Calculate variance of a list of numbers."""
        if not values:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)

    def _empty_fingerprint(self) -> Dict[str, Any]:
        """Return an empty fingerprint template."""
        return {
            "avg_response_length": 0,
            "response_length_category": "unknown",
            "avg_sentence_length": 0,
            "sentence_length_variance": 0,
            "vocabulary_diversity": 0,
            "exclamation_rate": 0,
            "question_rate": 0,
            "contraction_rate": 0,
            "emoji_usage": False,
            "emoji_rate": 0,
            "uppercase_emphasis": False,
            "formality_level": "unknown",
            "top_phrases": {},
            "sample_count": 0,
            "total_words_analyzed": 0,
        }

    async def style_transfer(self, content: str, fingerprint: Dict) -> str:
        """Rewrite content to match the user's communication style."""
        if not self._llm:
            return content

        prompt = f"""Rewrite the following content to match this person's communication style:

COMMUNICATION FINGERPRINT:
- Response Length: {fingerprint.get('response_length_category', 'medium')}
- Formality: {fingerprint.get('formality_level', 'balanced')}
- Avg Sentence Length: {fingerprint.get('avg_sentence_length', 15)} words
- Uses Exclamations: {'Yes' if fingerprint.get('exclamation_rate', 0) > 0.1 else 'Rarely'}
- Uses Questions: {'Yes' if fingerprint.get('question_rate', 0) > 0.1 else 'Rarely'}
- Uses Emojis: {'Yes' if fingerprint.get('emoji_usage', False) else 'No'}
- Uses Contractions: {'Frequently' if fingerprint.get('contraction_rate', 0) > 0.03 else 'Rarely'}

ORIGINAL CONTENT:
{content}

Rewrite to match the style. Keep the meaning but change the delivery to sound like this person."""

        try:
            response = await self._llm.complete(
                prompt,
                max_tokens=500,
                temperature=0.7,
            )
            return response
        except Exception:
            return content


communication_engine = CommunicationEngine()
