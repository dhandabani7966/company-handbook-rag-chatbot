"""
backend/embeddings/embedder.py
Sentence Transformers embedder using sentence-transformers/all-MiniLM-L6-v2.
Matches Colab Module 6 implementation with normalize_embeddings=True.
"""

from typing import List
import threading

_embedder_instance = None
_embedder_lock = threading.Lock()


class SentenceTransformerEmbedder:
    """Wrapper around SentenceTransformer model with thread-safe singleton loading."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _ensure_model_loaded(self):
        if self._model is None:
            with _embedder_lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(self.model_name)

    def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Compute normalized embeddings for a list of document chunk texts."""
        if not texts:
            return []
        self._ensure_model_loaded()
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Compute normalized embedding for a single search question."""
        if not query or not query.strip():
            return []
        self._ensure_model_loaded()
        embedding = self._model.encode(
            query.strip(),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embedding.tolist()


def get_embedder(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformerEmbedder:
    """Return the global cached embedder instance."""
    global _embedder_instance
    if _embedder_instance is None:
        with _embedder_lock:
            if _embedder_instance is None:
                _embedder_instance = SentenceTransformerEmbedder(model_name=model_name)
    return _embedder_instance


def get_embeddings(text_list: List[str]) -> List[List[float]]:
    """Colab notebook compatible helper to generate normalized embeddings."""
    embedder = get_embedder()
    return embedder.embed_documents(text_list)
