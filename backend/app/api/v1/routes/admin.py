"""
Privacy Eye — Production Administration & System Monitoring Engine
Restricted strictly to authenticated users with ADMIN role.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_

from app.database.session import get_db
from app.database.models import (
    User,
    MediaAnalysis,
    Report,
    UserSession,
    AuditLog,
    ModelVersion,
    UserRole,
    RiskLevel,
    MediaType,
    utcnow,
)
from app.schemas.schemas import (
    ModelVersionResponse,
    AdminStatsResponse,
    AdminUserResponse,
    AdminUserUpdateStatusRequest,
    AdminUserUpdateRoleRequest,
)
from app.core.security import get_current_user
from app.services.user_service import user_service
from app.services.ml_service import ml_service

router = APIRouter()


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Authorize access strictly for users with ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )
    return current_user


# ── System Statistics ─────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Comprehensive real-time platform statistics for the Admin Operations Center.
    Aggregates user counts, scan risk distributions, active sessions, and ML health.
    """
    now = datetime.now(timezone.utc)

    # User statistics
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar() or 0
    verified_users = (await db.execute(select(func.count(User.id)).where(User.is_verified == True))).scalar() or 0

    # Scan statistics
    total_scans = (await db.execute(select(func.count(MediaAnalysis.id)))).scalar() or 0

    # Risk level distribution
    risk_results = (
        await db.execute(
            select(MediaAnalysis.risk_level, func.count(MediaAnalysis.id)).group_by(MediaAnalysis.risk_level)
        )
    ).all()
    scans_by_risk: Dict[str, int] = {r.value: 0 for r in RiskLevel}
    for r_level, count in risk_results:
        if r_level:
            key = r_level.value if hasattr(r_level, "value") else str(r_level)
            scans_by_risk[key] = count

    # Media type distribution
    media_results = (
        await db.execute(
            select(MediaAnalysis.media_type, func.count(MediaAnalysis.id)).group_by(MediaAnalysis.media_type)
        )
    ).all()
    scans_by_media: Dict[str, int] = {m.value: 0 for m in MediaType}
    for m_type, count in media_results:
        if m_type:
            key = m_type.value if hasattr(m_type, "value") else str(m_type)
            scans_by_media[key] = count

    # Reports & active sessions
    total_reports = (await db.execute(select(func.count(Report.id)))).scalar() or 0
    active_sessions = (
        await db.execute(
            select(func.count(UserSession.id)).where(
                and_(UserSession.revoked_at.is_(None), UserSession.expires_at > now)
            )
        )
    ).scalar() or 0

    # ML & System Health
    ml_info = ml_service.get_model_info()
    system_status = {
        "database": "connected",
        "ml_pipeline": "operational",
        "active_models": ml_info.get("models_loaded", []),
        "fallback_mode": ml_info.get("mode") == "forensics_only",
    }

    return {
        "total_users": total_users,
        "active_users": active_users,
        "verified_users": verified_users,
        "total_scans": total_scans,
        "scans_by_risk": scans_by_risk,
        "scans_by_media": scans_by_media,
        "total_reports": total_reports,
        "active_sessions": active_sessions,
        "system_status": system_status,
    }


# ── User Management ──────────────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    q: Optional[str] = Query(None, description="Search by email or full name"),
    role: Optional[str] = Query(None, description="Filter by role (USER, ADMIN, ENTERPRISE)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter active/inactive"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Paginated user directory with search and filtering for administrator oversight.
    """
    stmt = select(User)
    conditions = []

    if q:
        q_clean = f"%{q.strip().lower()}%"
        conditions.append(or_(func.lower(User.email).like(q_clean), func.lower(User.full_name).like(q_clean)))

    if role:
        try:
            r_enum = UserRole(role.upper())
            conditions.append(User.role == r_enum)
        except ValueError:
            pass

    if status_filter == "active":
        conditions.append(User.is_active == True)
    elif status_filter == "inactive" or status_filter == "suspended":
        conditions.append(User.is_active == False)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    # Total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated results
    stmt = stmt.order_by(desc(User.created_at)).limit(limit).offset(offset)
    users_result = (await db.execute(stmt)).scalars().all()

    # Pre-calculate scan counts for listed users
    user_ids = [u.id for u in users_result]
    scan_counts_map: Dict[str, int] = {}
    if user_ids:
        scans_count_stmt = (
            select(MediaAnalysis.user_id, func.count(MediaAnalysis.id))
            .where(MediaAnalysis.user_id.in_(user_ids))
            .group_by(MediaAnalysis.user_id)
        )
        for uid, count in (await db.execute(scans_count_stmt)).all():
            scan_counts_map[uid] = count

    items = [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value if hasattr(u.role, "value") else str(u.role),
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "scans_used_this_month": u.scans_used_this_month,
            "scans_limit": u.scans_limit,
            "total_scans": scan_counts_map.get(u.id, 0),
            "created_at": u.created_at,
        }
        for u in users_result
    ]

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    body: AdminUserUpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Activate or suspend a user account.
    Self-suspension by the executing admin is strictly blocked.
    """
    if admin.id == user_id and not body.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot suspend their own account.",
        )

    user = await user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.is_active = body.is_active
    user.updated_at = datetime.now(timezone.utc)

    # If deactivating, terminate active sessions
    if not body.is_active:
        await user_service.revoke_all_sessions(db, user.id)

    db.add(AuditLog(
        user_id=admin.id,
        action="ADMIN_USER_STATUS_CHANGE",
        detail={"target_user_id": user_id, "target_email": user.email, "is_active": body.is_active},
    ))
    await db.commit()

    return {
        "success": True,
        "message": f"User account has been {'activated' if body.is_active else 'suspended'}.",
        "user_id": user_id,
        "is_active": user.is_active,
    }


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    body: AdminUserUpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Elevate or modify a user's role (USER, ADMIN, ENTERPRISE).
    Self-demotion is blocked to prevent accidental administrative lockout.
    """
    clean_role = body.role.strip().upper()
    try:
        new_role = UserRole(clean_role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{clean_role}'. Valid roles are: USER, ADMIN, ENTERPRISE.",
        )

    if admin.id == user_id and new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot demote themselves.",
        )

    user = await user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_role = user.role.value if hasattr(user.role, "value") else str(user.role)
    user.role = new_role
    user.updated_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        user_id=admin.id,
        action="ADMIN_USER_ROLE_CHANGE",
        detail={"target_user_id": user_id, "target_email": user.email, "old_role": old_role, "new_role": clean_role},
    ))
    await db.commit()

    return {
        "success": True,
        "message": f"User role updated to {clean_role}.",
        "user_id": user_id,
        "role": clean_role,
    }


# ── Global Scans Audit Feed ───────────────────────────────────────────────────

@router.get("/scans")
async def list_global_scans(
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    media_type: Optional[str] = Query(None, description="Filter by media type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Audit recent deepfake detection scans across the entire platform.
    """
    stmt = (
        select(MediaAnalysis, User.email.label("user_email"))
        .outerjoin(User, MediaAnalysis.user_id == User.id)
    )
    conditions = []

    if risk_level:
        try:
            r_enum = RiskLevel(risk_level.upper())
            conditions.append(MediaAnalysis.risk_level == r_enum)
        except ValueError:
            pass

    if media_type:
        try:
            m_enum = MediaType(media_type.upper())
            conditions.append(MediaAnalysis.media_type == m_enum)
        except ValueError:
            pass

    if conditions:
        stmt = stmt.where(and_(*conditions))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(desc(MediaAnalysis.created_at)).limit(limit).offset(offset)
    results = (await db.execute(stmt)).all()

    items = []
    for analysis, user_email in results:
        items.append({
            "id": analysis.id,
            "user_id": analysis.user_id,
            "user_email": user_email or "Anonymous/System",
            "original_filename": analysis.original_filename,
            "media_type": analysis.media_type.value if hasattr(analysis.media_type, "value") else str(analysis.media_type),
            "file_size_bytes": analysis.file_size_bytes,
            "status": analysis.status.value if hasattr(analysis.status, "value") else str(analysis.status),
            "risk_level": analysis.risk_level.value if hasattr(analysis.risk_level, "value") else str(analysis.risk_level) if analysis.risk_level else "UNDETERMINED",
            "synthetic_probability": analysis.synthetic_probability,
            "confidence": analysis.confidence,
            "created_at": analysis.created_at,
        })

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── Audit Logs Stream ─────────────────────────────────────────────────────────

@router.get("/audit-logs")
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action code"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Retrieve immutable security audit trail records for compliance and threat analysis.
    """
    stmt = (
        select(AuditLog, User.email.label("user_email"))
        .outerjoin(User, AuditLog.user_id == User.id)
    )
    if action:
        stmt = stmt.where(AuditLog.action == action.strip().upper())

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
    results = (await db.execute(stmt)).all()

    items = [
        {
            "id": log.id,
            "user_id": log.user_id,
            "user_email": user_email or "System / Anonymous",
            "action": log.action,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "detail": log.detail,
            "created_at": log.created_at,
        }
        for log, user_email in results
    ]

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── Model Registry & Legacy Endpoints ─────────────────────────────────────────

@router.get("/models", response_model=List[ModelVersionResponse])
async def list_models(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List all registered ML model versions."""
    result = await db.execute(select(ModelVersion).order_by(desc(ModelVersion.created_at)))
    return result.scalars().all()


@router.get("/model/current")
async def current_model_version():
    """Get currently active model version info (public endpoint for auditability)."""
    return ml_service.get_model_info()

