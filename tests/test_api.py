"""
tests/test_api.py
API tests for FastAPI endpoints: /health, /upload, and /ask.
"""

from fastapi.testclient import TestClient
from backend.main import create_app

client = TestClient(create_app())


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "rag_ready" in data
    assert "indexed_chunks" in data


def test_upload_non_pdf_rejected():
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"plain text", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF" in response.json()["detail"]


def test_ask_empty_question_rejected():
    response = client.post(
        "/ask",
        json={"question": "   "}
    )
    assert response.status_code in (400, 422)
