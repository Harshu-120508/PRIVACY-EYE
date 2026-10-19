"""
Privacy Eye — Database Models (SQLAlchemy ORM)

Tables:
  users                  User accounts
  api_keys               Developer API keys
  media_analysis         Each scan record
  analysis_signals       Detected signals per analysis
  model_versions         ML model registry
  reports                Generated evidence reports
  audit_logs             Immutable audit trail
"""
import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Boolean, DateTime, Float, Integer, Text,
    ForeignKey, Enum as SAEnum, JSON, Index, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


# ── Enums ────────────────────────────────────────────────────────────────────

class MediaType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNDETERMINED = "UNDETERMINED"


class AnalysisStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"


class ConsentPurpose(str, enum.Enum):
    MEDIA_PROCESSING = "MEDIA_PROCESSING"        # Necessary for detection
    SAVE_HISTORY = "SAVE_HISTORY"                # Optional
    RETAIN_MEDIA = "RETAIN_MEDIA"                # Optional (default False)
    EXTERNAL_AI_SHARING = "EXTERNAL_AI_SHARING"  # Optional (default False)
    MODEL_TRAINING = "MODEL_TRAINING"            # Optional (default False)
    ANALYTICS = "ANALYTICS"                      # Optional (default False)


class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    ENTERPRISE = "ENTERPRISE"


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    scans_used_this_month: Mapped[int] = mapped_column(Integer, default=0)
    scans_limit: Mapped[int] = mapped_column(Integer, default=20)  # free tier
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    analyses: Mapped[List["MediaAnalysis"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    api_keys: Mapped[List["ApiKey"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[List["Report"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    preferences: Mapped[Optional["UserPreferences"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    consents: Mapped[List["UserConsent"]] = relationship(back_populates="user", cascade="all, delete-orphan")


# ── Sessions ──────────────────────────────────────────────────────────────────

class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    is_remember_me: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions")


# ── User Preferences ──────────────────────────────────────────────────────────

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    language: Mapped[str] = mapped_column(String(10), default="en")
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    privacy_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    cloud_processing_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="preferences")


# ── Granular User Consents ───────────────────────────────────────────────────

class UserConsent(Base):
    __tablename__ = "user_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose: Mapped[ConsentPurpose] = mapped_column(SAEnum(ConsentPurpose), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="consents")

    __table_args__ = (
        UniqueConstraint("user_id", "purpose", name="uq_user_consent_purpose"),
        Index("ix_user_consents_user_purpose", "user_id", "purpose"),
    )


# ── Password Reset Tokens ─────────────────────────────────────────────────────

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship()


# ── API Keys ─────────────────────────────────────────────────────────────────

class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # hashed, never stored plain
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="api_keys")


# ── Model Versions ────────────────────────────────────────────────────────────

class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "image", "video", "audio"
    description: Mapped[Optional[str]] = mapped_column(Text)
    accuracy: Mapped[Optional[float]] = mapped_column(Float)
    precision: Mapped[Optional[float]] = mapped_column(Float)
    recall: Mapped[Optional[float]] = mapped_column(Float)
    f1_score: Mapped[Optional[float]] = mapped_column(Float)
    roc_auc: Mapped[Optional[float]] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (UniqueConstraint("name", "version", name="uq_model_name_version"),)


# ── Media Analysis ────────────────────────────────────────────────────────────

class MediaAnalysis(Base):
    __tablename__ = "media_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # File metadata (NOT the file itself)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    media_type: Mapped[MediaType] = mapped_column(SAEnum(MediaType), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_sha256: Mapped[Optional[str]] = mapped_column(String(64))  # SHA-256 of content
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)  # For video/audio

    # Analysis status
    status: Mapped[AnalysisStatus] = mapped_column(SAEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_ms: Mapped[Optional[int]] = mapped_column(Integer)

    # Detection results
    risk_level: Mapped[Optional[RiskLevel]] = mapped_column(SAEnum(RiskLevel))
    synthetic_probability: Mapped[Optional[float]] = mapped_column(Float)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    model_version_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("model_versions.id"))

    # Model and inference transparency
    model_id: Mapped[Optional[str]] = mapped_column(String(100))
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    prediction: Mapped[Optional[str]] = mapped_column(String(50))
    limitations: Mapped[Optional[str]] = mapped_column(Text)
    error_code: Mapped[Optional[str]] = mapped_column(String(50))

    # Explainability
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    raw_scores: Mapped[Optional[dict]] = mapped_column(JSON)  # Raw per-model scores
    provenance_info: Mapped[Optional[dict]] = mapped_column(JSON)  # C2PA / metadata

    # Privacy: temp file was deleted?
    media_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="analyses")
    signals: Mapped[List["AnalysisSignal"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    report: Mapped[Optional["Report"]] = relationship(back_populates="analysis", uselist=False)

    __table_args__ = (
        Index("ix_media_analysis_user_created", "user_id", "created_at"),
        Index("ix_media_analysis_risk", "risk_level"),
    )


# ── Analysis Signals ──────────────────────────────────────────────────────────

class AnalysisSignal(Base):
    __tablename__ = "analysis_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("media_analysis.id", ondelete="CASCADE"), nullable=False
    )
    signal_key: Mapped[str] = mapped_column(String(100), nullable=False)
    signal_label: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # "low", "medium", "high"
    score: Mapped[Optional[float]] = mapped_column(Float)
    description: Mapped[Optional[str]] = mapped_column(Text)

    analysis: Mapped["MediaAnalysis"] = relationship(back_populates="signals")


# ── Reports ───────────────────────────────────────────────────────────────────

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("media_analysis.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    recommendations: Mapped[Optional[str]] = mapped_column(Text)
    report_json: Mapped[Optional[dict]] = mapped_column(JSON)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to generated PDF
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="reports")
    analysis: Mapped["MediaAnalysis"] = relationship(back_populates="report")


# ── Audit Logs ────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50))
    resource_id: Mapped[Optional[str]] = mapped_column(String(36))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    detail: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (Index("ix_audit_logs_user_action", "user_id", "action"),)


# ── Face Training Samples (Consent-Based Model Database) ──────────────────────

class FaceTrainingSample(Base):
    __tablename__ = "face_training_samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False)
    category_label: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(500))  # Saved only if consent_given is True
    landmarks_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ── Dataset Governance & Lineage ─────────────────────────────────────────────

class DatasetRecord(Base):
    __tablename__ = "dataset_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    sample_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # CATEGORY_A_GENUINE, etc.
    source_dataset: Mapped[str] = mapped_column(String(100), nullable=False)        # "InternalConsented", "FaceForensics++"
    license_terms: Mapped[str] = mapped_column(String(100), nullable=False)         # "CC-BY-4.0", "InternalConsent"
    subject_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)      # For subject-disjoint splits
    video_id: Mapped[Optional[str]] = mapped_column(String(100))
    generator_family: Mapped[Optional[str]] = mapped_column(String(50))             # "stylegan2", "sdxl", etc.
    manipulation_type: Mapped[Optional[str]] = mapped_column(String(50))            # "faceswap", "replay", etc.
    device_class: Mapped[Optional[str]] = mapped_column(String(50))
    environment_type: Mapped[Optional[str]] = mapped_column(String(50))
    resolution: Mapped[Optional[str]] = mapped_column(String(20))
    fps: Mapped[Optional[int]] = mapped_column(Integer, default=30)
    true_label: Mapped[str] = mapped_column(String(50), nullable=False)             # "real", "fake", "replay"
    split: Mapped[str] = mapped_column(String(50), default="train", index=True)     # "train", "val", "test_unseen_subject"
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    sha256_checksum: Mapped[Optional[str]] = mapped_column(String(64))
    consent_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_dataset_category_split", "category", "split"),
    )


# ── Failure Cases (Hard Negative Mining) ─────────────────────────────────────

class FailureCase(Base):
    __tablename__ = "failure_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    failure_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    input_type: Mapped[str] = mapped_column(String(50), nullable=False)
    device: Mapped[Optional[str]] = mapped_column(String(50))
    resolution: Mapped[Optional[str]] = mapped_column(String(20))
    environment: Mapped[Optional[str]] = mapped_column(String(50))
    true_label: Mapped[str] = mapped_column(String(50), nullable=False)
    prediction: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_verified_by_human: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100))
    added_to_training_set: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ── Model Registry & Governance ──────────────────────────────────────────────

class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    model_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="EXPERIMENTAL")  # EXPERIMENTAL, VALIDATION, STAGING, PRODUCTION, DEPRECATED
    license: Mapped[str] = mapped_column(String(100), nullable=False)
    weights_license: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    ece_score: Mapped[Optional[float]] = mapped_column(Float)
    brier_score: Mapped[Optional[float]] = mapped_column(Float)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100))
    metrics_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ── Live Camera Sessions ─────────────────────────────────────────────────────

class LiveSession(Base):
    __tablename__ = "live_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    device_info: Mapped[Optional[str]] = mapped_column(String(200))
    stream_fps: Mapped[Optional[float]] = mapped_column(Float)
    resolution: Mapped[Optional[str]] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    total_frames_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[Optional[float]] = mapped_column(Float)
