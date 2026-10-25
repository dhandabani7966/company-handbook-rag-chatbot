"""
backend/api/routes.py
FastAPI router defining /health, /upload, and /ask endpoints.
Aligned with Colab pipeline logic, with granular latency metrics and persistent storage.
"""

import time
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel, Field

from backend.utils.helpers import get_project_root, sanitize_filename, ensure_directory, load_config
from backend.ingestion.loader import extract_pdf_pages, PDFExtractionError
from backend.chunking.chunker import chunk_pages
from backend.embeddings.embedder import get_embedder
from backend.vectordb.vector_store import get_vector_store
from backend.retrieval.retriever import get_retriever
from backend.llm.llm_client import get_llm_client, ask_handbook

# Setup latency logger
logger = logging.getLogger("rag_latency")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
    logger.addHandler(ch)

router = APIRouter()
_current_indexed_filename: Optional[str] = None
_request_counter: int = 0


# --- Pydantic Models ---

class HealthResponse(BaseModel):
    status: str
    rag_ready: bool
    indexed_chunks: int
    current_document: Optional[str] = None


class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_indexed: int


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Employee handbook query")


class SourceItem(BaseModel):
    page: int
    text: str


class LatencyBreakdown(BaseModel):
    embedding_ms: float
    retrieval_ms: float
    prompt_ms: float
    generation_ms: float
    total_ms: float
    is_first_request: bool


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    timing: Optional[LatencyBreakdown] = None


# --- Endpoints ---

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Return backend health, RAG readiness, and local indexed chunk count."""
    global _current_indexed_filename
    vector_store = get_vector_store()
    chunk_count = vector_store.get_chunk_count()

    # Automatically identify active indexed document directly from ChromaDB metadata
    if _current_indexed_filename is None and chunk_count > 0:
        try:
            sample = vector_store.collection.get(limit=1)
            if sample and sample.get("metadatas") and sample["metadatas"]:
                _current_indexed_filename = sample["metadatas"][0].get("source")
        except Exception:
            pass
        if _current_indexed_filename is None:
            docs_dir = get_project_root() / "data" / "documents"
            pdf_files = [f.name for f in docs_dir.glob("*.pdf") if not f.name.startswith("sample")]
            if pdf_files:
                _current_indexed_filename = pdf_files[0]

    return HealthResponse(
        status="ok",
        rag_ready=chunk_count > 0,
        indexed_chunks=chunk_count,
        current_document=_current_indexed_filename
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_handbook(file: UploadFile = File(...)):
    """
    Upload and index a PDF company handbook.
    Validates file, extracts pages, chunks text, creates embeddings, and updates persistent ChromaDB.
    """
    global _current_indexed_filename

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

    try:
        pages = extract_pdf_pages(saved_pdf_path)
    except PDFExtractionError as e:
        if saved_pdf_path.exists():
            saved_pdf_path.unlink()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if saved_pdf_path.exists():
            saved_pdf_path.unlink()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error reading PDF: {str(e)}")

    # Chunk text with notebook parameters (chunk_size: 1000, overlap: 150)
    chunk_size = config.get("rag", {}).get("chunk_size", 1000)
    chunk_overlap = config.get("rag", {}).get("chunk_overlap", 150)
    chunks = chunk_pages(pages, chunk_size=chunk_size, overlap=chunk_overlap)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not generate readable chunks from the provided PDF."
        )

    try:
        embedder = get_embedder()
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedder.embed_documents(chunk_texts)

        vector_store = get_vector_store()
        total_indexed = vector_store.add_chunks(chunks, embeddings, clear_existing=True, batch_size=50)
        _current_indexed_filename = safe_name

        return UploadResponse(
            message="PDF uploaded and indexed successfully",
            filename=safe_name,
            chunks_indexed=total_indexed
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index PDF: {str(e)}"
        )


@router.post("/ask", response_model=AskResponse)
def handle_ask_question(request: AskRequest):
    """
    Answer questions grounded strictly in the indexed handbook context.
    Measures and logs latency for query embedding, ChromaDB retrieval, prompt formatting, and LLM inference.
    """
    global _request_counter
    _request_counter += 1
    is_first = (_request_counter == 1)

    t_start = time.perf_counter()

    clean_question = request.question.strip()
    if not clean_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )

    vector_store = get_vector_store()
    if vector_store.get_chunk_count() == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No handbook has been indexed yet. Please upload a PDF handbook first."
        )

    config = load_config()
    top_k = config.get("rag", {}).get("top_k", 4)

    try:
        # Step 1: Query embedding
        t_embed_start = time.perf_counter()
        embedder = get_embedder()
        query_vector = embedder.embed_query(clean_question)
        t_embed_ms = (time.perf_counter() - t_embed_start) * 1000

        # Step 2: ChromaDB retrieval with relevance inspection and score logging
        t_retrieval_start = time.perf_counter()
        retriever = get_retriever()
        retrieval_data = retriever.retrieve_and_inspect(clean_question, top_k=top_k)
        sources = retrieval_data["sources"]
        t_retrieval_ms = (time.perf_counter() - t_retrieval_start) * 1000

        # Step 3 & 4: Prompt assembly and LLM generation
        llm = get_llm_client()
        gen_result = llm.generate_answer(clean_question, sources, max_new_tokens=300)
        t_prompt_ms = gen_result["prompt_time_ms"]
        t_gen_ms = gen_result["generation_time_ms"]

        # Step 5: Total end-to-end time
        t_total_ms = (time.perf_counter() - t_start) * 1000

        # Log detailed latency metrics
        logger.info(
            f"[LATENCY] Request #{_request_counter} (first={is_first}) | "
            f"Embed: {t_embed_ms:.2f}ms | "
            f"Retrieval: {t_retrieval_ms:.2f}ms | "
            f"Prompt: {t_prompt_ms:.2f}ms | "
            f"Generation: {t_gen_ms:.2f}ms | "
            f"Total: {t_total_ms:.2f}ms"
        )

        # Requirement 2 & 3: Return only sources that directly support the answer
        supporting_pages = set(gen_result.get("supporting_pages", []))
        if "not contain" in gen_result["answer"].lower() or "insufficient" in gen_result["answer"].lower():
            final_sources = []
        elif supporting_pages:
            final_sources = [s for s in sources if int(s.get("page", -1)) in supporting_pages]
        else:
            final_sources = sources[:1] if sources else []

        formatted_sources = [
            SourceItem(page=int(s["page"]), text=s["text"])
            for s in final_sources
        ]

        return AskResponse(
            answer=gen_result["answer"],
            sources=formatted_sources,
            timing=LatencyBreakdown(
                embedding_ms=round(t_embed_ms, 2),
                retrieval_ms=round(t_retrieval_ms, 2),
                prompt_ms=round(t_prompt_ms, 2),
                generation_ms=round(t_gen_ms, 2),
                total_ms=round(t_total_ms, 2),
                is_first_request=is_first
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ERROR] Ask endpoint failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval or generation failed: {str(e)}"
        )
