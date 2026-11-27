"""
EchoMind Embedding Engine
Generates embeddings using OpenAI or Sentence Transformers.
"""

from typing import List, Optional
import numpy as np
from app.core.config import settings


class EmbeddingEngine:
    """Generates text embeddings for memory storage and similarity search."""

    def __init__(self):
        self._openai_client = None
        self._local_model = None
        # Set once OpenAI has failed for a non-transient reason (bad key, no
        # quota). Retrying every call would stall each ingest on a doomed
        # request, so we drop to the local model for the rest of the process.
        self._openai_disabled = False

    async def initialize(self):
        """Initialize embedding models."""
        if settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def _use_openai(self) -> bool:
        return self._openai_client is not None and not self._openai_disabled

    def _disable_openai(self, exc: Exception) -> None:
        """Fall back to local embeddings permanently after an API failure."""
        self._openai_disabled = True
        print(
            f"  ⚠️ OpenAI embeddings unavailable ({type(exc).__name__}: {exc}); "
            "falling back to the local sentence-transformers model."
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for a single text.

        Falls back to the local model if OpenAI is unreachable or out of quota —
        an embedding failure must never fail the whole ingestion.
        """
        if self._use_openai():
            try:
                return await self._generate_openai_embedding(text)
            except Exception as e:
                self._disable_openai(e)
        return self._generate_local_embedding(text)

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts, with the same fallback."""
        if self._use_openai():
            try:
                return await self._generate_openai_batch(texts)
            except Exception as e:
                self._disable_openai(e)
        return [self._generate_local_embedding(t) for t in texts]

    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        response = await self._openai_client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    async def _generate_openai_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings using OpenAI API."""
        # Process in batches of EMBEDDING_BATCH_SIZE
        all_embeddings = []
        for i in range(0, len(texts), settings.EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + settings.EMBEDDING_BATCH_SIZE]
            response = await self._openai_client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=batch,
            )
            all_embeddings.extend([d.embedding for d in response.data])
        return all_embeddings

    def _generate_local_embedding(self, text: str) -> List[float]:
        """Generate embedding using local sentence-transformers model (fallback)."""
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer("all-MiniLM-L6-v2")

        embedding = self._local_model.encode(text, normalize_embeddings=True)
        # Pad or truncate to match expected dimension
        result = np.zeros(settings.EMBEDDING_DIMENSION, dtype=np.float32)
        dim = min(len(embedding), settings.EMBEDDING_DIMENSION)
        result[:dim] = embedding[:dim]
        return result.tolist()

    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        a = np.array(embedding1)
        b = np.array(embedding2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


embedding_engine = EmbeddingEngine()
