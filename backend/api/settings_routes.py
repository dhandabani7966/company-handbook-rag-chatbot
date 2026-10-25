"""
backend/api/settings_routes.py
User and application preferences endpoint.
Supports theme, font size, notifications, sound, and privacy/analytics options.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.db.database import get_db_connection
from backend.auth.security import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    font_size: Optional[str] = None
    email_notifications: Optional[bool] = None
    chat_sound: Optional[bool] = None
    analytics_opt_in: Optional[bool] = None


@router.get("")
async def get_settings(user: dict = Depends(get_current_user)):
    """Fetch user settings, auto-creating defaults if not present."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user["id"],))
    row = cursor.fetchone()
    if not row:
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO user_settings (user_id, theme, font_size, email_notifications, chat_sound, analytics_opt_in, updated_at)
            VALUES (?, 'system', 'medium', 1, 1, 1, ?)
        """, (user["id"], now))
        conn.commit()
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user["id"],))
        row = cursor.fetchone()

    data = dict(row)
    conn.close()
    return {
        "user_id": data["user_id"],
        "theme": data["theme"],
        "font_size": data["font_size"],
        "email_notifications": bool(data["email_notifications"]),
        "chat_sound": bool(data["chat_sound"]),
        "analytics_opt_in": bool(data["analytics_opt_in"]),
        "updated_at": data["updated_at"]
    }


@router.put("")
async def update_settings(payload: SettingsUpdate, user: dict = Depends(get_current_user)):
    """Update settings for the logged-in user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user["id"],))
    existing = cursor.fetchone()
    now = datetime.now().isoformat()

    theme = payload.theme if payload.theme is not None else (existing["theme"] if existing else "system")
    font_size = payload.font_size if payload.font_size is not None else (existing["font_size"] if existing else "medium")
    email_notif = int(payload.email_notifications) if payload.email_notifications is not None else (existing["email_notifications"] if existing else 1)
    chat_sound = int(payload.chat_sound) if payload.chat_sound is not None else (existing["chat_sound"] if existing else 1)
    analytics = int(payload.analytics_opt_in) if payload.analytics_opt_in is not None else (existing["analytics_opt_in"] if existing else 1)

    if existing:
        cursor.execute("""
            UPDATE user_settings
            SET theme = ?, font_size = ?, email_notifications = ?, chat_sound = ?, analytics_opt_in = ?, updated_at = ?
            WHERE user_id = ?
        """, (theme, font_size, email_notif, chat_sound, analytics, now, user["id"]))
    else:
        cursor.execute("""
            INSERT INTO user_settings (user_id, theme, font_size, email_notifications, chat_sound, analytics_opt_in, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user["id"], theme, font_size, email_notif, chat_sound, analytics, now))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": "Settings updated successfully",
        "settings": {
            "theme": theme,
            "font_size": font_size,
            "email_notifications": bool(email_notif),
            "chat_sound": bool(chat_sound),
            "analytics_opt_in": bool(analytics),
            "updated_at": now
        }
    }
