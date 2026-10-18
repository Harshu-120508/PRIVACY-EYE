"""
Privacy Eye — Production Authentication & Security Engine
Implements Argon2id password hashing, JWT signing, session token hashing,
and dual-mode (Bearer Header + HttpOnly Cookie) user extraction.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import argon2
import bcrypt
import structlog

from app.core.config import settings
from app.database.session import get_db

logger = structlog.get_logger(__name__)

# Primary Argon2id hasher configured to OWASP recommendations
_argon2_hasher = argon2.PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    type=argon2.Type.ID,
)

bearer_scheme = HTTPBearer(auto_error=False)


# ── Password Cryptography ───────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash password using Argon2id with automatic salt generation."""
    validate_password_policy(password)
    return _argon2_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify password against hash.
    Supports primary Argon2id hashes with seamless backward-compatible
    fallback for legacy bcrypt records.
    """
    if not plain or not hashed:
        return False

    # Check for Argon2id prefix
    if hashed.startswith("$argon2id$") or hashed.startswith("$argon2"):
        try:
            return _argon2_hasher.verify(hashed, plain)
        except (argon2.exceptions.VerifyMismatchError, argon2.exceptions.VerificationError, argon2.exceptions.InvalidHashError):
            return False

    # Check for legacy bcrypt prefix
    if hashed.startswith("$2b$") or hashed.startswith("$2a$"):
        try:
            pwd_bytes = plain.encode("utf-8")[:72]
            return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
        except Exception:
            return False

    return False


def validate_password_policy(password: str, confirm_password: Optional[str] = None) -> None:
    """Enforce NIST-aligned, usable password policy."""
    if not password:
        raise ValueError("Password cannot be empty.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(password) > 128:
        raise ValueError("Password cannot exceed 128 characters.")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one numeric digit.")
    if confirm_password is not None and password != confirm_password:
        raise ValueError("Password and confirmation do not match.")


# ── Token & Session Cryptography ─────────────────────────────────────────────

def generate_secure_token() -> str:
    """Generate a high-entropy cryptographically secure random token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Compute SHA-256 digest of token for safe server-side storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str,
    role: str = "USER",
    session_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
    extra: dict = {},
) -> str:
    """Generate signed JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "role": role,
        "sid": session_id,
        "exp": expire,
        "type": "access",
        **extra,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    session_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate signed JWT refresh token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload = {
        "sub": subject,
        "sid": session_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_verification_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate signed JWT email verification token (defaults to 24 hours)."""
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(hours=24)
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "type": "email_verification",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and cryptographically verify a JWT."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Authentication Dependencies ──────────────────────────────────────────────

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Extracts and authenticates the current user.
    Supports dual transport:
    1. HTTP Authorization: Bearer <token> header (API / mobile / Swagger)
    2. HttpOnly Cookie: access_token (browser Next.js sessions)
    """
    from app.services.user_service import user_service
    from app.database.models import UserSession

    token: Optional[str] = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")

    user_id = payload.get("sub")
    session_id = payload.get("sid")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token identity.")

    # If token is tied to a database session, verify session is active
    if session_id:
        sess_result = await db.execute(
            select(UserSession).where(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
        )
        sess = sess_result.scalar_one_or_none()
        if not sess:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been terminated or revoked.",
            )
        # Update last used timestamp
        sess.last_used_at = datetime.now(timezone.utc)

    user = await user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    return user


async def require_admin(current_user=Depends(get_current_user)):
    """Authorize access strictly for users with ADMIN role."""
    from app.database.models import UserRole
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )
    return current_user
