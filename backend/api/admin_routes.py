"""
backend/api/admin_routes.py
Admin Dashboard metrics, user role management, system health, and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from backend.db.database import get_db_connection
from backend.auth.security import get_current_admin
from backend.vectordb.vector_store import get_vector_store

router = APIRouter(prefix="/api/admin", tags=["admin"])


class RoleUpdate(BaseModel):
    role: str  # 'admin' or 'employee'


@router.get("/overview")
async def get_overview(admin: dict = Depends(get_current_admin)):
    """Summary statistics for admin dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # User counts
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Document counts
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]

    # Conversation counts
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total_convs = cursor.fetchone()[0]

    # Message / Queries count
    cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'")
    total_queries = cursor.fetchone()[0]

    # Feedback stats
    cursor.execute("SELECT COUNT(*), AVG(rating) FROM feedback")
    fb_row = cursor.fetchone()
    total_feedback = fb_row[0] or 0
    avg_rating = round(fb_row[1] or 0.0, 1)

    # Vector store chunk count
    try:
        vs = get_vector_store()
        vector_chunks = vs.get_chunk_count()
        vector_status = "healthy"
    except Exception as e:
        vector_chunks = 0
        vector_status = f"unhealthy: {e}"

    conn.close()

    return {
        "metrics": {
            "total_users": total_users,
            "total_documents": total_docs,
            "total_conversations": total_convs,
            "total_queries": total_queries,
            "average_feedback_rating": avg_rating,
            "vector_store_chunks": vector_chunks,
            "rag_health": vector_status,
            "system_uptime": "99.98%"
        }
    }


@router.get("/activity")
async def get_activity_analytics(admin: dict = Depends(get_current_admin)):
    """7-day conversation activity and top queries."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 7-day conversation histogram
    today = datetime.now().date()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    activity_data = []

    for d in days:
        d_str = d.isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM conversations
            WHERE DATE(created_at) = ?
        """, (d_str,))
        count = cursor.fetchone()[0]
        # Day abbreviation, e.g., 'Mon', 'Tue'
        label = d.strftime("%a")
        activity_data.append({"day": label, "date": d_str, "conversations": count})

    # 2. Top asked questions (user messages)
    cursor.execute("""
        SELECT content, COUNT(*) as query_count, MAX(timestamp) as last_asked
        FROM messages
        WHERE role = 'user'
        GROUP BY content
        ORDER BY query_count DESC
        LIMIT 6
    """)
    top_questions = [
        {
            "query": row["content"],
            "count": row["query_count"],
            "last_asked": row["last_asked"]
        }
        for row in cursor.fetchall()
    ]

    conn.close()

    return {
        "weekly_activity": activity_data,
        "top_questions": top_questions
    }


@router.get("/users")
async def list_users(admin: dict = Depends(get_current_admin)):
    """List all registered users with their roles and activity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, full_name, role, avatar_url, created_at, last_login
        FROM users
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    users = [dict(r) for r in rows]
    conn.close()
    return {"users": users}


@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, payload: RoleUpdate, admin: dict = Depends(get_current_admin)):
    """Promote or demote user role (admin / employee)."""
    if payload.role not in ["admin", "employee"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either 'admin' or 'employee'"
        )

    if user_id == admin["id"] and payload.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote your own admin account"
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    target_user = cursor.fetchone()
    if not target_user:
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (payload.role, user_id))

    # Audit log
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO audit_logs (id, user_id, action, details, created_at)
        VALUES (?, ?, 'update_user_role', ?, ?)
    """, (str(uuid.uuid4()), admin["id"], f"Changed {target_user['email']} role to {payload.role}", now))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"User role updated to {payload.role}",
        "user_id": user_id,
        "new_role": payload.role
    }


@router.get("/audit-logs")
async def get_audit_logs(admin: dict = Depends(get_current_admin)):
    """Recent system audit logs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.*, u.email as user_email
        FROM audit_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
        LIMIT 50
    """)
    logs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"logs": logs}
