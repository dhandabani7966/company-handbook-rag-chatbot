"""
tests/test_app.py
End-to-end integration test validating the complete RAG prompt flow.
"""

from backend.prompts.prompt_templates import build_user_prompt, SYSTEM_PROMPT


def test_rag_prompt_construction():
    mock_sources = [
        {"page": 3, "text": "Employees receive 15 days of annual leave."},
        {"page": 7, "text": "Carry forward of up to 5 annual leave days is permitted."}
    ]
    question = "Can I carry forward my leave?"
    user_prompt = build_user_prompt(question, mock_sources)

    assert "[Source: PDF page 3]" in user_prompt
    assert "[Source: PDF page 7]" in user_prompt
    assert "Carry forward of up to 5 annual leave days is permitted." in user_prompt
    assert question in user_prompt
    assert "HANDBOOK CONTEXT:" in user_prompt


def test_empty_sources_prompt():
    user_prompt = build_user_prompt("What is the leave policy?", [])
    assert "No handbook context available." in user_prompt
