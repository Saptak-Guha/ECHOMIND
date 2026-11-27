"""
EchoMind Vector Store
Dual vector store using ChromaDB (persistent) and FAISS (in-memory fast search).
"""

import os
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.core.config import settings


class VectorStore:
    """Dual vector store combining ChromaDB for persistence and FAISS for fast search."""

    def __init__(self):
        self.chroma_client = None
        self.faiss_index = None
        self.faiss_metadata: Dict[str, Dict] = {}
        self._dimension = settings.EMBEDDING_DIMENSION

    async def connect(self):
        """Initialize vector store connections."""
        import chromadb
        import faiss

        # ChromaDB — persistent storage
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

        # FAISS — in-memory fast search
        os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)
        faiss_path = os.path.join(settings.FAISS_INDEX_DIR, "echomind.index")
        if os.path.exists(faiss_path):
            self.faiss_index = faiss.read_index(faiss_path)
            meta_path = os.path.join(settings.FAISS_INDEX_DIR, "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    self.faiss_metadata = json.load(f)
        else:
            self.faiss_index = faiss.IndexFlatIP(self._dimension)  # Inner product for cosine sim

    def _get_collection(self, collection_name: str):
        """Get or create a ChromaDB collection."""
        return self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def store_embedding(
        self,
        user_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any] = None,
        collection_name: str = "memories",
    ) -> str:
        """Store an embedding in both ChromaDB and FAISS."""
        embedding_id = str(uuid.uuid4())
        meta = metadata or {}
        meta["user_id"] = user_id

        # ChromaDB — persistent
        collection = self._get_collection(f"{collection_name}_{user_id}")
        collection.add(
            ids=[embedding_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[meta],
        )

        # FAISS — fast search
        embedding_np = np.array([embedding], dtype=np.float32)
        # Normalize for cosine similarity
        faiss_module = __import__("faiss")
        faiss_module.normalize_L2(embedding_np)
        self.faiss_index.add(embedding_np)
        self.faiss_metadata[str(self.faiss_index.ntotal - 1)] = {
            "embedding_id": embedding_id,
            "user_id": user_id,
            "collection": collection_name,
        }

        return embedding_id

    async def search_similar(
        self,
        user_id: str,
        query_embedding: List[float],
        collection_name: str = "memories",
        top_k: int = 10,
    ) -> List[Dict]:
        """Search for similar embeddings using ChromaDB."""
        collection = self._get_collection(f"{collection_name}_{user_id}")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()) if collection.count() > 0 else 1,
            include=["documents", "metadatas", "distances"],
        )

        if not results["ids"][0]:
            return []

        return [
            {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
            }
            for i in range(len(results["ids"][0]))
        ]

    async def search_fast(
        self,
        query_embedding: List[float],
        top_k: int = 10,
    ) -> List[Dict]:
        """Fast similarity search using FAISS."""
        if self.faiss_index.ntotal == 0:
            return []

        query_np = np.array([query_embedding], dtype=np.float32)
        faiss_module = __import__("faiss")
        faiss_module.normalize_L2(query_np)

        scores, indices = self.faiss_index.search(query_np, min(top_k, self.faiss_index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = self.faiss_metadata.get(str(idx), {})
            results.append({
                "faiss_index": int(idx),
                "similarity": float(score),
                **meta,
            })

        return results

    async def delete_embedding(self, user_id: str, embedding_id: str, collection_name: str = "memories"):
        """Delete an embedding from ChromaDB."""
        collection = self._get_collection(f"{collection_name}_{user_id}")
        collection.delete(ids=[embedding_id])

    async def get_collection_stats(self, user_id: str, collection_name: str = "memories") -> Dict:
        """Get stats for a user's collection."""
        collection = self._get_collection(f"{collection_name}_{user_id}")
        return {
            "collection": collection_name,
            "user_id": user_id,
            "count": collection.count(),
        }

    def save_faiss_index(self):
        """Persist FAISS index to disk."""
        import faiss
        faiss_path = os.path.join(settings.FAISS_INDEX_DIR, "echomind.index")
        faiss.write_index(self.faiss_index, faiss_path)
        meta_path = os.path.join(settings.FAISS_INDEX_DIR, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump(self.faiss_metadata, f)


vector_store = VectorStore()
