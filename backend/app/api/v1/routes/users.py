"""
Privacy Eye — User Profile & Account Management Routes
Endpoints:
- GET    /api/v1/users/me — Get authenticated user profile
- PATCH  /api/v1/users/me — Update profile details
- DELETE /api/v1/users/me — Permanently delete account with cascade
"""
import hashlib
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
import structlog

from app.database.session import get_db
from app.database.models import User, AuditLog
from app.schemas.schemas import (
    UserResponse,
    DeleteAccountRequest,
    UserConsentListResponse,
    UserConsentUpdateRequest,
    ConsentItem,
    UserAuditLogResponse,
    UserAuditLogItem,
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
    (analyses, signals, reports, sessions, face training samples).
    Requires password confirmation. Enforces GDPR Article 17 Right to Erasure.
    """
    user_id = current_user.id
    email = current_user.email
    email_sha256 = hashlib.sha256(email.encode("utf-8")).hexdigest()

    deleted = await user_service.delete_account(db, current_user, body.password_confirmation)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password confirmation failed. Account was not deleted.",
        )

    # Record compliant anonymized tombstone without persisting plaintext email
    db.add(AuditLog(
        user_id=None,
        action="ACCOUNT_DELETED",
        resource_type="USER",
        resource_id=user_id,
        detail={
            "anonymized_user_id": user_id,
            "email_sha256": email_sha256,
            "erasure_type": "GDPR_ARTICLE_17_RIGHT_TO_BE_FORGOTTEN",
            "status": "PERMANENTLY_ERASED",
        },
    ))
    await db.commit()
    logger.info("Account permanently deleted under GDPR Article 17", user_id=user_id)

    return {
        "success": True,
        "message": "Your account and all associated data have been permanently deleted.",
    }


@router.get("/me/export")
async def export_user_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GDPR Article 20 Right to Data Portability.
    Exports all personal account data, preferences, consents, analysis audit history,
    and security event logs in structured, machine-readable JSON format.
    """
    # Consents
    from app.database.models import MediaAnalysis, UserConsent, UserPreferences, ConsentPurpose
    from sqlalchemy.orm import selectinload

    consents_res = await db.execute(select(UserConsent).where(UserConsent.user_id == current_user.id))
    existing_consents = {c.purpose: c for c in consents_res.scalars().all()}
    defaults = [
        (ConsentPurpose.MEDIA_PROCESSING, True),
        (ConsentPurpose.SAVE_HISTORY, True),
        (ConsentPurpose.RETAIN_MEDIA, False),
        (ConsentPurpose.EXTERNAL_AI_SHARING, False),
        (ConsentPurpose.MODEL_TRAINING, False),
        (ConsentPurpose.ANALYTICS, False),
    ]
    consents = []
    for purpose_enum, default_val in defaults:
        if purpose_enum in existing_consents:
            c = existing_consents[purpose_enum]
            consents.append({
                "purpose": c.purpose.value,
                "granted": c.granted,
                "policy_version": c.policy_version,
                "granted_at": c.granted_at.isoformat() if c.granted_at else None,
                "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
            })
        else:
            consents.append({
                "purpose": purpose_enum.value,
                "granted": default_val,
                "policy_version": "1.0.0",
                "granted_at": current_user.created_at.isoformat() if default_val else None,
                "withdrawn_at": None,
            })

    # Preferences
    prefs_res = await db.execute(select(UserPreferences).where(UserPreferences.user_id == current_user.id))
    prefs = prefs_res.scalar_one_or_none()

    # Analyses & signals
    analyses_res = await db.execute(
        select(MediaAnalysis)
        .options(selectinload(MediaAnalysis.signals))
        .where(MediaAnalysis.user_id == current_user.id, MediaAnalysis.deleted_at.is_(None))
        .order_by(desc(MediaAnalysis.created_at))
    )
    analyses = [
        {
            "id": a.id,
            "filename": a.original_filename,
            "media_type": a.media_type.value if hasattr(a.media_type, "value") else str(a.media_type),
            "file_size_bytes": a.file_size_bytes,
            "file_sha256": a.file_sha256,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "risk_level": a.risk_level.value if a.risk_level and hasattr(a.risk_level, "value") else str(a.risk_level) if a.risk_level else "UNDETERMINED",
            "synthetic_probability": a.synthetic_probability,
            "confidence": a.confidence,
            "prediction": a.prediction,
            "explanation": a.explanation,
            "limitations": a.limitations,
            "created_at": a.created_at.isoformat(),
            "signals": [
                {
                    "key": s.signal_key,
                    "label": s.signal_label,
                    "severity": s.severity,
                    "score": s.score,
                    "description": s.description,
                }
                for s in a.signals
            ],
        }
        for a in analyses_res.scalars().all()
    ]

    # Audit events
    audit_res = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .order_by(desc(AuditLog.created_at))
        .limit(100)
    )
    audit_events = [
        {
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "created_at": l.created_at.isoformat(),
        }
        for l in audit_res.scalars().all()
    ]

    # Record data export in audit trail
    db.add(AuditLog(
        user_id=current_user.id,
        action="USER_DATA_EXPORTED",
        resource_type="USER",
        resource_id=current_user.id,
        detail={"format": "json", "regulation": "GDPR_ARTICLE_20"},
    ))
    await db.commit()

    return {
        "export_metadata": {
            "platform": "Privacy Eye",
            "regulation": "GDPR Article 20 (Right to Data Portability)",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "export_version": "1.0.0",
        },
        "user_profile": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            "is_verified": current_user.is_verified,
            "registered_at": current_user.created_at.isoformat(),
        },
        "preferences": {
            "theme": prefs.theme if prefs else "dark",
            "language": prefs.language if prefs else "en",
            "privacy_mode": prefs.privacy_mode if prefs else True,
            "cloud_processing_enabled": prefs.cloud_processing_enabled if prefs else False,
        },
        "consents": consents,
        "analyses": analyses,
        "recent_audit_events": audit_events,
    }


@router.get("/me/audit-logs", response_model=UserAuditLogResponse)
async def get_user_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve user's personal security audit trail records (logins, consent toggles, scans).
    """
    stmt = select(AuditLog).where(AuditLog.user_id == current_user.id)
    if action:
        stmt = stmt.where(AuditLog.action == action.strip().upper())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * limit
    stmt = stmt.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)
    logs = (await db.execute(stmt)).scalars().all()

    return UserAuditLogResponse(
        items=[
            UserAuditLogItem(
                id=log.id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                detail=log.detail,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=total,
        page=page,
        limit=limit,
    )


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
