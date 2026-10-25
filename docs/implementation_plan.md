# Implementation Plan — Company Handbook Intelligence AI

## Progress Tracker
- [x] **Phase 1: Project Setup & Baseline**
  - Scaffolding of modular directories (`backend/`, `frontend/`, `data/`, `tests/`, `logs/`, `docs/`).
  - Configuration files (`config.yaml`, `.env.example`, `.gitignore`, `requirements.txt`).
  - Python virtual environment `.venv` created and dependencies installed.
  - React + Vite frontend scaffolded with Lucide icons.
- [x] **Phase 2: PDF Ingestion & Chunking**
  - `backend/ingestion/loader.py`: Text extraction per page with 1-indexed numbering.
  - `backend/chunking/chunker.py`: Overlapping chunker retaining page and document metadata.
- [x] **Phase 3: Embeddings & Vector Storage**
  - `backend/embeddings/embedder.py`: Singleton wrapper for `sentence-transformers/all-MiniLM-L6-v2`.
  - `backend/vectordb/vector_store.py`: Persistent ChromaDB storage under `data/chroma_db/`.
- [x] **Phase 4: Retrieval, Prompts & Local LLM**
  - `backend/retrieval/retriever.py`: Semantic top-$k$ similarity retriever.
  - `backend/prompts/prompt_templates.py`: Strict grounding prompts preventing policy hallucination.
  - `backend/llm/llm_client.py`: Local `Qwen/Qwen2.5-1.5B-Instruct` generator with CPU optimization.
- [x] **Phase 5: FastAPI Backend**
  - `backend/api/routes.py`: Endpoints for `GET /health`, `POST /upload`, and `POST /ask`.
  - `backend/main.py`: CORS configuration, lifespan events, and directory initialization.
- [x] **Phase 6: React UI**
  - `PdfUpload.jsx`, `ChatWindow.jsx`, `AnswerCard.jsx`, `SourceCitation.jsx`.
  - Modern, accessible responsive styling in `App.css`.
  - Production build validated with `npm run build`.
- [x] **Phase 7: End-to-End Validation**
  - Automated tests passing via Pytest (`tests/test_api.py`, `tests/test_ingestion.py`, `tests/test_retrieval.py`, `tests/test_app.py`).
  - Persistence verified across restarts.
