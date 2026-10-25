"""
backend/api/feedback_routes.py
User feedback and rating submissions endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

from backend.db.database import get_db_connection
from backend.auth.security import get_current_user, get_current_admin

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5 stars")
    category: Optional[str] = "general"
    comment: str = Field(min_length=3, description="Feedback message")


@router.post("")
async def submit_feedback(payload: FeedbackCreate, user: dict = Depends(get_current_user)):
    """Submit rating and feedback."""
    feedback_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (id, user_id, rating, category, comment, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (feedback_id, user["id"], payload.rating, payload.category, payload.comment.strip(), now))

    # Log action
    cursor.execute("""
        INSERT INTO audit_logs (id, user_id, action, details, created_at)
        VALUES (?, ?, 'submit_feedback', ?, ?)
    """, (str(uuid.uuid4()), user["id"], f"Rating: {payload.rating} - {payload.category}", now))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "id": feedback_id,
        "message": "Thank you for your feedback! It helps us improve Handbook AI."
    }


@router.get("")
async def get_all_feedback(admin: dict = Depends(get_current_admin)):
    """Admin endpoint to view all submitted feedback."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.*, u.email as user_email, u.full_name as user_name
        FROM feedback f
        JOIN users u ON f.user_id = u.id
        ORDER BY f.created_at DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()

    avg_rating = 0.0
    if results:
        avg_rating = sum(r["rating"] for r in results) / len(results)

    return {
        "total": len(results),
        "average_rating": round(avg_rating, 2),
        "feedback": results
    }
