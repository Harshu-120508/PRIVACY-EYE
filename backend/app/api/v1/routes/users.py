"""
Privacy Eye — User Profile & Account Management Routes
Endpoints:
- GET    /api/v1/users/me — Get authenticated user profile
- PATCH  /api/v1/users/me — Update profile details
- DELETE /api/v1/users/me — Permanently delete account with cascade
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database.session import get_db
from app.database.models import User, AuditLog
from app.schemas.schemas import (
    UserResponse,
    DeleteAccountRequest,
    UserConsentListResponse,
    UserConsentUpdateRequest,
    ConsentItem,
)
from app.core.security import get_current_user
from app.services.user_service import user_service

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile of the currently authenticated user."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    full_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user full name."""
    clean_name = full_name.strip()[:200]
    if not clean_name:
        raise HTTPException(status_code=400, detail="Name cannot be empty.")
    current_user.full_name = clean_name
    await db.commit()
    return current_user


@router.delete("/me")
async def delete_account(
    body: DeleteAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete the authenticated user account and all owned assets
    (analyses, signals, reports, sessions). Requires password confirmation.
    """
    user_id = current_user.id
    email = current_user.email

    deleted = await user_service.delete_account(db, current_user, body.password_confirmation)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password confirmation failed. Account was not deleted.",
        )

    db.add(AuditLog(
        user_id=None,
        action="ACCOUNT_DELETED",
        detail={"user_id": user_id, "email": email},
    ))
    await db.commit()
    logger.info("Account permanently deleted", user_id=user_id)

    return {
        "success": True,
        "message": "Your account and all associated data have been permanently deleted.",
    }


# ── Granular Consent Management ──────────────────────────────────────────────

@router.get("/me/consents", response_model=UserConsentListResponse)
async def get_user_consents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve user's granular consent records across all processing purposes.
    Initializes default unbundled consent states if not previously configured.
    """
    from app.database.models import UserConsent, ConsentPurpose
    from sqlalchemy import select

    result = await db.execute(
        select(UserConsent).where(UserConsent.user_id == current_user.id)
    )
    existing_consents = {c.purpose: c for c in result.scalars().all()}

    defaults = [
        (ConsentPurpose.MEDIA_PROCESSING, True),  # Necessary for detection
        (ConsentPurpose.SAVE_HISTORY, True),       # Default enabled for user audit log
        (ConsentPurpose.RETAIN_MEDIA, False),      # Disabled by default
        (ConsentPurpose.EXTERNAL_AI_SHARING, False),# Disabled by default
        (ConsentPurpose.MODEL_TRAINING, False),    # Opt-in only
        (ConsentPurpose.ANALYTICS, False),         # Optional
    ]

    items = []
    for purpose, default_val in defaults:
        if purpose in existing_consents:
            c = existing_consents[purpose]
            items.append(ConsentItem(
                purpose=purpose.value,
                granted=c.granted,
                policy_version=c.policy_version,
                granted_at=c.granted_at,
                withdrawn_at=c.withdrawn_at,
            ))
        else:
            items.append(ConsentItem(
                purpose=purpose.value,
                granted=default_val,
                policy_version="1.0.0",
                granted_at=current_user.created_at if default_val else None,
                withdrawn_at=None,
            ))

    return UserConsentListResponse(consents=items, policy_version="1.0.0")


@router.put("/me/consents", response_model=UserConsentListResponse)
async def update_user_consent(
    body: UserConsentUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update or withdraw consent for a specific processing purpose.
    Applies immediately to all future processing.
    """
    from app.database.models import UserConsent, ConsentPurpose
    from sqlalchemy import select
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    purpose_enum = ConsentPurpose(body.purpose.value)

    result = await db.execute(
        select(UserConsent).where(
            UserConsent.user_id == current_user.id,
            UserConsent.purpose == purpose_enum,
        )
    )
    consent_record = result.scalar_one_or_none()

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")[:500]

    if consent_record:
        consent_record.granted = body.granted
        consent_record.policy_version = body.policy_version
        if body.granted:
            consent_record.granted_at = now
            consent_record.withdrawn_at = None
        else:
            consent_record.withdrawn_at = now
        consent_record.ip_address = ip
        consent_record.user_agent = ua
    else:
        consent_record = UserConsent(
            user_id=current_user.id,
            purpose=purpose_enum,
            granted=body.granted,
            policy_version=body.policy_version,
            granted_at=now if body.granted else None,
            withdrawn_at=now if not body.granted else None,
            ip_address=ip,
            user_agent=ua,
        )
        db.add(consent_record)

    action = "CONSENT_GRANTED" if body.granted else "CONSENT_WITHDRAWN"
    db.add(AuditLog(
        user_id=current_user.id,
        action=action,
        resource_type="CONSENT",
        resource_id=consent_record.id,
        detail={"purpose": body.purpose.value, "granted": body.granted, "policy_version": body.policy_version},
        ip_address=ip,
    ))
    await db.commit()

    logger.info("User consent decision recorded", user_id=current_user.id, purpose=body.purpose.value, granted=body.granted)
    return await get_user_consents(db=db, current_user=current_user)
