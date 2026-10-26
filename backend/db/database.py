"""
backend/db/database.py
SQLite database connection and schema management for enterprise Handbook AI.
Manages users, sessions, conversations, messages, documents, settings, feedback, and audit logs.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.utils.helpers import get_project_root, ensure_directory

DB_PATH = get_project_root() / "data" / "handbook_ai.db"


def get_db_connection() -> sqlite3.Connection:
    """Return a sqlite3 database connection with dictionary row access."""
    ensure_directory(DB_PATH.parent)
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all necessary enterprise tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'employee',
        avatar_url TEXT,
        created_at TEXT NOT NULL,
        last_login TEXT
    )
    """)

    # 2. Password reset tokens table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 3. Conversations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        preview TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 4. Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        sources_json TEXT DEFAULT '[]',
        timing_json TEXT DEFAULT '{}',
        is_error INTEGER NOT NULL DEFAULT 0,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
    )
    """)

    # 5. Documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        filename TEXT UNIQUE NOT NULL,
        original_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        chunks_count INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'indexed',
        uploaded_by TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        error_message TEXT
    )
    """)

    # 6. User Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id TEXT PRIMARY KEY,
        theme TEXT NOT NULL DEFAULT 'system',
        font_size TEXT NOT NULL DEFAULT 'medium',
        email_notifications INTEGER NOT NULL DEFAULT 1,
        chat_sound INTEGER NOT NULL DEFAULT 1,
        analytics_opt_in INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 7. Feedback table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        rating INTEGER NOT NULL,
        category TEXT DEFAULT 'general',
        comment TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # 8. Audit Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        action TEXT NOT NULL,
        details TEXT NOT NULL,
        ip_address TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


def seed_default_admin():
    """Ensure a default admin and demo user exist for immediate testing and SaaS demonstration."""
    from backend.auth.security import hash_password
    import uuid

    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    # 1. Admin User
    admin_email = "admin@company.com"
    cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    admin_row = cursor.fetchone()
    if not admin_row:
        admin_id = str(uuid.uuid4())
        pw_hash = hash_password("Admin@12345")
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, role, created_at)
            VALUES (?, ?, ?, ?, 'admin', ?)
        """, (admin_id, admin_email, pw_hash, "System Administrator", now))

        # Default settings
        cursor.execute("""
            INSERT INTO user_settings (user_id, theme, updated_at)
            VALUES (?, 'system', ?)
        """, (admin_id, now))

    # 2. Demo Employee User ("Abhishek", Employee)
    demo_email = "abhishek@company.com"
    cursor.execute("SELECT id FROM users WHERE email = ?", (demo_email,))
    demo_row = cursor.fetchone()
    if not demo_row:
        demo_id = str(uuid.uuid4())
        pw_hash = hash_password("Abhishek@123")
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, role, created_at)
            VALUES (?, ?, ?, ?, 'employee', ?)
        """, (demo_id, demo_email, pw_hash, "Abhishek Kumar", now))

        cursor.execute("""
            INSERT INTO user_settings (user_id, theme, updated_at)
            VALUES (?, 'system', ?)
        """, (demo_id, now))

    # 3. Synchronize existing handbook PDF in data/documents with documents table
    docs_dir = get_project_root() / "data" / "documents"
    if docs_dir.exists():
        for pdf_file in docs_dir.glob("*.pdf"):
            cursor.execute("SELECT id FROM documents WHERE filename = ?", (pdf_file.name,))
            if not cursor.fetchone():
                doc_id = str(uuid.uuid4())
                file_size = pdf_file.stat().st_size
                cursor.execute("""
                    INSERT INTO documents (id, filename, original_name, file_path, file_size, chunks_count, status, uploaded_by, uploaded_at)
                    VALUES (?, ?, ?, ?, ?, 378, 'indexed', 'system', ?)
                """, (doc_id, pdf_file.name, pdf_file.name, str(pdf_file), file_size, now))

    conn.commit()
    conn.close()
