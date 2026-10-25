"""
backend/api/chat_routes.py
Persistent conversation management and RAG question answering endpoints.
Stores all user prompts, assistant answers, latency breakdowns, and citations in SQLite.
"""

import uuid
import json
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field

from backend.db.database import get_db_connection
from backend.auth.security import get_current_user
from backend.vectordb.vector_store import get_vector_store
from backend.retrieval.retriever import get_retriever
from backend.embeddings.embedder import get_embedder
from backend.llm.llm_client import get_llm_client
from backend.utils.helpers import load_config

router = APIRouter(prefix="/api/conversations", tags=["Chat & Conversations"])


# --- Schemas ---

class CreateConversationRequest(BaseModel):
    title: Optional[str] = None


class RenameConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    sources: List[Dict[str, Any]] = []
    timing: Optional[Dict[str, Any]] = None
    is_error: bool = False
    timestamp: str


class ConversationSummary(BaseModel):
    id: str
    title: str
    preview: str
    created_at: str
    updated_at: str
    message_count: int


class ConversationDetail(BaseModel):
    id: str
    title: str
    preview: str
    created_at: str
    updated_at: str
    messages: List[MessageItem]


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000, description="Question for the Handbook AI")


# --- Endpoints ---

@router.get("", response_model=List[ConversationSummary])
def list_conversations(
    search: Optional[str] = Query(None, description="Search term for title or preview"),
    current_user: dict = Depends(get_current_user)
):
    """Retrieve all conversations for the authenticated user, ordered by most recent."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if search and search.strip():
        term = f"%{search.strip()}%"
        cursor.execute("""
            SELECT c.id, c.title, c.preview, c.created_at, c.updated_at,
                   COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_id = ? AND (c.title LIKE ? OR c.preview LIKE ?)
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        """, (current_user["id"], term, term))
    else:
        cursor.execute("""
            SELECT c.id, c.title, c.preview, c.created_at, c.updated_at,
                   COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.user_id = ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        """, (current_user["id"],))

    rows = cursor.fetchall()
    conn.close()

    return [
        ConversationSummary(
            id=r["id"],
            title=r["title"],
            preview=r["preview"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            message_count=r["message_count"]
        )
        for r in rows
    ]


@router.post("", response_model=ConversationDetail)
def create_conversation(req: CreateConversationRequest, current_user: dict = Depends(get_current_user)):
    """Create a new conversation session for the current user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine default sequential title
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (current_user["id"],))
    count = cursor.fetchone()[0]
    title = req.title.strip() if (req.title and req.title.strip()) else f"Chat {count + 1}"

    conv_id = f"conv-{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO conversations (id, user_id, title, preview, created_at, updated_at)
        VALUES (?, ?, ?, 'New conversation with Handbook AI', ?, ?)
    """, (conv_id, current_user["id"], title, now, now))

    conn.commit()
    conn.close()

    return ConversationDetail(
        id=conv_id,
        title=title,
        preview="New conversation with Handbook AI",
        created_at=now,
        updated_at=now,
        messages=[]
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve details and all messages of a specific conversation."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, preview, created_at, updated_at
        FROM conversations
        WHERE id = ? AND user_id = ?
    """, (conversation_id, current_user["id"]))
    conv = cursor.fetchone()

    if not conv:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    cursor.execute("""
        SELECT id, role, content, sources_json, timing_json, is_error, timestamp
        FROM messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    """, (conversation_id,))
    msg_rows = cursor.fetchall()
    conn.close()

    messages = []
    for m in msg_rows:
        try:
            sources = json.loads(m["sources_json"]) if m["sources_json"] else []
        except Exception:
            sources = []
        try:
            timing = json.loads(m["timing_json"]) if m["timing_json"] else None
        except Exception:
            timing = None

        messages.append(MessageItem(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            sources=sources,
            timing=timing,
            is_error=bool(m["is_error"]),
            timestamp=m["timestamp"]
        ))

    return ConversationDetail(
        id=conv["id"],
        title=conv["title"],
        preview=conv["preview"],
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        messages=messages
    )


@router.patch("/{conversation_id}", response_model=ConversationSummary)
def rename_conversation(
    conversation_id: str,
    req: RenameConversationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Rename a conversation title."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    new_title = req.title.strip()
    now = datetime.now().isoformat()
    cursor.execute("UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?", (new_title, now, conversation_id))
    cursor.execute("""
        SELECT c.id, c.title, c.preview, c.created_at, c.updated_at, COUNT(m.id) as message_count
        FROM conversations c
        LEFT JOIN messages m ON c.id = m.conversation_id
        WHERE c.id = ?
        GROUP BY c.id
    """, (conversation_id,))
    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return ConversationSummary(**dict(row))


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a conversation and all its messages."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, current_user["id"]))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

    conn.commit()
    conn.close()

    return {"message": "Conversation deleted successfully."}


@router.delete("")
def clear_all_conversations(current_user: dict = Depends(get_current_user)):
    """Clear all chat history for the authenticated user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM conversations WHERE user_id = ?", (current_user["id"],))
    user_convs = [r["id"] for r in cursor.fetchall()]

    if user_convs:
        placeholders = ",".join("?" for _ in user_convs)
        cursor.execute(f"DELETE FROM messages WHERE conversation_id IN ({placeholders})", user_convs)
        cursor.execute("DELETE FROM conversations WHERE user_id = ?", (current_user["id"],))

    conn.commit()
    conn.close()

    return {"message": "All conversations have been cleared."}


@router.post("/{conversation_id}/messages", response_model=MessageItem)
def send_message_to_conversation(
    conversation_id: str,
    req: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send question within a conversation, invoke RAG pipeline, and persist user & assistant messages.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, current_user["id"]))
    conv = cursor.fetchone()
    if not conv:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    clean_question = req.content.strip()
    now_user = datetime.now().isoformat()
    user_msg_id = f"msg-{uuid.uuid4().hex[:12]}"

    # Save user message
    cursor.execute("""
        INSERT INTO messages (id, conversation_id, role, content, timestamp)
        VALUES (?, ?, 'user', ?, ?)
    """, (user_msg_id, conversation_id, clean_question, now_user))

    # Update conversation title if first question
    cursor.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conversation_id,))
    total_msgs = cursor.fetchone()[0]
    updated_title = conv["title"]
    if total_msgs <= 1 and (conv["title"].startswith("Chat ") or conv["title"] == "New Chat"):
        updated_title = clean_question[:36] + "..." if len(clean_question) > 36 else clean_question

    cursor.execute("""
        UPDATE conversations
        SET title = ?, preview = ?, updated_at = ?
        WHERE id = ?
    """, (updated_title, clean_question, now_user, conversation_id))
    conn.commit()

    # RAG Retrieval & Generation
    vector_store = get_vector_store()
    if vector_store.get_chunk_count() == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No handbook has been indexed yet. Please upload a PDF handbook first."
        )

    config = load_config()
    top_k = config.get("rag", {}).get("top_k", 4)

    t_start = time.perf_counter()
    try:
        embedder = get_embedder()
        t_embed_start = time.perf_counter()
        query_vector = embedder.embed_query(clean_question)
        t_embed_ms = (time.perf_counter() - t_embed_start) * 1000

        retriever = get_retriever()
        t_ret_start = time.perf_counter()
        retrieval_data = retriever.retrieve_and_inspect(clean_question, top_k=top_k)
        sources = retrieval_data["sources"]
        t_ret_ms = (time.perf_counter() - t_ret_start) * 1000

        llm = get_llm_client()
        gen_result = llm.generate_answer(clean_question, sources, max_new_tokens=300)
        t_prompt_ms = gen_result["prompt_time_ms"]
        t_gen_ms = gen_result["generation_time_ms"]
        t_total_ms = (time.perf_counter() - t_start) * 1000

        supporting_pages = set(gen_result.get("supporting_pages", []))
        if "not contain" in gen_result["answer"].lower() or "insufficient" in gen_result["answer"].lower():
            final_sources = []
        elif supporting_pages:
            final_sources = [s for s in sources if int(s.get("page", -1)) in supporting_pages]
        else:
            final_sources = sources[:1] if sources else []

        formatted_sources = [{"page": int(s["page"]), "text": s["text"]} for s in final_sources]
        timing_data = {
            "embedding_ms": round(t_embed_ms, 2),
            "retrieval_ms": round(t_ret_ms, 2),
            "prompt_ms": round(t_prompt_ms, 2),
            "generation_ms": round(t_gen_ms, 2),
            "total_ms": round(t_total_ms, 2)
        }

        assistant_msg_id = f"msg-{uuid.uuid4().hex[:12]}"
        now_assist = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO messages (id, conversation_id, role, content, sources_json, timing_json, is_error, timestamp)
            VALUES (?, ?, 'assistant', ?, ?, ?, 0, ?)
        """, (
            assistant_msg_id,
            conversation_id,
            gen_result["answer"],
            json.dumps(formatted_sources),
            json.dumps(timing_data),
            now_assist
        ))
        cursor.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now_assist, conversation_id))
        conn.commit()
        conn.close()

        return MessageItem(
            id=assistant_msg_id,
            role="assistant",
            content=gen_result["answer"],
            sources=formatted_sources,
            timing=timing_data,
            is_error=False,
            timestamp=now_assist
        )

    except Exception as e:
        error_msg_id = f"msg-{uuid.uuid4().hex[:12]}"
        now_err = datetime.now().isoformat()
        error_content = f"Could not retrieve answer: {str(e)}"

        cursor.execute("""
            INSERT INTO messages (id, conversation_id, role, content, is_error, timestamp)
            VALUES (?, ?, 'assistant', ?, 1, ?)
        """, (error_msg_id, conversation_id, error_content, now_err))
        conn.commit()
        conn.close()

        return MessageItem(
            id=error_msg_id,
            role="assistant",
            content=error_content,
            sources=[],
            is_error=True,
            timestamp=now_err
        )
