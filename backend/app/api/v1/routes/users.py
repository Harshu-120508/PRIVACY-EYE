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
    ConsentActionRequest,
    ConsentLedgerItem,
    UserConsentHistoryResponse,
    ConsentPurposeEnum,
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
    Extracts the latest state from the append-only ledger.
    """
    from app.database.models import UserConsent, ConsentPurpose
    from sqlalchemy import select

    result = await db.execute(
        select(UserConsent)
        .where(UserConsent.user_id == current_user.id)
        .order_by(UserConsent.timestamp.desc(), UserConsent.created_at.desc())
    )
    all_consents = result.scalars().all()
    latest_by_purpose = {}
    for c in all_consents:
        if c.purpose not in latest_by_purpose:
            latest_by_purpose[c.purpose] = c

    defaults = [
        (ConsentPurpose.MEDIA_PROCESSING, True),  # Inherent to contracted detection service
        (ConsentPurpose.SAVE_HISTORY, True),       # Default enabled for user audit log
        (ConsentPurpose.RETAIN_MEDIA, False),      # Disabled by default
        (ConsentPurpose.EXTERNAL_AI_SHARING, False),# Disabled by default
        (ConsentPurpose.MODEL_TRAINING, False),    # Opt-in only
        (ConsentPurpose.ANALYTICS, False),         # Optional
    ]

    items = []
    for purpose, default_val in defaults:
        if purpose in latest_by_purpose:
            c = latest_by_purpose[purpose]
            is_granted = c.granted and c.status == "granted"
            items.append(ConsentItem(
                purpose=purpose.value,
                status=c.status,
                granted=is_granted,
                policy_version=c.policy_version,
                timestamp=c.timestamp,
                method=c.method,
                granted_at=c.granted_at,
                withdrawn_at=c.withdrawn_at,
            ))
        else:
            items.append(ConsentItem(
                purpose=purpose.value,
                status="granted" if default_val else "withdrawn",
                granted=default_val,
                policy_version="1.0.0",
                timestamp=current_user.created_at,
                method="DEFAULT",
                granted_at=current_user.created_at if default_val else None,
                withdrawn_at=None if default_val else current_user.created_at,
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
    Append-only ledger update: records a new consent state in the ledger.
    Applies immediately to all future processing.
    """
    from app.database.models import UserConsent, ConsentPurpose
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    purpose_enum = ConsentPurpose(body.purpose.value)
    status_str = "granted" if body.granted else "withdrawn"

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")[:500]

    consent_record = UserConsent(
        user_id=current_user.id,
        purpose=purpose_enum,
        status=status_str,
        granted=body.granted,
        policy_version=body.policy_version,
        timestamp=now,
        method="UI",
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
        detail={"purpose": body.purpose.value, "status": status_str, "granted": body.granted, "policy_version": body.policy_version, "method": "UI"},
        ip_address=ip,
    ))
    await db.commit()

    logger.info("User consent decision recorded in append-only ledger", user_id=current_user.id, purpose=body.purpose.value, status=status_str)
    return await get_user_consents(db=db, current_user=current_user)


@router.post("/me/consents/grant", response_model=UserConsentListResponse)
async def grant_user_consent(
    body: ConsentActionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Explicitly grant consent for a single purpose and append to immutable ledger (GDPR Art. 7(1)).
    """
    from app.database.models import UserConsent, ConsentPurpose
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    purpose_enum = ConsentPurpose(body.purpose.value)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")[:500]

    record = UserConsent(
        user_id=current_user.id,
        purpose=purpose_enum,
        status="granted",
        granted=True,
        policy_version=body.policy_version,
        timestamp=now,
        method=body.method,
        granted_at=now,
        withdrawn_at=None,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(record)
    db.add(AuditLog(
        user_id=current_user.id,
        action="CONSENT_GRANTED",
        resource_type="CONSENT",
        resource_id=record.id,
        detail={"purpose": body.purpose.value, "status": "granted", "policy_version": body.policy_version, "method": body.method},
        ip_address=ip,
    ))
    await db.commit()
    logger.info("Consent explicitly granted", user_id=current_user.id, purpose=body.purpose.value, method=body.method)
    return await get_user_consents(db=db, current_user=current_user)


@router.post("/me/consents/withdraw", response_model=UserConsentListResponse)
async def withdraw_user_consent(
    body: ConsentActionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Withdraw consent for a single purpose as easily as granting (GDPR Art. 7(3)) and append to ledger.
    """
    from app.database.models import UserConsent, ConsentPurpose
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    purpose_enum = ConsentPurpose(body.purpose.value)
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")[:500]

    record = UserConsent(
        user_id=current_user.id,
        purpose=purpose_enum,
        status="withdrawn",
        granted=False,
        policy_version=body.policy_version,
        timestamp=now,
        method=body.method,
        granted_at=None,
        withdrawn_at=now,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(record)
    db.add(AuditLog(
        user_id=current_user.id,
        action="CONSENT_WITHDRAWN",
        resource_type="CONSENT",
        resource_id=record.id,
        detail={"purpose": body.purpose.value, "status": "withdrawn", "policy_version": body.policy_version, "method": body.method},
        ip_address=ip,
    ))
    await db.commit()
    logger.info("Consent explicitly withdrawn", user_id=current_user.id, purpose=body.purpose.value, method=body.method)
    return await get_user_consents(db=db, current_user=current_user)


@router.get("/me/consents/history", response_model=UserConsentHistoryResponse)
async def get_user_consent_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve full demonstrable append-only audit trail of all consent grants and withdrawals (GDPR Art. 7(1)).
    """
    from app.database.models import UserConsent
    from sqlalchemy import select

    stmt = (
        select(UserConsent)
        .where(UserConsent.user_id == current_user.id)
        .order_by(UserConsent.timestamp.desc(), UserConsent.created_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = [
        ConsentLedgerItem(
            id=r.id,
            purpose=r.purpose.value,
            status=r.status,
            granted=r.granted,
            policy_version=r.policy_version,
            timestamp=r.timestamp,
            method=r.method,
            ip_address=r.ip_address,
            user_agent=r.user_agent,
            created_at=r.created_at,
        )
        for r in records
    ]
    return UserConsentHistoryResponse(history=items, total=len(items))


@router.get("/me/consents/verify/{purpose}")
async def verify_consent_gate(
    purpose: ConsentPurposeEnum,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verification route demonstrating require_consent dependency enforcement.
    Blocks with 403 Forbidden if consent is absent or withdrawn.
    """
    from app.core.security import require_consent
    gate = require_consent(purpose.value)
    consent = await gate(db=db, current_user=current_user)
    return {
        "purpose": consent.purpose.value,
        "status": consent.status,
        "granted": consent.granted,
        "timestamp": consent.timestamp.isoformat() if consent.timestamp else None,
        "policy_version": consent.policy_version,
        "method": consent.method,
    }
