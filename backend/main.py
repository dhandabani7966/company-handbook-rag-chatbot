"""
backend/main.py
FastAPI entrypoint for the Company Handbook Intelligence AI application.
Configures CORS, lifespan events, model warmups, and registers modular API routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.utils.helpers import load_config, get_project_root, ensure_directory
from backend.api.routes import router as api_router
from backend.api.auth_routes import router as auth_router
from backend.api.chat_routes import router as chat_router
from backend.api.document_routes import router as document_router
from backend.api.settings_routes import router as settings_router
from backend.api.feedback_routes import router as feedback_router
from backend.api.admin_routes import router as admin_router
from backend.db.database import init_db, seed_default_admin
from backend.vectordb.vector_store import get_vector_store
from backend.embeddings.embedder import get_embedder


import os
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv()

from backend.auth.security import get_jwt_secret


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events with database initialization, secret verification, and warmup."""
    config = load_config()
    root = get_project_root()
    
    # 1. Enforce JWT security and configuration validation
    get_jwt_secret()

    # 2. Ensure storage directories exist
    ensure_directory(root / config.get("storage", {}).get("documents_dir", "data/documents"))
    ensure_directory(root / config.get("storage", {}).get("chroma_db_dir", "data/chroma_db"))

    # 3. Initialize SQLite database schema and seed default accounts
    try:
        init_db()
        seed_default_admin()
        print("[STARTUP] SQLite database initialized and default accounts verified.")
    except Exception as e:
        print(f"[STARTUP ERROR] Database initialization failed: {e}")

    # 4. Check vector store count without resetting
    try:
        store = get_vector_store()
        count = store.get_chunk_count()
        print(f"[STARTUP] Persistent ChromaDB initialized. Existing chunks in collection: {count}")
    except Exception as e:
        print(f"[STARTUP WARNING] Vector store initialization: {e}")

    # 5. Warm up sentence transformers embedder
    try:
        print("[STARTUP] Preloading Sentence Transformers embedder...")
        embedder = get_embedder()
        embedder.embed_query("warmup")
        print("[STARTUP] Sentence Transformers embedder warm and ready.")
    except Exception as e:
        print(f"[STARTUP WARNING] Embedder warmup: {e}")

    yield

    print("[SHUTDOWN] Company Handbook Intelligence AI backend stopped.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = load_config()
    env_mode = os.environ.get("ENVIRONMENT", os.environ.get("APP_ENV", "development")).lower()
    is_prod = env_mode in ["production", "prod"]
    enable_docs = not is_prod or os.environ.get("ENABLE_DOCS", "false").lower() == "true"

    app = FastAPI(
        title="Company Handbook Intelligence AI",
        description="Enterprise RAG application for querying company handbook PDFs with page citations.",
        version="2.0.0",
        docs_url="/docs" if enable_docs else None,
        redoc_url="/redoc" if enable_docs else None,
        openapi_url="/openapi.json" if enable_docs else None,
        lifespan=lifespan,
    )

    cors_origins = config.get("server", {}).get("cors_origins", [
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core & backward-compatible routes (/ask, /upload, /health)
    app.include_router(api_router)

    # Enterprise SaaS routers
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(document_router)
    app.include_router(settings_router)
    app.include_router(feedback_router)
    app.include_router(admin_router)

    return app


app = create_app()

if __name__ == "__main__":
    cfg = load_config()
    host = cfg.get("server", {}).get("host", "127.0.0.1")
    port = cfg.get("server", {}).get("port", 8000)
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
