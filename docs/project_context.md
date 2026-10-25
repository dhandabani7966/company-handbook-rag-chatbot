# Project Context — Company Handbook Intelligence AI

## Background
Originally prototyped in Google Colab, this application has been engineered into a production-grade local full-stack RAG web application running on Windows without external paid API keys.

## Technical Specifications
- **Operating Environment**: Windows 11 (64-bit)
- **Runtime**: Python 3.13, Node.js v24
- **PDF Extraction**: PyPDF (1-indexed page preservation)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Vector Database**: ChromaDB (Persistent on-disk storage under `data/chroma_db/`)
- **LLM Generator**: `Qwen/Qwen2.5-1.5B-Instruct` (CPU-optimized, low memory footprint)
- **Backend**: FastAPI with async route handlers and CORS
- **Frontend**: React 18, Vite 5, Lucide React, Vanilla CSS

## Critical Constraints
- **Zero Paid APIs**: No OpenAI or third-party paid keys are utilized.
- **Local Persistence**: Vector embeddings persist in `data/chroma_db/` and survive process restarts.
- **Strict Grounding**: System prompt strictly forbids policy invention or hallucinated citations.
