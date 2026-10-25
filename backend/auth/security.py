"""
backend/auth/security.py
Security utilities for password hashing using bcrypt, JWT token generation/validation,
and role-based access control dependencies for FastAPI.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.db.database import get_db_connection

_DEV_EPHEMERAL_SECRET: Optional[str] = None


def get_jwt_secret() -> str:
    """
    Retrieve JWT signing secret.
    In production mode, strictly requires an environment-provided JWT_SECRET_KEY (min 32 chars)
    and terminates startup safely if missing, weak, or set to an insecure placeholder.
    """
    secret = os.environ.get("JWT_SECRET_KEY")
    env_mode = os.environ.get("ENVIRONMENT", os.environ.get("APP_ENV", "development")).lower()
    insecure_fallbacks = {
        "enterprise-handbook-ai-super-secret-key-change-in-production-2026",
        "secret",
        "changeme",
        "admin",
        "default",
        "password",
        "12345678"
    }

    if env_mode in ["production", "prod"]:
        if not secret or secret.strip() in insecure_fallbacks or len(secret.strip()) < 32:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: A strong JWT_SECRET_KEY (minimum 32 characters) "
                "must be explicitly set in the environment for production mode. "
                "Server startup aborted to prevent insecure token signing."
            )
        return secret.strip()

    # In development or testing mode:
    if secret and secret.strip():
        return secret.strip()

    global _DEV_EPHEMERAL_SECRET
    if _DEV_EPHEMERAL_SECRET is None:
        _DEV_EPHEMERAL_SECRET = secrets.token_hex(32)
    return _DEV_EPHEMERAL_SECRET


JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash plaintext password using bcrypt."""
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        pw_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pw_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(user_id: str, email: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)

    to_encode = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret(), algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Dict[str, Any]:
    """FastAPI dependency to retrieve the authenticated user from the Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication payload.",
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, role, avatar_url, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account removed.",
        )

    return dict(user)


def get_current_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """FastAPI dependency to enforce Administrator role."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to access this resource.",
        )
    return current_user
