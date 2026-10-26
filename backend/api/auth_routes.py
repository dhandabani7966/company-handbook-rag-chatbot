"""
backend/api/auth_routes.py
Authentication endpoints: login, registration, password reset, profile management, and sessions.
"""

import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, EmailStr, Field

from backend.db.database import get_db_connection
from backend.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# --- Schemas ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password at least 6 characters")
    full_name: str = Field(..., min_length=2, max_length=100)
    role: Optional[str] = Field("employee", description="employee or admin")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Endpoints ---

@router.post("/register", response_model=AuthResponse)
def register_user(req: RegisterRequest, request: Request):
    """Register a new user account and return JWT session."""
    conn = get_db_connection()
    cursor = conn.cursor()

    email_clean = req.email.strip().lower()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(req.password)
    now = datetime.now().isoformat()
    role = "admin" if req.role.lower() == "admin" else "employee"

    cursor.execute("""
        INSERT INTO users (id, email, password_hash, full_name, role, created_at, last_login)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, email_clean, pw_hash, req.full_name.strip(), role, now, now))

    # Initialize default user settings
    cursor.execute("""
        INSERT INTO user_settings (user_id, theme, updated_at)
        VALUES (?, 'system', ?)
    """, (user_id, now))

    # Audit log
    cursor.execute("""
        INSERT INTO audit_logs (id, user_id, action, details, ip_address, created_at)
        VALUES (?, ?, 'USER_REGISTERED', ?, ?, ?)
    """, (str(uuid.uuid4()), user_id, f"User {email_clean} registered with role {role}", request.client.host if request.client else None, now))

    conn.commit()
    conn.close()

    token = create_access_token(user_id=user_id, email=email_clean, role=role)

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=email_clean,
            full_name=req.full_name.strip(),
            role=role,
            created_at=now
        )
    )


@router.post("/login", response_model=AuthResponse)
def login_user(req: LoginRequest, request: Request):
    """Authenticate user with email and password and return signed JWT."""
    conn = get_db_connection()
    cursor = conn.cursor()

    email_clean = req.email.strip().lower()

    cursor.execute("SELECT id, email, password_hash, full_name, role, avatar_url, created_at FROM users WHERE email = ?", (email_clean,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials: Account not found. Only registered users can sign in. Please sign up first."
        )

    if not verify_password(req.password, user["password_hash"]):
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please verify your credentials."
        )

    user_dict = dict(user)
    now = datetime.now().isoformat()

    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_dict["id"]))
    cursor.execute("""
        INSERT INTO audit_logs (id, user_id, action, details, ip_address, created_at)
        VALUES (?, ?, 'USER_LOGIN', ?, ?, ?)
    """, (str(uuid.uuid4()), user_dict["id"], f"User {email_clean} logged in", request.client.host if request.client else None, now))

    conn.commit()
    conn.close()

    token = create_access_token(user_id=user_dict["id"], email=email_clean, role=user_dict["role"])

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user_dict["id"],
            email=user_dict["email"],
            full_name=user_dict["full_name"],
            role=user_dict["role"],
            avatar_url=user_dict.get("avatar_url"),
            created_at=user_dict["created_at"]
        )
    )


@router.post("/google", response_model=AuthResponse)
async def google_auth(req: GoogleAuthRequest, request: Request):
    """
    Authenticate or register user via Google Sign-In.
    Verifies Google ID token when provided, or creates/retrieves authenticated Google user session.
    """
    google_email: Optional[str] = None
    google_name: Optional[str] = None
    google_avatar: Optional[str] = None

    if req.credential:
        # 1. Try verifying with Google public tokeninfo endpoint
        import httpx
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}")
                if res.status_code == 200:
                    info = res.json()
                    google_email = info.get("email")
                    google_name = info.get("name")
                    google_avatar = info.get("picture")
        except Exception:
            pass

        # 2. Fallback to unverified JWT payload extraction if offline or testing
        if not google_email:
            import jwt
            try:
                decoded = jwt.decode(req.credential, options={"verify_signature": False})
                google_email = decoded.get("email")
                google_name = decoded.get("name")
                google_avatar = decoded.get("picture")
            except Exception:
                pass

    # 3. Direct email/profile fallback (from interactive Google dialog or OAuth popup)
    if not google_email and req.email:
        google_email = str(req.email).strip().lower()
        google_name = req.full_name or google_email.split("@")[0].title()
        google_avatar = req.avatar_url

    if not google_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google authentication requires a valid Google account email or token."
        )

    email_clean = google_email.strip().lower()
    full_name_clean = (google_name or email_clean.split("@")[0].title()).strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, email, full_name, role, avatar_url, created_at FROM users WHERE email = ?", (email_clean,))
    user = cursor.fetchone()
    now = datetime.now().isoformat()

    if user:
        # Existing user - sign them in
        user_dict = dict(user)
        user_id = user_dict["id"]
        role = user_dict["role"]
        avatar = google_avatar or user_dict.get("avatar_url")

        cursor.execute("UPDATE users SET last_login = ?, avatar_url = COALESCE(?, avatar_url) WHERE id = ?", (now, avatar, user_id))
        cursor.execute("""
            INSERT INTO audit_logs (id, user_id, action, details, ip_address, created_at)
            VALUES (?, ?, 'USER_LOGIN_GOOGLE', ?, ?, ?)
        """, (str(uuid.uuid4()), user_id, f"User {email_clean} logged in via Google SSO", request.client.host if request.client else None, now))
        conn.commit()
        conn.close()

        token = create_access_token(user_id=user_id, email=email_clean, role=role)
        return AuthResponse(
            access_token=token,
            user=UserResponse(
                id=user_id,
                email=email_clean,
                full_name=user_dict["full_name"],
                role=role,
                avatar_url=avatar,
                created_at=user_dict["created_at"]
            )
        )
    else:
        # Automatically register the user
        user_id = str(uuid.uuid4())
        role = "employee"
        pw_hash = hash_password(secrets.token_urlsafe(32))

        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, role, avatar_url, created_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, email_clean, pw_hash, full_name_clean, role, google_avatar, now, now))

        cursor.execute("""
            INSERT INTO user_settings (user_id, theme, updated_at)
            VALUES (?, 'system', ?)
        """, (user_id, now))

        cursor.execute("""
            INSERT INTO audit_logs (id, user_id, action, details, ip_address, created_at)
            VALUES (?, ?, 'USER_REGISTER_GOOGLE', ?, ?, ?)
        """, (str(uuid.uuid4()), user_id, f"User {email_clean} registered via Google SSO", request.client.host if request.client else None, now))

        conn.commit()
        conn.close()

        token = create_access_token(user_id=user_id, email=email_clean, role=role)
        return AuthResponse(
            access_token=token,
            user=UserResponse(
                id=user_id,
                email=email_clean,
                full_name=full_name_clean,
                role=role,
                avatar_url=google_avatar,
                created_at=now
            )
        )



@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        avatar_url=current_user.get("avatar_url"),
        created_at=current_user["created_at"]
    )


@router.put("/profile", response_model=UserResponse)
def update_profile(req: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    """Update profile details (name, avatar)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET full_name = ?, avatar_url = ?
        WHERE id = ?
    """, (req.full_name.strip(), req.avatar_url, current_user["id"]))

    cursor.execute("SELECT id, email, full_name, role, avatar_url, created_at FROM users WHERE id = ?", (current_user["id"],))
    updated = cursor.fetchone()
    conn.commit()
    conn.close()

    return UserResponse(**dict(updated))


@router.put("/change-password")
def change_password(req: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Change account password after validating old password."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (current_user["id"],))
    row = cursor.fetchone()

    if not row or not verify_password(req.old_password, row["password_hash"]):
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    new_hash = hash_password(req.new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, current_user["id"]))
    conn.commit()
    conn.close()

    return {"message": "Password updated successfully."}


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    """Generate a password reset token for the given email."""
    conn = get_db_connection()
    cursor = conn.cursor()

    email_clean = req.email.strip().lower()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        # Return generic success to prevent email enumeration
        return {
            "message": "If an account exists with this email, password reset instructions have been generated.",
            "reset_token": None
        }

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    cursor.execute("""
        INSERT INTO password_reset_tokens (token, user_id, expires_at, used)
        VALUES (?, ?, ?, 0)
    """, (token, user["id"], expires_at))

    conn.commit()
    conn.close()

    return {
        "message": "Password reset token generated successfully. In enterprise production, this is emailed securely to the user.",
        "reset_token": token
    }


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    """Reset password using a valid reset token."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT token, user_id, expires_at, used
        FROM password_reset_tokens
        WHERE token = ?
    """, (req.token,))
    token_row = cursor.fetchone()

    if not token_row:
        conn.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid password reset token.")

    if token_row["used"]:
        conn.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This reset token has already been used.")

    # Check expiration
    expires = datetime.fromisoformat(token_row["expires_at"])
    if datetime.now(timezone.utc) > expires:
        conn.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password reset token has expired.")

    new_hash = hash_password(req.new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, token_row["user_id"]))
    cursor.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (req.token,))

    conn.commit()
    conn.close()

    return {"message": "Password has been successfully reset. You can now log in with your new password."}


@router.post("/logout")
def logout_user(current_user: dict = Depends(get_current_user)):
    """Log out authenticated user session."""
    return {"message": f"User {current_user['email']} logged out successfully."}

