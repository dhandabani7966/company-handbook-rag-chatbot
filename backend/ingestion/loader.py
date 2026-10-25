"""
backend/ingestion/loader.py
Extracts text from PDF documents page by page, preserving 1-indexed page numbers.
"""

from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails or PDF contains no extractable text."""
    pass


def extract_pdf_pages(pdf_path: str | Path) -> List[Dict[str, Any]]:
    """
    Extract text from each page of a PDF file.
    
    Args:
        pdf_path: Absolute or relative path to the PDF file.
        
    Returns:
        List of dicts: [
            {"page": 1, "text": "Page content...", "source": "handbook.pdf"},
            ...
        ]
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PDFExtractionError: If the PDF is corrupted, encrypted, or has no extractable text.
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        reader = PdfReader(str(path))
    except Exception as e:
        raise PDFExtractionError(f"Failed to read PDF file '{path.name}': {str(e)}")

    if reader.is_encrypted:
        try:
            # Attempt to decrypt with empty password
            reader.decrypt("")
        except Exception:
            raise PDFExtractionError("PDF is password protected and cannot be extracted.")

    pages_data: List[Dict[str, Any]] = []
    total_extracted_characters = 0

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1  # 1-indexed human-readable page number
        try:
            text = page.extract_text() or ""
        except Exception as e:
            text = ""

        cleaned_text = text.strip()
        total_extracted_characters += len(cleaned_text)

        pages_data.append({
            "page": page_num,
            "text": cleaned_text,
            "source": path.name,
        })

    if total_extracted_characters == 0:
        raise PDFExtractionError(
            "PDF contains no extractable text. It may be a scanned image or empty. "
            "Please upload a text-based PDF document."
        )

    return pages_data
