"""
Privacy Eye — Dataset Management, Quality Gate, and Failure Mining API Endpoints
Asynchronous SQLAlchemy 2.0 implementation.
"""

import base64
from typing import List, Optional
import numpy as np
import cv2
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.database.models import DatasetRecord, FailureCase, ModelRegistry, User
from app.core.security import get_current_user, require_admin
from app.schemas.schemas import (
    DatasetRecordCreate,
    DatasetRecordResponse,
    QualityGateRequest,
    QualityGateResponse,
    FailureCaseCreate,
    FailureCaseResponse,
    ModelRegistryResponse,
    DatasetSummaryStats,
)
from app.dataset.quality_gate import QualityGate
from app.dataset.failure_mining import FailureCaseManager

router = APIRouter(prefix="/dataset", tags=["Dataset & Governance"])
_quality_gate = QualityGate()
_failure_manager = FailureCaseManager()


# ── Dataset Records & Provenance ─────────────────────────────────────────────

@router.post("/records", response_model=DatasetRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset_record(
    record: DatasetRecordCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Registers a sample into the dataset system with full provenance and licensing verification (Admin only)."""
    result = await db.execute(select(DatasetRecord).where(DatasetRecord.sample_id == record.sample_id))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Dataset record with sample_id '{record.sample_id}' already exists."
        )

    db_rec = DatasetRecord(
        sample_id=record.sample_id,
        category=record.category,
        source_dataset=record.source_dataset,
        license_terms=record.license_terms,
        subject_id=record.subject_id,
        video_id=record.video_id,
        generator_family=record.generator_family,
        manipulation_type=record.manipulation_type,
        device_class=record.device_class,
        environment_type=record.environment_type,
        resolution=record.resolution,
        fps=record.fps,
        true_label=record.true_label,
        split=record.split,
        file_path=record.file_path,
        sha256_checksum=record.sha256_checksum,
        consent_verified=record.consent_verified,
        metadata_json=record.metadata_json,
    )
    db.add(db_rec)
    await db.flush()
    await db.refresh(db_rec)
    return db_rec


@router.get("/records", response_model=List[DatasetRecordResponse])
async def list_dataset_records(
    category: Optional[str] = None,
    split: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queries dataset records filtered by category (A-E) and split."""
    stmt = select(DatasetRecord)
    if category:
        stmt = stmt.where(DatasetRecord.category == category)
    if split:
        stmt = stmt.where(DatasetRecord.split == split)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/stats", response_model=DatasetSummaryStats)
async def get_dataset_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Computes distribution metrics across Categories A-E, splits, and consent compliance."""
    total_res = await db.execute(select(func.count(DatasetRecord.id)))
    total = total_res.scalar() or 0

    category_counts = {}
    cat_res = await db.execute(select(DatasetRecord.category, func.count(DatasetRecord.id)).group_by(DatasetRecord.category))
    for cat, count in cat_res.all():
        category_counts[cat] = count

    split_counts = {}
    split_res = await db.execute(select(DatasetRecord.split, func.count(DatasetRecord.id)).group_by(DatasetRecord.split))
    for sp, count in split_res.all():
        split_counts[sp] = count

    consented_res = await db.execute(select(func.count(DatasetRecord.id)).where(DatasetRecord.consent_verified == True))
    consented = consented_res.scalar() or 0
    compliance_pct = (consented / total * 100.0) if total > 0 else 100.0

    return DatasetSummaryStats(
        total_samples=total,
        category_counts=category_counts,
        split_counts=split_counts,
        consent_compliance_pct=round(compliance_pct, 1),
    )


# ── Quality Gate ─────────────────────────────────────────────────────────────

@router.post("/quality-gate", response_model=QualityGateResponse)
def evaluate_quality_gate(
    payload: QualityGateRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Evaluates input optical, exposure, blur, and resolution quality before heavy inference.
    Rejects degraded inputs with recommended user guidance.
    """
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Decoded image is empty or invalid format.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid image format: {str(e)}"
        )

    res = _quality_gate.evaluate_face_crop(img)
    return QualityGateResponse(
        passed=res.passed,
        overall_quality_score=res.overall_quality_score,
        quality_label=res.quality_label,
        sharpness_score=res.sharpness_score,
        mean_luminance=res.mean_luminance,
        overexposed_ratio=res.overexposed_ratio,
        underexposed_ratio=res.underexposed_ratio,
        face_resolution=list(res.face_resolution),
        motion_blur_detected=res.motion_blur_detected,
        rejection_reasons=res.rejection_reasons,
        recommended_guidance=res.recommended_guidance,
    )


# ── Failure Cases & Hard-Negative Mining ─────────────────────────────────────

@router.post("/failure-cases", response_model=FailureCaseResponse, status_code=status.HTTP_201_CREATED)
async def log_failure_case(
    payload: FailureCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logs an authenticated model failure for investigation and hard-negative mining."""
    rec = _failure_manager.log_failure(
        model_version=payload.model_version,
        input_type=payload.input_type,
        device=payload.device or "laptop_webcam_720p",
        resolution=payload.resolution or "720p",
        environment=payload.environment or "indoor_bright",
        true_label=payload.true_label,
        prediction=payload.prediction,
        confidence=payload.confidence,
        reason=payload.reason,
    )

    db_rec = FailureCase(
        failure_id=rec.failure_id,
        model_version=rec.model_version,
        input_type=rec.input_type,
        device=rec.device,
        resolution=rec.resolution,
        environment=rec.environment,
        true_label=rec.true_label,
        prediction=rec.prediction,
        confidence=rec.confidence,
        reason=rec.reason,
        is_verified_by_human=rec.is_verified_by_human,
        reviewed_by=rec.reviewed_by,
        added_to_training_set=rec.added_to_training_set,
    )
    db.add(db_rec)
    await db.flush()
    await db.refresh(db_rec)
    return db_rec


@router.get("/failure-cases", response_model=List[FailureCaseResponse])
async def list_failure_cases(
    high_confidence_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Queries logged failure cases, highlighting high-confidence mistakes (Admin only)."""
    stmt = select(FailureCase)
    if high_confidence_only:
        stmt = stmt.where(FailureCase.confidence >= 0.75)
    stmt = stmt.order_by(FailureCase.confidence.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/failure-cases/{failure_id}/review", response_model=FailureCaseResponse)
async def review_failure_case(
    failure_id: str,
    approve_for_retraining: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Human-in-the-loop review approval before promotion to dataset (Admin only)."""
    result = await db.execute(select(FailureCase).where(FailureCase.failure_id == failure_id))
    db_rec = result.scalars().first()
    if not db_rec:
        raise HTTPException(status_code=404, detail="Failure case not found")

    reviewer_id = admin.id
    db_rec.is_verified_by_human = True
    db_rec.reviewed_by = reviewer_id
    db_rec.added_to_training_set = approve_for_retraining
    await db.flush()
    await db.refresh(db_rec)

    _failure_manager.review_and_approve(failure_id, reviewer_id, approve_for_retraining)
    return db_rec
