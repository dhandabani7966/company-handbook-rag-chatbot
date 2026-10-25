"""
backend/vectordb/vector_store.py
Persistent ChromaDB vector store matching Colab Module 7 & 8 specifications.
Saves vectors, text, and 1-indexed page metadata locally under data/chroma_db/.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from backend.utils.helpers import get_project_root, ensure_directory, load_config

_client_instance = None
_collection_instance = None


class ChromaVectorStore:
    """Manages persistent ChromaDB collection storage, batching, and querying."""

    def __init__(self, db_dir: Optional[str] = None, collection_name: Optional[str] = None):
        config = load_config()
        root = get_project_root()
        
        rel_db_dir = db_dir or config.get("storage", {}).get("chroma_db_dir", "data/chroma_db")
        self.persist_dir = str(ensure_directory(root / rel_db_dir))
        self.collection_name = collection_name or config.get("storage", {}).get("collection_name", "company_handbook")

        # Persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def get_chunk_count(self) -> int:
        """Return the current number of stored chunks."""
        try:
            return self.collection.count()
        except Exception:
            try:
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                return self.collection.count()
            except Exception:
                return 0

    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        clear_existing: bool = True,
        batch_size: int = 50
    ) -> int:
        """
        Store chunks and embeddings in ChromaDB using batches of 50 as in Colab Module 8.
        """
        if not chunks or not embeddings:
            return 0

        if clear_existing:
            try:
                self.client.delete_collection(name=self.collection_name)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

        total_chunks = len(chunks)
        for start in range(0, total_chunks, batch_size):
            end = min(start + batch_size, total_chunks)
            batch_chunks = chunks[start:end]
            batch_embeddings = embeddings[start:end]

            batch_ids = [
                item.get("chunk_id", f"chunk_{i}")
                for i, item in enumerate(batch_chunks, start=start)
            ]
            batch_documents = [item["text"] for item in batch_chunks]
            batch_metadatas = [
                {
                    "page": int(item["page"]),
                    "source": str(item.get("source", "handbook.pdf")),
                    "section_heading": str(item.get("section_heading", "Policy Section")),
                    "chunk_id": str(item.get("chunk_id", f"chunk_{start + i}"))
                }
                for i, item in enumerate(batch_chunks)
            ]

            self.collection.add(
                ids=batch_ids,
                documents=batch_documents,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas
            )

        return self.collection.count()

    def query(self, query_embedding: List[float], top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieve the passages most relevant to the question vector.
        Matches Colab Module 11 retrieval.
        """
        count = self.collection.count()
        if count == 0:
            return []

        n_results = min(top_k, count)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        ids = results.get("ids", [[]])[0] if "ids" in results else []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] if "distances" in results else [0.0] * len(docs)

        retrieved: List[Dict[str, Any]] = []
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
            chunk_id = ids[i] if i < len(ids) else meta.get("chunk_id", f"chunk_{i}")
            retrieved.append({
                "id": chunk_id,
                "chunk_id": chunk_id,
                "page": int(meta.get("page", 1)),
                "text": doc,
                "source": meta.get("source", "handbook.pdf"),
                "section_heading": meta.get("section_heading", "Policy Section"),
                "distance": float(dist) if dist is not None else 0.0,
            })

        return retrieved

    def get_chunks_for_page(self, page: int, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all stored chunks for a specific 1-indexed PDF page and optional source.
        Allows assembling the full section text when an excerpt is truncated or spans chunks.
        """
        try:
            if source:
                where_filter = {
                    "$and": [
                        {"page": int(page)},
                        {"source": str(source)}
                    ]
                }
            else:
                where_filter = {"page": int(page)}

            results = self.collection.get(
                where=where_filter,
                include=["documents", "metadatas"]
            )
            docs = results.get("documents", [])
            metas = results.get("metadatas", [])
            ids = results.get("ids", [])
            chunks: List[Dict[str, Any]] = []
            for doc_id, doc, meta in zip(ids, docs, metas):
                chunks.append({
                    "chunk_id": doc_id,
                    "page": int(meta.get("page", page)),
                    "text": doc,
                    "source": meta.get("source", "handbook.pdf"),
                    "distance": 0.0,
                })
            return chunks
        except Exception:
            return []



def get_vector_store() -> ChromaVectorStore:
    """Singleton getter for vector store."""
    global _client_instance
    if _client_instance is None:
        _client_instance = ChromaVectorStore()
    return _client_instance
