"""
tests/test_e2e_rag.py
Complete end-to-end integration and policy citation validation test on sample handbook.
Isolated to temporary ChromaDB instance to protect active handbook.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.vectordb.vector_store import get_vector_store


@pytest.fixture
def isolated_chroma(tmp_path, monkeypatch):
    """Isolate e2e test to temporary ChromaDB directory and reset singletons on exit."""
    import backend.vectordb.vector_store as vs_module
    import backend.api.routes as routes_module
    import backend.retrieval.retriever as retriever_module
    from backend.vectordb.vector_store import ChromaVectorStore

    test_db_dir = tmp_path / "test_chroma"
    test_store = ChromaVectorStore(db_dir=str(test_db_dir), collection_name="test_handbook")
    monkeypatch.setattr(vs_module, "_client_instance", test_store)
    monkeypatch.setattr(vs_module, "get_vector_store", lambda: test_store)
    monkeypatch.setattr(routes_module, "get_vector_store", lambda: test_store)
    monkeypatch.setattr(retriever_module, "_retriever_instance", None)

    yield test_store

    vs_module._client_instance = None
    retriever_module._retriever_instance = None


def test_e2e_upload_query_and_persistence(isolated_chroma):
    client = TestClient(create_app())

    # Step 1: Health check
    res_health = client.get("/health")
    assert res_health.status_code == 200

    # Step 2: Upload real multi-page sample handbook
    pdf_path = Path("data/documents/sample_company_handbook.pdf")
    assert pdf_path.exists(), "Sample PDF must exist for e2e test."

    with open(pdf_path, "rb") as f:
        upload_res = client.post(
            "/upload",
            files={"file": ("sample_company_handbook.pdf", f, "application/pdf")}
        )

    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["chunks_indexed"] > 0
    assert upload_data["filename"] == "sample_company_handbook.pdf"

    # Step 3: Test Annual Leave Query (Expected on Page 2)
    ask_leave = client.post("/ask", json={"question": "What is the annual leave entitlement?"})
    assert ask_leave.status_code == 200
    data_leave = ask_leave.json()
    assert "sources" in data_leave
    assert len(data_leave["sources"]) > 0

    # Verify that at least one retrieved citation points to Page 2
    pages = [s["page"] for s in data_leave["sources"]]
    assert 2 in pages, f"Expected citation on Page 2, but got: {pages}"

    # Step 4: Test Privilege Leave Carry-Forward Query (Expected on Page 3)
    ask_carry = client.post("/ask", json={"question": "What is the privilege leave carry-forward limit?"})
    assert ask_carry.status_code == 200
    data_carry = ask_carry.json()
    assert len(data_carry["sources"]) > 0
    pages_carry = [s["page"] for s in data_carry["sources"]]
    assert 3 in pages_carry, f"Expected citation on Page 3, but got: {pages_carry}"

    # Step 5: Verify Persistence (ChromaDB has non-zero chunks after initial indexing)
    vector_store = get_vector_store()
    initial_chunks = vector_store.get_chunk_count()
    assert initial_chunks > 0

    # Re-instantiate app client (simulating server reboot)
    fresh_client = TestClient(create_app())
    health_reboot = fresh_client.get("/health")
    assert health_reboot.status_code == 200
    assert health_reboot.json()["indexed_chunks"] == initial_chunks
