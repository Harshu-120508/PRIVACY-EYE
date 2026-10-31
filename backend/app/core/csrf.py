"""
Privacy Eye — Cryptographic Double-Submit CSRF Protection Utilities
Adheres to OWASP CSRF Prevention Cheat Sheet:
- Token generation with cryptographic entropy (secrets.token_urlsafe)
- HMAC-SHA256 signature binding the token to server secret and session ID
- Constant-time verification (secrets.compare_digest)
- Token rotation lifecycle helpers
"""
import hmac
import hashlib
import secrets
from typing import Optional
from fastapi import Response

from app.core.config import settings


def get_csrf_secret() -> str:
    """Retrieve secret key used for HMAC signing of CSRF tokens."""
    return getattr(settings, "CSRF_SECRET_KEY", None) or settings.APP_SECRET_KEY or "privacy-eye-csrf-secret-fallback-key"


def generate_csrf_token(session_id: Optional[str] = None) -> str:
    """
    Generate an OWASP HMAC-signed Double-Submit CSRF token.
    Format: <entropy>.<signature>
    Bound to session_id when available, signed with server secret from env.
    """
    entropy = secrets.token_urlsafe(32)
    secret = get_csrf_secret().encode("utf-8")
    payload = f"{entropy}:{session_id or ''}".encode("utf-8")
    sig = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return f"{entropy}.{sig}"


def validate_csrf_token(
    cookie_token: Optional[str],
    header_token: Optional[str],
    session_id: Optional[str] = None,
) -> bool:
    """
    Validate CSRF token:
    1. Check presence of both cookie and header tokens.
    2. Constant-time comparison between cookie and header (double-submit).
    3. Verify cryptographic HMAC signature against server secret.
    """
    if not cookie_token or not header_token:
        return False

    # Constant-time comparison against header to prevent timing attacks
    if not secrets.compare_digest(cookie_token, header_token):
        return False

    parts = cookie_token.split(".")
    if len(parts) != 2:
        return False

    entropy, sig = parts[0], parts[1]
    secret = get_csrf_secret().encode("utf-8")

    # Check HMAC signature: verify if bound to session_id or unbound
    if session_id:
        bound_payload = f"{entropy}:{session_id}".encode("utf-8")
        expected_bound = hmac.new(secret, bound_payload, hashlib.sha256).hexdigest()
        if secrets.compare_digest(sig, expected_bound):
            return True

    unbound_payload = f"{entropy}:".encode("utf-8")
    expected_unbound = hmac.new(secret, unbound_payload, hashlib.sha256).hexdigest()
    return secrets.compare_digest(sig, expected_unbound)


def set_csrf_cookie(response: Response, session_id: Optional[str] = None) -> str:
    """
    Set or rotate the CSRF token cookie on response.
    Readable by JS (httponly=False) with SameSite=Lax and Secure in production.
    """
    is_prod = settings.APP_ENV == "production"
    token = generate_csrf_token(session_id=session_id)
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # Must be readable by JavaScript for Double-Submit
        samesite="lax",
        secure=is_prod,
        max_age=86400,   # 24 hours
        path="/",
    )
    return token


def clear_csrf_cookie(response: Response) -> None:
    """Purge CSRF token cookie on logout."""
    is_prod = settings.APP_ENV == "production"
    response.delete_cookie(key="csrf_token", path="/", secure=is_prod, samesite="lax")

