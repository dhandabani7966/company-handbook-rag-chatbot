"""
tests/benchmark_latency.py
Repeatable latency benchmarking suite for Company Handbook Intelligence AI.
Measures embedding, retrieval, prompt assembly, generation, and total latency across 5 representative queries.
Distinguishes first-request from subsequent-request latency.
"""

import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Route Hugging Face cache to D: drive
os.environ["HF_HOME"] = str(root_dir / "hf_cache")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_XET"] = "1"

from fastapi.testclient import TestClient
from backend.main import create_app
from backend.vectordb.vector_store import get_vector_store


def run_benchmark():
    print("=" * 70)
    print("COMPANY HANDBOOK INTELLIGENCE AI - LATENCY BENCHMARK")
    print("=" * 70)

    client = TestClient(create_app())

    # Step 1: Check handbook indexing
    pdf_path = Path("data/documents/sample_company_handbook.pdf")
    if not pdf_path.exists():
        raise FileNotFoundError("Sample PDF not found at data/documents/sample_company_handbook.pdf")

    print("[BENCHMARK] Re-indexing sample handbook with 1000-char chunks...")
    with open(pdf_path, "rb") as f:
        upload_res = client.post(
            "/upload",
            files={"file": ("sample_company_handbook.pdf", f, "application/pdf")}
        )
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    upload_info = upload_res.json()
    print(f"[BENCHMARK] Successfully indexed {upload_info['chunks_indexed']} chunks from {upload_info['filename']}.\n")

    test_queries = [
        {
            "id": "Q1",
            "question": "What is the company's annual leave policy?",
            "expected_page": 2,
            "type": "Policy Detail"
        },
        {
            "id": "Q2",
            "question": "What is the privilege leave carry-forward limit?",
            "expected_page": 3,
            "type": "Numeric Policy"
        },
        {
            "id": "Q3",
            "question": "What are the core operating hours and work schedule?",
            "expected_page": 1,
            "type": "General Guideline"
        },
        {
            "id": "Q4",
            "question": "What is the policy for sick leave?",
            "expected_page": 2,
            "type": "Leave Absence"
        },
        {
            "id": "Q5",
            "question": "What is the pet policy in the office?",
            "expected_page": None,
            "type": "Out of Context"
        }
    ]

    results = []

    for idx, q_info in enumerate(test_queries):
        is_first = (idx == 0)
        q = q_info["question"]
        print(f"--> Running {q_info['id']} ({'FIRST REQUEST' if is_first else 'SUBSEQUENT'}): \"{q}\"")

        t_client_start = time.perf_counter()
        res = client.post("/ask", json={"question": q})
        t_client_total_ms = (time.perf_counter() - t_client_start) * 1000

        assert res.status_code == 200, f"Query failed: {res.text}"
        data = res.json()

        timing = data.get("timing") or {}
        sources = data.get("sources", [])
        retrieved_pages = [s["page"] for s in sources]

        results.append({
            "id": q_info["id"],
            "type": q_info["type"],
            "question": q,
            "is_first": is_first,
            "embedding_ms": timing.get("embedding_ms", 0.0),
            "retrieval_ms": timing.get("retrieval_ms", 0.0),
            "prompt_ms": timing.get("prompt_ms", 0.0),
            "generation_ms": timing.get("generation_ms", 0.0),
            "backend_total_ms": timing.get("total_ms", 0.0),
            "client_total_ms": round(t_client_total_ms, 2),
            "retrieved_pages": retrieved_pages,
            "answer_preview": data.get("answer", "")[:120] + "..."
        })

    print("\n" + "=" * 90)
    print("BENCHMARK RESULTS TABLE")
    print("=" * 90)
    print(f"{'ID':<4} | {'Req Type':<11} | {'Embed(ms)':<9} | {'Retr(ms)':<8} | {'Gen(ms)':<9} | {'E2E Total(ms)':<13} | {'Retrieved Pages':<15}")
    print("-" * 90)

    for r in results:
        req_type = "First (Cold)" if r["is_first"] else "Subsequent"
        pages_str = str(r["retrieved_pages"])
        print(f"{r['id']:<4} | {req_type:<11} | {r['embedding_ms']:<9.1f} | {r['retrieval_ms']:<8.1f} | {r['generation_ms']:<9.1f} | {r['client_total_ms']:<13.1f} | {pages_str:<15}")

    print("=" * 90)
    return results


if __name__ == "__main__":
    run_benchmark()
