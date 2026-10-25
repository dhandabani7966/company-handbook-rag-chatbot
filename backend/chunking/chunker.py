"""
backend/chunking/chunker.py
Structure-aware, heading-preserving text chunker for Company Handbook Intelligence AI.
Preserves 1-indexed page numbers, natural section boundaries, bullet points, and metadata.
"""

import re
from typing import List, Dict, Any, Optional

SECTION_HEADER_REGEX = re.compile(
    r"^(?:(?:\d+\.){1,4}\d*|\b(?:Section|Chapter|Appendix)\s+[A-Za-z0-9\.]+)\s+[A-Z][^\n]{2,80}$",
    re.MULTILINE
)


def normalize_page_text(text: str) -> str:
    """
    Normalize whitespace and soft line-breaks inside paragraphs without
    collapsing section headers, list bullets, or paragraph boundaries.
    """
    if not text:
        return ""

    # Replace weird unicode bullets and symbols with standard bullet points
    text = re.sub(r"[\uf0d8\uf0a7\u2022\u25cf\u25aa\u25ab]+", "•", text)

    # Standardize Windows CRLF to LF
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove trailing spaces from each line
    lines = [line.rstrip() for line in text.split("\n")]

    # Join lines that are soft-wrapped mid-sentence (i.e. line does not end with punctuation,
    # and next line does not start with bullet, header, or digit list item)
    merged_lines: List[str] = []
    i = 0
    while i < len(lines):
        curr = lines[i]
        if not curr.strip():
            merged_lines.append("")
            i += 1
            continue

        # Check if next line should be joined
        if i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            is_header = bool(SECTION_HEADER_REGEX.match(curr)) or bool(SECTION_HEADER_REGEX.match(nxt))
            is_bullet = curr.strip().startswith("•") or nxt.startswith("•")
            is_numbered = bool(re.match(r"^\d+[\.\)]\s", nxt)) or bool(re.match(r"^\d+[\.\)]\s", curr.strip()))
            is_end_punct = curr.strip().endswith((".", ":", ";", "?", "!", "…"))

            if not is_header and not is_bullet and not is_numbered and not is_end_punct and nxt:
                merged_lines.append(curr + " " + nxt)
                i += 2
                continue

        merged_lines.append(curr)
        i += 1

    normalized = "\n".join(merged_lines)
    # Collapse 3 or more newlines to 2
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    return normalized


def extract_section_heading(text: str, default_heading: str = "Policy Guidelines") -> str:
    """Identify the primary section heading in a text block."""
    for line in text.splitlines():
        line_s = line.strip()
        # Look for patterns like "10.1.3 Annual Leave", "14. Work from Home", "11.1.6 Insurance Escalation Matrix"
        m = re.match(r"^((?:\d+\.){1,4}\d*\s+[A-Za-z][A-Za-z0-9\s/&,\-\(\)]+)", line_s)
        if m and len(m.group(1)) < 80:
            return m.group(1).strip()
        m2 = re.match(r"^((?:Section|Chapter|Appendix)\s+[A-Za-z0-9\.]+\s*[:\-]?\s*[A-Za-z0-9\s/&,\-]+)", line_s, re.I)
        if m2 and len(m2.group(1)) < 80:
            return m2.group(1).strip()
    return default_heading


def split_into_boundary_units(text: str) -> List[str]:
    """
    Split text into logical units: paragraphs, numbered items, or bullet points,
    so that chunks never break sentences mid-word.
    """
    units: List[str] = []
    # Split by double newline first
    blocks = re.split(r"\n\s*\n", text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Check if block has multiple bullet items or numbered steps
        sub_items = re.split(r"(?<=\n)(?=[•\d]+\.?\s)", block)
        for item in sub_items:
            item_clean = item.strip()
            if item_clean:
                units.append(item_clean)
    return units


def chunk_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = 1000,
    overlap: int = 150
) -> List[Dict[str, Any]]:
    """
    Split extracted PDF pages into structure-aware, overlapping chunks.
    Preserves 1-indexed page numbers, natural section boundaries, and metadata.
    
    Args:
        pages: List of page dicts: [{"page": 1, "text": "...", "source": "..."}, ...]
        chunk_size: Maximum characters per chunk (default 1000).
        overlap: Character overlap between consecutive chunks (default 150).
        
    Returns:
        List of chunk dicts:
        [
            {
                "chunk_id": "chunk_0",
                "page": 1,
                "text": "...",
                "source": "handbook.pdf",
                "section_heading": "10.1.3 Annual Leave"
            },
            ...
        ]
    """
    chunks: List[Dict[str, Any]] = []
    chunk_idx = 0

    for page in pages:
        raw_text = page.get("text", "")
        page_num = int(page.get("page", 1))
        source = str(page.get("source", "handbook.pdf"))

        if not raw_text.strip():
            continue

        normalized_text = normalize_page_text(raw_text)
        units = split_into_boundary_units(normalized_text)

        current_heading = extract_section_heading(normalized_text, f"Page {page_num} Section")

        # Assemble units into chunks up to chunk_size
        current_chunk_units: List[str] = []
        current_len = 0

        for unit in units:
            unit_heading = extract_section_heading(unit, "")
            if unit_heading:
                current_heading = unit_heading

            unit_len = len(unit)

            # If a single unit exceeds chunk_size, fallback to sentence or word slicing
            if unit_len > chunk_size:
                # Flush existing buffer first
                if current_chunk_units:
                    chunk_text = "\n\n".join(current_chunk_units).strip()
                    if chunk_text:
                        chunks.append({
                            "chunk_id": f"chunk_{chunk_idx}",
                            "page": page_num,
                            "text": chunk_text[:chunk_size],
                            "source": source,
                            "section_heading": current_heading
                        })
                        chunk_idx += 1
                    current_chunk_units = []
                    current_len = 0

                # Slice large unit by sentences or character windows
                start = 0
                while start < len(unit):
                    end = start + chunk_size
                    # Try to break at a period or space
                    if end < len(unit):
                        last_space = unit.rfind(" ", start, end)
                        if last_space > start + chunk_size // 2:
                            end = last_space
                    sub_slice = unit[start:end].strip()
                    if sub_slice:
                        chunks.append({
                            "chunk_id": f"chunk_{chunk_idx}",
                            "page": page_num,
                            "text": sub_slice[:chunk_size],
                            "source": source,
                            "section_heading": current_heading
                        })
                        chunk_idx += 1
                    start = end - overlap if (end - overlap > start) else end
                continue

            if current_len + unit_len + 2 > chunk_size and current_chunk_units:
                # Chunk boundary reached - save current chunk
                chunk_text = "\n\n".join(current_chunk_units).strip()
                chunks.append({
                    "chunk_id": f"chunk_{chunk_idx}",
                    "page": page_num,
                    "text": chunk_text[:chunk_size],
                    "source": source,
                    "section_heading": current_heading
                })
                chunk_idx += 1

                # Keep overlap from the end of current_chunk_units
                overlap_units: List[str] = []
                overlap_len = 0
                for u in reversed(current_chunk_units):
                    if overlap_len + len(u) <= overlap:
                        overlap_units.insert(0, u)
                        overlap_len += len(u) + 2
                    else:
                        break

                current_chunk_units = overlap_units + [unit]
                current_len = sum(len(u) for u in current_chunk_units) + (len(current_chunk_units) - 1) * 2
            else:
                current_chunk_units.append(unit)
                current_len += unit_len + 2

        # Flush final remaining units on the page
        if current_chunk_units:
            chunk_text = "\n\n".join(current_chunk_units).strip()
            if chunk_text:
                chunks.append({
                    "chunk_id": f"chunk_{chunk_idx}",
                    "page": page_num,
                    "text": chunk_text[:chunk_size],
                    "source": source,
                    "section_heading": current_heading
                })
                chunk_idx += 1

    return chunks
