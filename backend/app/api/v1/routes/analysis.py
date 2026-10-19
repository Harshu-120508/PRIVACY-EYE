"""
Media analysis routes — the core of Privacy Eye.

POST /analyze/image   — Upload and analyze an image
POST /analyze/video   — Upload and analyze a video
POST /analyze/audio   — Upload and analyze audio
GET  /analyze/{id}    — Get analysis result
GET  /analyze/history — Paginated analysis history
DELETE /analyze/{id}  — Delete an analysis record
GET  /analyze/stats   — Dashboard statistics
"""
import os
import hashlib
import aiofiles
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.database.models import (
    MediaAnalysis,
    AnalysisSignal,
    MediaType,
    AnalysisStatus,
    RiskLevel,
    AuditLog,
    UserConsent,
    ConsentPurpose,
)
from app.schemas.schemas import AnalysisResponse, AnalysisListResponse, DashboardStats
from app.core.security import get_current_user
from app.core.config import settings
from app.services.ml_service import ml_service
from app.services.file_service import file_service
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)

# Allowed MIME types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/avi"}
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/ogg", "audio/flac"}


async def _validate_upload(file: UploadFile, allowed_types: set, max_bytes: int) -> bytes:
    """Validate file type and size, return raw bytes."""
    content_type = file.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{content_type}'. Allowed: {sorted(allowed_types)}",
        )
    content = await file.read()
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed: {max_bytes // (1024*1024)} MB",
        )
    return content


async def _check_user_consent(db: AsyncSession, user_id: str, purpose: ConsentPurpose, default: bool = True) -> bool:
    """Server-side verification of granular user consent."""
    res = await db.execute(
        select(UserConsent).where(UserConsent.user_id == user_id, UserConsent.purpose == purpose)
    )
    rec = res.scalar_one_or_none()
    if rec is not None:
        return rec.granted
    return default


async def _create_analysis_record(
    db: AsyncSession,
    user_id: str,
    filename: str,
    media_type: MediaType,
    file_bytes: bytes,
    mime_type: str,
) -> MediaAnalysis:
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    analysis = MediaAnalysis(
        id=str(uuid.uuid4()),
        user_id=user_id,
        original_filename=filename[:500],
        media_type=media_type,
        file_size_bytes=len(file_bytes),
        file_sha256=sha256,
        mime_type=mime_type,
        status=AnalysisStatus.PROCESSING,
        processing_started_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    await db.flush()
    return analysis


async def _run_and_save_analysis(
    db: AsyncSession,
    analysis: MediaAnalysis,
    file_bytes: bytes,
    media_type_str: str,
):
    """Run ML pipeline and persist results."""
    start = datetime.now(timezone.utc)
    try:
        result = await ml_service.analyze(file_bytes, media_type_str, analysis.original_filename)

        analysis.status = AnalysisStatus.COMPLETE
        analysis.risk_level = RiskLevel(result["risk_level"])
        analysis.synthetic_probability = result["synthetic_probability"]
        analysis.confidence = result["confidence"]
        analysis.model_id = result.get("model_id")
        analysis.model_version = result.get("model_version")
        analysis.prediction = result.get("prediction")
        analysis.limitations = result.get("limitations")
        analysis.error_code = None
        analysis.explanation = result["explanation"]
        analysis.raw_scores = result.get("raw_scores", {})
        analysis.provenance_info = result.get("provenance", {})
        analysis.media_deleted = True  # We never persist raw media

        end = datetime.now(timezone.utc)
        analysis.processing_finished_at = end
        analysis.processing_ms = int((end - start).total_seconds() * 1000)

        # Persist signals
        for sig in result.get("signals", []):
            db.add(AnalysisSignal(
                id=str(uuid.uuid4()),
                analysis_id=analysis.id,
                signal_key=sig["key"],
                signal_label=sig["label"],
                severity=sig["severity"],
                score=sig.get("score"),
                description=sig.get("description"),
            ))

    except Exception as e:
        logger.error("ML analysis failed", analysis_id=analysis.id, error=str(e))
        analysis.status = AnalysisStatus.FAILED
        analysis.error_code = "ERR_INFERENCE_FAILURE"
        analysis.limitations = "Inference could not be completed due to internal pipeline exception."
        analysis.explanation = f"Analysis failed: {str(e)[:200]}"

    await db.flush()


@router.post("/image", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_image(
    file: UploadFile = File(..., description="Image file (JPEG, PNG, WEBP)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload and analyze an image for deepfake / AI-generation indicators."""
    can_process = await _check_user_consent(db, current_user.id, ConsentPurpose.MEDIA_PROCESSING, default=True)
    if not can_process:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Media processing consent is currently withdrawn. Enable detection processing in the Privacy Center to analyze media.",
        )

    if current_user.scans_used_this_month >= current_user.scans_limit:
        raise HTTPException(status_code=429, detail="Monthly scan limit reached. Upgrade to continue.")

    content = await _validate_upload(file, ALLOWED_IMAGE_TYPES, settings.max_image_bytes)
    analysis = await _create_analysis_record(db, current_user.id, file.filename or "image", MediaType.IMAGE, content, file.content_type or "")
    await _run_and_save_analysis(db, analysis, content, "image")

    # Enforce history consent
    save_history = await _check_user_consent(db, current_user.id, ConsentPurpose.SAVE_HISTORY, default=True)
    if not save_history:
        analysis.deleted_at = datetime.now(timezone.utc)

    # Increment scan counter
    current_user.scans_used_this_month += 1
    db.add(AuditLog(user_id=current_user.id, action="SCAN_IMAGE", resource_id=analysis.id))
    await db.commit()

    loaded = await db.execute(
        select(MediaAnalysis).options(selectinload(MediaAnalysis.signals)).where(MediaAnalysis.id == analysis.id)
    )
    return loaded.scalar_one()


@router.post("/video", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_video(
    file: UploadFile = File(..., description="Video file (MP4, MOV, WEBM)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload and analyze a video for temporal deepfake and face-swap indicators."""
    can_process = await _check_user_consent(db, current_user.id, ConsentPurpose.MEDIA_PROCESSING, default=True)
    if not can_process:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Media processing consent is currently withdrawn. Enable detection processing in the Privacy Center to analyze media.",
        )

    if current_user.scans_used_this_month >= current_user.scans_limit:
        raise HTTPException(status_code=429, detail="Monthly scan limit reached.")

    content = await _validate_upload(file, ALLOWED_VIDEO_TYPES, settings.max_video_bytes)
    analysis = await _create_analysis_record(db, current_user.id, file.filename or "video", MediaType.VIDEO, content, file.content_type or "")
    await _run_and_save_analysis(db, analysis, content, "video")

    save_history = await _check_user_consent(db, current_user.id, ConsentPurpose.SAVE_HISTORY, default=True)
    if not save_history:
        analysis.deleted_at = datetime.now(timezone.utc)

    current_user.scans_used_this_month += 1
    db.add(AuditLog(user_id=current_user.id, action="SCAN_VIDEO", resource_id=analysis.id))
    await db.commit()

    loaded = await db.execute(
        select(MediaAnalysis).options(selectinload(MediaAnalysis.signals)).where(MediaAnalysis.id == analysis.id)
    )
    return loaded.scalar_one()


@router.post("/audio", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_audio(
    file: UploadFile = File(..., description="Audio file (MP3, WAV, OGG, FLAC)"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload and analyze audio for voice-cloning and synthetic speech indicators."""
    can_process = await _check_user_consent(db, current_user.id, ConsentPurpose.MEDIA_PROCESSING, default=True)
    if not can_process:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Media processing consent is currently withdrawn. Enable detection processing in the Privacy Center to analyze media.",
        )

    if current_user.scans_used_this_month >= current_user.scans_limit:
        raise HTTPException(status_code=429, detail="Monthly scan limit reached.")

    content = await _validate_upload(file, ALLOWED_AUDIO_TYPES, settings.max_audio_bytes)
    analysis = await _create_analysis_record(db, current_user.id, file.filename or "audio", MediaType.AUDIO, content, file.content_type or "")
    await _run_and_save_analysis(db, analysis, content, "audio")

    save_history = await _check_user_consent(db, current_user.id, ConsentPurpose.SAVE_HISTORY, default=True)
    if not save_history:
        analysis.deleted_at = datetime.now(timezone.utc)

    current_user.scans_used_this_month += 1
    db.add(AuditLog(user_id=current_user.id, action="SCAN_AUDIO", resource_id=analysis.id))
    await db.commit()

    loaded = await db.execute(
        select(MediaAnalysis).options(selectinload(MediaAnalysis.signals)).where(MediaAnalysis.id == analysis.id)
    )
    return loaded.scalar_one()


@router.get("/history", response_model=AnalysisListResponse)
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    media_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieve paginated analysis history for the current user."""
    filters = [MediaAnalysis.user_id == current_user.id, MediaAnalysis.deleted_at.is_(None)]
    if media_type:
        filters.append(MediaAnalysis.media_type == media_type.upper())

    count_q = await db.execute(select(func.count()).select_from(MediaAnalysis).where(and_(*filters)))
    total = count_q.scalar() or 0

    q = (
        select(MediaAnalysis)
        .options(selectinload(MediaAnalysis.signals))
        .where(and_(*filters))
        .order_by(MediaAnalysis.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    items = result.scalars().all()

    return AnalysisListResponse(items=list(items), total=total, page=page, per_page=per_page)


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get dashboard statistics for the current user."""
    base = and_(MediaAnalysis.user_id == current_user.id, MediaAnalysis.deleted_at.is_(None))

    async def count(extra=None):
        q = select(func.count()).select_from(MediaAnalysis).where(base if extra is None else and_(base, extra))
        r = await db.execute(q)
        return r.scalar() or 0

    total = await count()
    suspicious = await count(MediaAnalysis.risk_level == RiskLevel.SUSPICIOUS)
    low_risk = await count(MediaAnalysis.risk_level == RiskLevel.LOW)
    high_risk = await count(MediaAnalysis.risk_level == RiskLevel.HIGH)
    critical = await count(MediaAnalysis.risk_level == RiskLevel.CRITICAL)
    undetermined = await count(MediaAnalysis.risk_level == RiskLevel.UNDETERMINED)

    return DashboardStats(
        total_scanned=total,
        suspicious=suspicious,
        low_risk=low_risk,
        high_risk=high_risk,
        critical=critical,
        undetermined=undetermined,
        scans_this_month=current_user.scans_used_this_month,
        scans_limit=current_user.scans_limit,
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(MediaAnalysis)
        .options(selectinload(MediaAnalysis.signals))
        .where(
            MediaAnalysis.id == analysis_id,
            MediaAnalysis.user_id == current_user.id,
            MediaAnalysis.deleted_at.is_(None),
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(MediaAnalysis).where(
            MediaAnalysis.id == analysis_id,
            MediaAnalysis.user_id == current_user.id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    analysis.deleted_at = datetime.now(timezone.utc)
    db.add(AuditLog(user_id=current_user.id, action="DELETE_ANALYSIS", resource_id=analysis_id))
    await db.commit()
