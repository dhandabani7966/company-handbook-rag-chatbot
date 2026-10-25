"""
tests/test_retrieval.py
Unit tests for ChromaVectorStore and semantic retrieval.
"""

import shutil
from pathlib import Path
from backend.vectordb.vector_store import ChromaVectorStore


def test_chroma_vector_store_persistence(tmp_path):
    test_db_dir = tmp_path / "test_chroma"
    store = ChromaVectorStore(db_dir=str(test_db_dir), collection_name="test_collection")
    
    # Initially empty
    assert store.get_chunk_count() == 0

    dummy_chunks = [
        {"chunk_id": "c1", "page": 4, "text": "Health insurance covers dental and vision.", "source": "benefits.pdf"},
        {"chunk_id": "c2", "page": 9, "text": "Maternity leave is 16 weeks fully paid.", "source": "benefits.pdf"}
    ]
    # Simple 3-dimensional dummy embeddings for test
    dummy_embeddings = [
        [0.1, 0.2, 0.9],
        [0.8, 0.1, 0.1]
    ]

    added = store.add_chunks(dummy_chunks, dummy_embeddings, clear_existing=True)
    assert added == 2
    assert store.get_chunk_count() == 2

    # Query with vector close to c1
    results = store.query(query_embedding=[0.1, 0.2, 0.85], top_k=1)
    assert len(results) == 1
    assert results[0]["page"] == 4
    assert "Health insurance" in results[0]["text"]
    assert results[0]["source"] == "benefits.pdf"

    # Simulate restart by instantiating new client on the same folder
    store_restarted = ChromaVectorStore(db_dir=str(test_db_dir), collection_name="test_collection")
    assert store_restarted.get_chunk_count() == 2
