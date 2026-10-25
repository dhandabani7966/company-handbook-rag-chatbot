# Design Document — Company Handbook Intelligence AI

## Product Overview
A professional, local, privacy-preserving internal knowledge assistant. Employees upload a company handbook PDF, ask natural-language questions, and review evidence-backed answers with exact PDF page citations.

## Core Principles
1. **Trustworthy**: Every statement is grounded directly in retrieved handbook passages, complete with 1-indexed PDF page citations.
2. **Simple**: Intuitive interface with drag-and-drop PDF upload and familiar conversational interface.
3. **Readable**: Strong visual hierarchy, dark slate background, accessible contrast, clean card containers.
4. **Responsive**: Adaptable layout across desktop, tablet, and mobile browsers.
5. **Honest**: When retrieved evidence is missing or insufficient, the system explicitly states that the handbook does not contain the answer.

## Architecture
```
Employee -> React + Vite UI (Port 5173) -> FastAPI Backend (Port 8000) -> Python Modular RAG Engine
                                                                        |-- PDF Ingestion (PyPDF)
                                                                        |-- Page-aware Chunking
                                                                        |-- Sentence Transformers
                                                                        |-- Persistent ChromaDB
                                                                        |-- Local Qwen2.5-1.5B Generation
Employee <- React UI <- Answer + Source Excerpts + Human-Readable PDF Page Numbers
```

## UI Components
- `AppShell`: Top-level container managing layout, state, and periodic health checks.
- `AppHeader`: Product branding, active backend indicator, refresh trigger.
- `PdfUpload`: Drag-and-drop file upload, indexing indicator, chunk counter, active document label.
- `ChatWindow`: Message history, suggested question chips, character counter, input form.
- `AnswerCard`: Assistant response bubble with grounding badge and timestamp.
- `SourceCitation`: Expandable source card with PDF Page tags and excerpt snippets.
