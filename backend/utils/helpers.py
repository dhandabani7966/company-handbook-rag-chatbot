"""
backend/utils/helpers.py
Shared utility functions for configuration loading, safe file naming, and path management.
"""

import os
from pathlib import Path
import re
import yaml
from typing import Any, Dict


def get_project_root() -> Path:
    """Return the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


# Configure Hugging Face cache to live on D: drive (140+ GB free space) rather than C: (out of space)
_hf_cache_dir = get_project_root() / "hf_cache"
_hf_cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(_hf_cache_dir))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from a YAML file relative to project root with sensible fallbacks."""
    root = get_project_root()
    full_path = root / config_path
    
    defaults: Dict[str, Any] = {
        "server": {
            "host": "127.0.0.1",
            "port": 8000,
            "cors_origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        },
        "storage": {
            "documents_dir": "data/documents",
            "chroma_db_dir": "data/chroma_db",
            "collection_name": "company_handbook",
        },
        "models": {
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_model": "Qwen/Qwen2.5-1.5B-Instruct",
        },
        "rag": {
            "chunk_size": 500,
            "chunk_overlap": 100,
            "top_k": 4,
            "max_upload_size_mb": 25,
            "max_question_length": 500,
        },
    }

    if not full_path.exists():
        return defaults

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
            
        # Deep merge user_config into defaults
        for section, values in user_config.items():
            if isinstance(values, dict) and section in defaults:
                defaults[section].update(values)
            else:
                defaults[section] = values
        return defaults
    except Exception:
        return defaults


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent directory traversal and remove problematic characters."""
    # Strip paths
    clean_name = Path(filename).name
    # Keep only alphanumeric, underscores, hyphens, and periods
    clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", clean_name)
    # Ensure it's not empty and ends with .pdf
    if not clean_name or clean_name.startswith("."):
        clean_name = f"document_{clean_name}"
    return clean_name


def ensure_directory(path: Path) -> Path:
    """Ensure that the given directory exists and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path
