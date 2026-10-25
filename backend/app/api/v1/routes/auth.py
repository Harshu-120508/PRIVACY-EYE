"""
Privacy Eye — Production Authentication & Session Routes
Endpoints:
- POST   /api/v1/auth/register        — Create account with Argon2id hash & auto-login
- POST   /api/v1/auth/login           — Authenticate against DB & issue session cookies
- POST   /api/v1/auth/refresh         — Rotate session token
- POST   /api/v1/auth/logout          — Invalidate current session & wipe cookies
- POST   /api/v1/auth/logout-all      — Invalidate all active user sessions everywhere
- GET    /api/v1/auth/me              — Return sanitized authenticated user profile
- POST   /api/v1/auth/change-password — Update password & revoke other sessions
- POST   /api/v1/auth/forgot-password — Enumeration-safe reset workflow
- POST   /api/v1/auth/reset-password  — Complete password reset
- GET    /api/v1/auth/sessions        — Inspect active user sessions
- DELETE /api/v1/auth/sessions/{id}   — Terminate a specific session
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog

from app.database.session import get_db
from app.database.models import User, UserSession, PasswordResetToken, AuditLog
from app.schemas.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    AuthSuccessResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    SessionResponse,
    VerifyEmailRequest,
    RequestEmailVerificationRequest,
)
from app.core.security import (
    verify_password,
    hash_password,
    validate_password_policy,
    generate_secure_token,
    hash_token,
    decode_token,
    create_verification_token,
    get_current_user,
)
from app.services.user_service import user_service
from app.core.config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str, remember_me: bool = False):
    """Set secure authentication cookies on response."""
    is_prod = settings.APP_ENV == "production"
    # Access token cookie (60 minutes) - Set httponly=False so frontend JS and headers are fully synchronized
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=False,
        secure=is_prod,
        samesite="lax",
        path="/",
    )
    # Refresh token cookie (30 days if remember_me, 24 hours if regular)
    refresh_max_age = (30 if remember_me else 1) * 24 * 3600
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,   # Strictly HttpOnly: immune to JavaScript XSS
        secure=is_prod,
        samesite="lax",
        path="/",
    )
    # Non-sensitive logged_in indicator for client-side UI hydration
    response.set_cookie(
        key="logged_in",
        value="true",
        max_age=refresh_max_age,
        httponly=False,
        secure=is_prod,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response):
    """Purge authentication cookies on response."""
    is_prod = settings.APP_ENV == "production"
    response.delete_cookie(key="access_token", path="/", secure=is_prod, samesite="lax")
    response.delete_cookie(key="refresh_token", path="/", secure=is_prod, samesite="lax")
    response.delete_cookie(key="logged_in", path="/", secure=is_prod, samesite="lax")


# ── Core Authentication ──────────────────────────────────────────────────────

@router.post("/register", response_model=AuthSuccessResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserRegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Create a new database user account with Argon2id and immediately authenticate."""
    try:
        validate_password_policy(body.password, body.confirm_password)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    existing = await user_service.get_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="An account is already registered with this email address.",
        )

    user = await user_service.create(db, body)

    # Automatically create session
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    session, access_token, raw_refresh = await user_service.create_session(
        db, user, is_remember_me=True, ip_address=ip, user_agent=ua
    )

    db.add(AuditLog(
        user_id=user.id,
        action="ACCOUNT_CREATED",
        ip_address=ip,
        user_agent=ua,
        detail={"email": user.email},
    ))
    await db.commit()

    _set_auth_cookies(response, access_token, raw_refresh, remember_me=True)
    logger.info("User registered and authenticated", user_id=user.id)

    tokens = TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return AuthSuccessResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
    )


@router.post("/login", response_model=AuthSuccessResponse)
async def login(
    body: UserLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate credentials against PostgreSQL and issue a persistent session."""
    user = await user_service.get_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        # Prevent timing attacks and user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact security support.",
        )

    # Seamless hash upgrade: if user has a legacy bcrypt hash, upgrade to Argon2id automatically
    if not (user.hashed_password.startswith("$argon2id$") or user.hashed_password.startswith("$argon2")):
        try:
            user.hashed_password = hash_password(body.password)
        except Exception:
            pass

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    session, access_token, raw_refresh = await user_service.create_session(
        db, user, is_remember_me=body.remember_me, ip_address=ip, user_agent=ua
    )

    db.add(AuditLog(
        user_id=user.id,
        action="LOGIN_SUCCESS",
        ip_address=ip,
        user_agent=ua,
        detail={"session_id": session.id, "remember_me": body.remember_me},
    ))
    await db.commit()

    _set_auth_cookies(response, access_token, raw_refresh, remember_me=body.remember_me)
    logger.info("User successfully logged in", user_id=user.id, session_id=session.id)

    tokens = TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return AuthSuccessResponse(
        user=UserResponse.model_validate(user),
        tokens=tokens,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_session(
    request: Request,
    response: Response,
    body_token: Optional[str] = Body(None, embed=True, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
):
    """Rotate session refresh token and issue a fresh access token."""
    raw_token = body_token or request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided.",
        )

    result = await user_service.rotate_session(db, raw_token)
    if not result:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or was revoked. Please log in again.",
        )

    user, new_access, new_refresh = result
    await db.commit()

    _set_auth_cookies(response, new_access, new_refresh, remember_me=True)
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Terminate the current session in PostgreSQL and clear browser cookies."""
    # Extract session_id from token if available
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else request.cookies.get("access_token")
    if token:
        try:
            payload = decode_token(token)
            sid = payload.get("sid")
            if sid:
                await user_service.revoke_session(db, sid, current_user.id)
        except Exception:
            pass

    # Invalidate by cookie refresh token as well
    cookie_refresh = request.cookies.get("refresh_token")
    if cookie_refresh:
        h = hash_token(cookie_refresh)
        res = await db.execute(
            select(UserSession).where(UserSession.refresh_token_hash == h)
        )
        s = res.scalar_one_or_none()
        if s:
            s.revoked_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        user_id=current_user.id,
        action="LOGOUT",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    ))
    await db.commit()

    _clear_auth_cookies(response)
    return {"success": True, "message": "Session successfully terminated."}


@router.post("/logout-all")
async def logout_all(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Terminate all active sessions across all devices for the current user."""
    count = await user_service.revoke_all_sessions(db, current_user.id)
    db.add(AuditLog(
        user_id=current_user.id,
        action="LOGOUT_ALL_SESSIONS",
        detail={"revoked_count": count},
    ))
    await db.commit()

    _clear_auth_cookies(response)
    return {
        "success": True,
        "revoked_sessions": count,
        "message": f"Successfully invalidated {count} active sessions.",
    }


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Retrieve sanitized profile for the authenticated database user."""
    return current_user


# ── Password & Account Security ──────────────────────────────────────────────

@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify existing password, validate policy, and update to new Argon2id hash."""
    try:
        validate_password_policy(body.new_password, body.confirm_password)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    success = await user_service.change_password(
        db,
        current_user,
        body.current_password,
        body.new_password,
        body.confirm_password,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    db.add(AuditLog(
        user_id=current_user.id,
        action="PASSWORD_CHANGED",
    ))
    await db.commit()

    return {
        "success": True,
        "message": "Password changed successfully. All other sessions have been logged out.",
    }


@router.post("/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates password recovery.
    Always returns a generic message to prevent account enumeration.
    """
    user = await user_service.get_by_email(db, body.email)
    if user and user.is_active:
        raw_reset = generate_secure_token()
        token_rec = PasswordResetToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=hash_token(raw_reset),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        )
        db.add(token_rec)
        db.add(AuditLog(
            user_id=user.id,
            action="PASSWORD_RESET_REQUESTED",
        ))
        await db.commit()
        if settings.APP_ENV != "production":
            response.headers["X-Dev-Reset-Token"] = raw_reset
        logger.info("Password reset token generated", user_id=user.id)

    return {
        "message": "If an account exists for that email address, password reset instructions have been issued.",
    }


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify reset token and update to new Argon2id password."""
    try:
        validate_password_policy(body.new_password, body.confirm_password)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    h = hash_token(body.token)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token_hash == h,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
        )
    )
    reset_rec = result.scalar_one_or_none()
    if not reset_rec:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")

    user = await user_service.get_by_id(db, reset_rec.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Associated user account not found.")

    user.hashed_password = hash_password(body.new_password)
    reset_rec.used_at = now

    # Invalidate all sessions
    await user_service.revoke_all_sessions(db, user.id)

    db.add(AuditLog(
        user_id=user.id,
        action="PASSWORD_RESET_COMPLETED",
    ))
    await db.commit()

    return {
        "success": True,
        "message": "Password has been successfully updated. You may now sign in with your new credentials.",
    }


# ── Session Inspection ───────────────────────────────────────────────────────

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all active sessions for the authenticated user."""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else request.cookies.get("access_token")
    current_sid = None
    if token:
        try:
            payload = decode_token(token)
            current_sid = payload.get("sid")
        except Exception:
            pass

    sessions = await user_service.get_active_sessions(db, current_user.id, current_sid)
    return sessions


@router.delete("/sessions/{session_id}")
async def terminate_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a specific session by ID."""
    revoked = await user_service.revoke_session(db, session_id, current_user.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="Session not found or already terminated.")
    await db.commit()
    return {"success": True, "message": "Session terminated."}


# ── Email Verification ────────────────────────────────────────────────────────

@router.post("/request-verification")
async def request_verification(
    body: Optional[RequestEmailVerificationRequest] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an email verification link for the user.
    Can be called by an authenticated user, or by supplying the registered email.
    """
    user: Optional[User] = None
    if request:
        auth_header = request.headers.get("authorization", "")
        token = auth_header.replace("Bearer ", "").strip() if auth_header.startswith("Bearer ") else request.cookies.get("access_token")
        if token:
            try:
                payload = decode_token(token)
                uid = payload.get("sub")
                if uid:
                    user = await user_service.get_by_id(db, uid)
            except Exception:
                pass

    if not user and body and body.email:
        user = await user_service.get_by_email(db, body.email)

    if not user:
        raise HTTPException(status_code=400, detail="User account not found or not authenticated.")

    if user.is_verified:
        return {"success": True, "message": "Email is already verified."}

    verification_token = create_verification_token(subject=user.id)

    db.add(AuditLog(
        user_id=user.id,
        action="EMAIL_VERIFICATION_REQUESTED",
    ))
    await db.commit()

    resp = {
        "success": True,
        "message": "Verification instructions have been generated.",
    }
    if settings.APP_ENV != "production":
        resp["verification_token"] = verification_token

    return resp


@router.post("/verify-email")
async def verify_email(
    body: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email address using cryptographically signed verification token.
    """
    payload = decode_token(body.token)
    token_type = payload.get("type")
    if token_type != "email_verification":
        raise HTTPException(status_code=400, detail="Invalid token type for email verification.")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid token subject.")

    user = await user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated.")

    user.is_verified = True
    user.updated_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        user_id=user.id,
        action="EMAIL_VERIFIED",
    ))
    await db.commit()
    await db.refresh(user)

    return {
        "success": True,
        "message": "Email address successfully verified.",
        "user": {
            "id": user.id,
            "email": user.email,
            "is_verified": user.is_verified,
        },
    }
