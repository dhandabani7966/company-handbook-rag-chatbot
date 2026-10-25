"""
backend/api/document_routes.py
Document management endpoints: listing, upload & indexing, retry, secure preview/download,
and admin-only document deletion with ChromaDB synchronization.
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.db.database import get_db_connection
from backend.auth.security import get_current_user, get_current_admin
from backend.utils.helpers import get_project_root, sanitize_filename, ensure_directory, load_config
from backend.ingestion.loader import extract_pdf_pages, PDFExtractionError
from backend.chunking.chunker import chunk_pages
from backend.embeddings.embedder import get_embedder
from backend.vectordb.vector_store import get_vector_store
from backend.retrieval.retriever import get_retriever

router = APIRouter(prefix="/api/documents", tags=["Document Management"])


# --- Schemas ---

class DocumentItem(BaseModel):
    id: str
    filename: str
    original_name: str
    file_size: int
    chunks_count: int
    status: str
    uploaded_by: str
    uploaded_at: str
    error_message: Optional[str] = None


class DocumentMetrics(BaseModel):
    total: int
    indexed: int
    processing: int
    failed: int


class DocumentListResponse(BaseModel):
    metrics: DocumentMetrics
    documents: List[DocumentItem]


# --- Endpoints ---

@router.get("", response_model=DocumentListResponse)
def list_documents(current_user: dict = Depends(get_current_user)):
    """List all documents with indexing status, size, and aggregate metrics."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, filename, original_name, file_size, chunks_count, status, uploaded_by, uploaded_at, error_message
        FROM documents
        ORDER BY uploaded_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    docs = []
    total = len(rows)
    indexed = sum(1 for r in rows if r["status"] == "indexed")
    processing = sum(1 for r in rows if r["status"] == "processing")
    failed = sum(1 for r in rows if r["status"] == "failed")

    for r in rows:
        docs.append(DocumentItem(
            id=r["id"],
            filename=r["filename"],
            original_name=r["original_name"],
            file_size=r["file_size"],
            chunks_count=r["chunks_count"],
            status=r["status"],
            uploaded_by=r["uploaded_by"],
            uploaded_at=r["uploaded_at"],
            error_message=r["error_message"]
        ))

    return DocumentListResponse(
        metrics=DocumentMetrics(total=total, indexed=indexed, processing=processing, failed=failed),
        documents=docs
    )


@router.post("/upload", response_model=DocumentItem)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and index a PDF company handbook document.
    Validates PDF format, size, chunks text, creates embeddings, updates ChromaDB, and registers in DB.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF (.pdf) files are supported."
        )

    config = load_config()
    max_size_mb = config.get("rag", {}).get("max_upload_size_mb", 25)
    max_bytes = max_size_mb * 1024 * 1024

    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_size_mb} MB."
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty."
        )

    safe_name = sanitize_filename(file.filename)
    root = get_project_root()
    doc_dir = ensure_directory(root / config.get("storage", {}).get("documents_dir", "data/documents"))
    saved_pdf_path = doc_dir / safe_name

    with open(saved_pdf_path, "wb") as f:
        f.write(contents)

    doc_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    file_size = len(contents)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Register document as processing
    cursor.execute("""
        INSERT OR REPLACE INTO documents (id, filename, original_name, file_path, file_size, chunks_count, status, uploaded_by, uploaded_at)
        VALUES (?, ?, ?, ?, ?, 0, 'processing', ?, ?)
    """, (doc_id, safe_name, file.filename, str(saved_pdf_path), file_size, current_user["full_name"], now))
    conn.commit()

    try:
        pages = extract_pdf_pages(saved_pdf_path)
        chunk_size = config.get("rag", {}).get("chunk_size", 1000)
        chunk_overlap = config.get("rag", {}).get("chunk_overlap", 150)
        chunks = chunk_pages(pages, chunk_size=chunk_size, overlap=chunk_overlap)

        if not chunks:
            raise ValueError("No readable text found in document.")

        # Tag chunks with source document filename and unique chunk IDs
        for idx, c in enumerate(chunks):
            c["source"] = safe_name
            c["chunk_id"] = f"{doc_id[:8]}_{idx}"

        embedder = get_embedder()
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedder.embed_documents(chunk_texts)

        vector_store = get_vector_store()
        total_indexed = vector_store.add_chunks(chunks, embeddings, clear_existing=False, batch_size=50)

        # Invalidate BM25 index so new document is immediately retrievable
        try:
            get_retriever().invalidate_bm25_cache()
        except Exception:
            pass

        # Mark indexed
        cursor.execute("""
            UPDATE documents
            SET status = 'indexed', chunks_count = ?, error_message = NULL
            WHERE id = ?
        """, (len(chunks), doc_id))
        conn.commit()

        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc_row = cursor.fetchone()
        conn.close()

        return DocumentItem(
            id=doc_row["id"],
            filename=doc_row["filename"],
            original_name=doc_row["original_name"],
            file_size=doc_row["file_size"],
            chunks_count=doc_row["chunks_count"],
            status=doc_row["status"],
            uploaded_by=doc_row["uploaded_by"],
            uploaded_at=doc_row["uploaded_at"]
        )

    except Exception as e:
        cursor.execute("""
            UPDATE documents
            SET status = 'failed', error_message = ?
            WHERE id = ?
        """, (str(e), doc_id))
        conn.commit()
        conn.close()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index document: {str(e)}"
        )


@router.post("/{document_id}/retry", response_model=DocumentItem)
def retry_document_indexing(document_id: str, current_user: dict = Depends(get_current_user)):
    """Retry indexing for a document marked as failed."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF source file missing on disk.")

    config = load_config()
    try:
        pages = extract_pdf_pages(file_path)
        chunks = chunk_pages(pages, chunk_size=config.get("rag", {}).get("chunk_size", 1000), overlap=150)
        for idx, c in enumerate(chunks):
            c["source"] = doc["filename"]
            c["chunk_id"] = f"{document_id[:8]}_{idx}"

        embedder = get_embedder()
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedder.embed_documents(chunk_texts)

        vector_store = get_vector_store()
        vector_store.add_chunks(chunks, embeddings, clear_existing=False, batch_size=50)

        # Invalidate BM25 cache
        try:
            get_retriever().invalidate_bm25_cache()
        except Exception:
            pass

        cursor.execute("""
            UPDATE documents
            SET status = 'indexed', chunks_count = ?, error_message = NULL
            WHERE id = ?
        """, (len(chunks), document_id))
        conn.commit()

        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        updated = cursor.fetchone()
        conn.close()

        return DocumentItem(
            id=updated["id"],
            filename=updated["filename"],
            original_name=updated["original_name"],
            file_size=updated["file_size"],
            chunks_count=updated["chunks_count"],
            status=updated["status"],
            uploaded_by=updated["uploaded_by"],
            uploaded_at=updated["uploaded_at"]
        )
    except Exception as e:
        cursor.execute("UPDATE documents SET status = 'failed', error_message = ? WHERE id = ?", (str(e), document_id))
        conn.commit()
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Retry failed: {str(e)}")


@router.get("/{document_id}/download")
def download_document(document_id: str, current_user: dict = Depends(get_current_user)):
    """Download or preview a stored PDF document securely."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT file_path, original_name FROM documents WHERE id = ?", (document_id,))
    doc = cursor.fetchone()
    conn.close()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    path = Path(doc["file_path"])
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server.")

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=doc["original_name"]
    )


@router.delete("/{document_id}")
def delete_document(document_id: str, current_admin: dict = Depends(get_current_admin)):
    """
    Admin-only: Delete a document from disk, remove from database,
    and purge its chunks from the ChromaDB vector database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT file_path, filename FROM documents WHERE id = ?", (document_id,))
    doc = cursor.fetchone()

    if not doc:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    filename = doc["filename"]
    file_path = Path(doc["file_path"])

    # 1. Purge chunks from ChromaDB
    try:
        vector_store = get_vector_store()
        vector_store.collection.delete(where={"source": filename})
        get_retriever().invalidate_bm25_cache()
    except Exception as e:
        pass

    # 2. Remove file from disk
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        pass

    # 3. Delete from database
    cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()
    conn.close()

    return {"message": f"Document '{filename}' and associated indexed chunks removed successfully."}
