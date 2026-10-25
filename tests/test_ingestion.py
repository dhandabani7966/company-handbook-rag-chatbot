"""
tests/test_ingestion.py
Unit tests for PDF extraction and chunking with page number preservation.
"""

import pytest
from backend.ingestion.loader import extract_pdf_pages, PDFExtractionError
from backend.chunking.chunker import chunk_pages


def test_chunking_preserves_page_numbers():
    pages = [
        {"page": 1, "text": "Annual leave entitlement is 20 days per calendar year.", "source": "handbook.pdf"},
        {"page": 2, "text": "Sick leave requires medical certificate after two consecutive days.", "source": "handbook.pdf"},
    ]
    chunks = chunk_pages(pages, chunk_size=30, overlap=10)
    assert len(chunks) >= 2
    page_1_chunks = [c for c in chunks if c["page"] == 1]
    page_2_chunks = [c for c in chunks if c["page"] == 2]
    assert len(page_1_chunks) > 0
    assert len(page_2_chunks) > 0
    assert "Annual leave" in page_1_chunks[0]["text"]
    assert "Sick leave" in page_2_chunks[0]["text"]


def test_chunking_default_1000_chars():
    long_text = "This is a company policy statement. " * 50
    pages = [{"page": 1, "text": long_text, "source": "handbook.pdf"}]
    chunks = chunk_pages(pages, chunk_size=1000, overlap=150)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk["page"] == 1
        assert len(chunk["text"]) <= 1000


def test_extraction_missing_file_raises_error(tmp_path):
    missing_file = tmp_path / "non_existent.pdf"
    with pytest.raises(FileNotFoundError):
        extract_pdf_pages(missing_file)
