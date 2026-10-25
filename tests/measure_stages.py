"""
tests/measure_stages.py
Measures timing for embedding generation, ChromaDB retrieval, prompt formatting, and context overhead.
"""

import sys
import os
import time
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

os.environ["HF_HOME"] = str(root_dir / "hf_cache")

from backend.embeddings.embedder import get_embedder, get_embeddings
from backend.vectordb.vector_store import get_vector_store
from backend.prompts.prompt_templates import build_user_prompt
from backend.chunking.chunker import chunk_pages
from backend.ingestion.loader import extract_pdf_pages

def test_stage_timings():
    print("=" * 75)
    print("STAGE-BY-STAGE LATENCY & BOTTLENECK DIAGNOSIS")
    print("=" * 75)

    pdf_path = root_dir / "data" / "documents" / "sample_company_handbook.pdf"
    
    # 1. Ingestion & Chunking timing
    t0 = time.perf_counter()
    pages = extract_pdf_pages(pdf_path)
    t_extract_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    chunks = chunk_pages(pages, chunk_size=1000, overlap=150)
    t_chunk_ms = (time.perf_counter() - t0) * 1000

    # 2. Embedding creation timing
    t0 = time.perf_counter()
    embedder = get_embedder()
    chunk_texts = [c["text"] for c in chunks]
    embeddings = embedder.embed_documents(chunk_texts)
    t_doc_embed_ms = (time.perf_counter() - t0) * 1000

    # 3. ChromaDB indexing timing
    store = get_vector_store()
    t0 = time.perf_counter()
    count = store.add_chunks(chunks, embeddings, clear_existing=True, batch_size=50)
    t_index_ms = (time.perf_counter() - t0) * 1000

    print(f"Extraction Time:       {t_extract_ms:.2f} ms")
    print(f"Chunking Time:         {t_chunk_ms:.2f} ms (Chunks generated: {len(chunks)})")
    print(f"Document Embedding:    {t_doc_embed_ms:.2f} ms ({t_doc_embed_ms/len(chunks):.2f} ms/chunk)")
    print(f"ChromaDB Indexing:     {t_index_ms:.2f} ms")
    print("-" * 75)

    queries = [
        "What is the company's annual leave policy?",
        "What is the privilege leave carry-forward limit?",
        "What are the core operating hours and work schedule?",
        "What is the policy for sick leave?",
        "What is the pet policy in the office?"
    ]

    print(f"{'Query':<52} | {'Embed(ms)':<10} | {'Retrieve(ms)':<12} | {'Prompt(ms)':<10}")
    print("-" * 92)

    for idx, q in enumerate(queries):
        is_first = (idx == 0)
        
        # Measure query embedding
        t0 = time.perf_counter()
        q_vec = embedder.embed_query(q)
        t_q_embed_ms = (time.perf_counter() - t0) * 1000

        # Measure ChromaDB retrieval
        t0 = time.perf_counter()
        retrieved = store.query(q_vec, top_k=4)
        t_retr_ms = (time.perf_counter() - t0) * 1000

        # Measure prompt assembly
        t0 = time.perf_counter()
        prompt = build_user_prompt(q, retrieved)
        t_prompt_ms = (time.perf_counter() - t0) * 1000

        label = f"Q{idx+1} ({'Cold' if is_first else 'Warm'}): {q[:38]}..."
        print(f"{label:<52} | {t_q_embed_ms:<10.2f} | {t_retr_ms:<12.2f} | {t_prompt_ms:<10.2f}")

    print("=" * 75)

if __name__ == "__main__":
    test_stage_timings()
