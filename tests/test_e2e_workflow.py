"""
tests/test_e2e_workflow.py
Production Readiness Verification:
End-to-End workflow testing user login, synthetic PDF upload & indexing,
query retrieval, citation validation, latency separation, conversation history,
cross-user isolation, and authorized cleanup.
"""

import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import create_app

app = create_app()
client = TestClient(app)


def test_full_production_workflow():
    print("\n--- 1. AUTHENTICATION & LOGIN ---")
    login_res = client.post("/api/auth/login", json={
        "email": "abhishek@company.com",
        "password": "Abhishek@123"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    auth_data = login_res.json()
    token = auth_data["access_token"]
    user_id = auth_data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in as: {auth_data['user']['email']} (Role: {auth_data['user']['role']})")

    # Also log in as admin for isolation and cleanup verification
    admin_res = client.post("/api/auth/login", json={
        "email": "admin@company.com",
        "password": "Admin@12345"
    })
    assert admin_res.status_code == 200
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    print("\n--- 2. SYNTHETIC PDF UPLOAD & INDEXING ---")
    synth_pdf = Path("tests/test_synthetic_travel_policy.pdf")
    assert synth_pdf.exists(), "Synthetic test PDF not found"

    with open(synth_pdf, "rb") as f:
        upload_res = client.post(
            "/api/documents/upload",
            headers=headers,
            files={"file": ("test_synthetic_travel_policy.pdf", f, "application/pdf")}
        )
    assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["status"] == "indexed"
    assert doc_data["chunks_count"] > 0
    print(f"Uploaded and indexed synthetic document ID: {doc_id} with {doc_data['chunks_count']} chunks")

    print("\n--- 3. CONVERSATION SESSION CREATION ---")
    conv_res = client.post(
        "/api/conversations",
        headers=headers,
        json={"title": "Travel Policy Inquiries"}
    )
    assert conv_res.status_code == 200
    conv_id = conv_res.json()["id"]
    print(f"Created conversation session: {conv_id}")

    print("\n--- 4. QUERY EXECUTION & SEPARATED LATENCY MEASUREMENT ---")
    q = "What is the daily domestic meal allowance?"
    t0 = time.perf_counter()
    msg_res = client.post(
        f"/api/conversations/{conv_id}/messages",
        headers=headers,
        json={"content": q}
    )
    e2e_total_ms = (time.perf_counter() - t0) * 1000
    assert msg_res.status_code == 200, f"Chat message failed: {msg_res.text}"
    msg_data = msg_res.json()

    answer = msg_data["content"]
    sources = msg_data["sources"]
    timing = msg_data["timing"]

    print(f"User Query: {q}")
    print(f"Answer: {answer}")
    print(f"Sources/Citations ({len(sources)}):")
    for s in sources:
        print(f"  - Page {s['page']}")

    print("\n--- 5. SEPARATED LATENCY METRICS ---")
    print(f"  Embedding Latency:  {timing.get('embedding_ms', 0):.2f} ms")
    print(f"  Retrieval Latency:  {timing.get('retrieval_ms', 0):.2f} ms")
    print(f"  Prompt Formatting:  {timing.get('prompt_ms', 0):.2f} ms")
    print(f"  Generation Latency: {timing.get('generation_ms', 0):.2f} ms")
    print(f"  Total Server Time:  {timing.get('total_ms', 0):.2f} ms")
    print(f"  Client-observed:    {e2e_total_ms:.2f} ms")

    assert "1,500" in answer or "1500" in answer, "Answer missing expected allowance"
    assert len(sources) > 0, "No sources cited for synthetic document query"

    print("\n--- 6. CONVERSATION HISTORY VERIFICATION ---")
    history_res = client.get(f"/api/conversations/{conv_id}", headers=headers)
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert len(history_data["messages"]) >= 2
    assert history_data["messages"][0]["role"] == "user"
    assert history_data["messages"][1]["role"] == "assistant"
    print(f"History verified with {len(history_data['messages'])} persisted messages.")

    print("\n--- 7. CROSS-USER OBJECT-LEVEL ISOLATION (IDOR) ---")
    # Admin tries to access Abhishek's conversation -> must be 404
    cross_read = client.get(f"/api/conversations/{conv_id}", headers=admin_headers)
    assert cross_read.status_code == 404, "Security violation: Cross-user conversation access allowed!"
    print("Cross-user isolation verified: Admin cannot view Employee's conversation.")

    print("\n--- 8. AUTHORIZED CLEANUP OF SYNTHETIC DOCUMENT ---")
    # Non-admin cannot delete
    unauth_del = client.delete(f"/api/documents/{doc_id}", headers=headers)
    assert unauth_del.status_code == 403, "Non-admin was able to delete document!"

    # Admin deletes synthetic document
    del_res = client.delete(f"/api/documents/{doc_id}", headers=admin_headers)
    assert del_res.status_code == 200
    print(f"Admin successfully purged synthetic document {doc_id} and its vector chunks.")

    # Clean up test conversation
    clean_conv = client.delete(f"/api/conversations/{conv_id}", headers=headers)
    assert clean_conv.status_code == 200
    print("Cleaned up test conversation session.")

    print("\n--- 9. LOGOUT VERIFICATION ---")
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    print("Logout completed successfully.")


if __name__ == "__main__":
    test_full_production_workflow()
