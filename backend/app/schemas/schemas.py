"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: Optional[str] = None
    full_name: Optional[str] = Field(None, max_length=200)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserPreferencesResponse(BaseModel):
    theme: str = "dark"
    language: str = "en"
    notifications_enabled: bool = True
    privacy_mode: bool = True
    cloud_processing_enabled: bool = False

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_verified: bool
    scans_used_this_month: int
    scans_limit: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthSuccessResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: Optional[str] = None


class DeleteAccountRequest(BaseModel):
    password_confirmation: str


class SessionResponse(BaseModel):
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_current: bool = False
    is_remember_me: bool = False
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class VerifyEmailRequest(BaseModel):
    token: str


class RequestEmailVerificationRequest(BaseModel):
    email: Optional[EmailStr] = None


class AdminUserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    scans_used_this_month: int
    scans_limit: int
    total_scans: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUserUpdateStatusRequest(BaseModel):
    is_active: bool


class AdminUserUpdateRoleRequest(BaseModel):
    role: str


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    total_scans: int
    scans_by_risk: Dict[str, int]
    scans_by_media: Dict[str, int]
    total_reports: int
    active_sessions: int
    system_status: Dict[str, Any]


# ── Analysis ──────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "LOW"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNDETERMINED = "UNDETERMINED"


class AnalysisStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"


class SignalResponse(BaseModel):
    signal_key: str
    signal_label: str
    severity: str
    score: Optional[float]
    description: Optional[str]

    model_config = {"from_attributes": True}


class AnalysisResponse(BaseModel):
    id: str
    original_filename: str
    media_type: str
    file_size_bytes: int
    file_sha256: Optional[str]
    mime_type: Optional[str]
    duration_seconds: Optional[float]
    status: str
    risk_level: Optional[str]
    synthetic_probability: Optional[float]
    confidence: Optional[float]
    model_id: Optional[str] = None
    model_version: Optional[str] = None
    prediction: Optional[str] = None
    limitations: Optional[str] = None
    error_code: Optional[str] = None
    explanation: Optional[str]
    signals: List[SignalResponse] = []
    raw_scores: Optional[Dict[str, Any]]
    provenance_info: Optional[Dict[str, Any]]
    media_deleted: bool
    processing_ms: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisListResponse(BaseModel):
    items: List[AnalysisResponse]
    total: int
    page: int
    per_page: int


# ── Reports ───────────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    id: str
    analysis_id: str
    title: str
    summary: Optional[str]
    recommendations: Optional[str]
    report_json: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Model Version ─────────────────────────────────────────────────────────────

class ModelVersionResponse(BaseModel):
    id: str
    name: str
    version: str
    model_type: str
    description: Optional[str]
    accuracy: Optional[float]
    f1_score: Optional[float]
    roc_auc: Optional[float]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard Stats ───────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_scanned: int
    suspicious: int
    low_risk: int
    high_risk: int
    critical: int
    undetermined: int
    scans_this_month: int
    scans_limit: int


# ── Dataset & Quality Gate Schemas ───────────────────────────────────────────

class DatasetRecordCreate(BaseModel):
    sample_id: str
    category: str
    source_dataset: str
    license_terms: str
    subject_id: Optional[str] = None
    video_id: Optional[str] = None
    generator_family: Optional[str] = "none"
    manipulation_type: Optional[str] = "none"
    device_class: Optional[str] = "laptop_webcam_720p"
    environment_type: Optional[str] = "indoor_bright"
    resolution: Optional[str] = "720p"
    fps: Optional[int] = 30
    true_label: str
    split: Optional[str] = "train"
    file_path: Optional[str] = None
    sha256_checksum: Optional[str] = None
    consent_verified: bool = True
    metadata_json: Optional[Dict[str, Any]] = None


class DatasetRecordResponse(DatasetRecordCreate):
    id: str
    created_at: datetime
    model_config = {"from_attributes": True}


class QualityGateRequest(BaseModel):
    image_base64: str


class QualityGateResponse(BaseModel):
    passed: bool
    overall_quality_score: float
    quality_label: str
    sharpness_score: float
    mean_luminance: float
    overexposed_ratio: float
    underexposed_ratio: float
    face_resolution: List[int]
    motion_blur_detected: bool
    rejection_reasons: List[str]
    recommended_guidance: Optional[str] = None


class FailureCaseCreate(BaseModel):
    model_version: str
    input_type: str
    device: Optional[str] = "laptop_webcam_720p"
    resolution: Optional[str] = "720p"
    environment: Optional[str] = "indoor_bright"
    true_label: str
    prediction: str
    confidence: float
    reason: str


class FailureCaseResponse(FailureCaseCreate):
    id: str
    failure_id: str
    is_verified_by_human: bool
    reviewed_by: Optional[str]
    added_to_training_set: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ModelRegistryResponse(BaseModel):
    id: str
    model_id: str
    model_name: str
    version: str
    status: str
    license: str
    weights_license: str
    checksum_sha256: str
    ece_score: Optional[float]
    brier_score: Optional[float]
    latency_ms: Optional[float]
    approved_by: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class DatasetSummaryStats(BaseModel):
    total_samples: int
    category_counts: Dict[str, int]
    split_counts: Dict[str, int]
    consent_compliance_pct: float


# ── Granular Consent Schemas ──────────────────────────────────────────────────

class ConsentPurposeEnum(str, Enum):
    MEDIA_PROCESSING = "MEDIA_PROCESSING"
    SAVE_HISTORY = "SAVE_HISTORY"
    RETAIN_MEDIA = "RETAIN_MEDIA"
    EXTERNAL_AI_SHARING = "EXTERNAL_AI_SHARING"
    MODEL_TRAINING = "MODEL_TRAINING"
    ANALYTICS = "ANALYTICS"


class ConsentItem(BaseModel):
    purpose: ConsentPurposeEnum
    granted: bool
    policy_version: str = "1.0.0"
    granted_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserConsentListResponse(BaseModel):
    consents: List[ConsentItem]
    policy_version: str = "1.0.0"


class UserConsentUpdateRequest(BaseModel):
    purpose: ConsentPurposeEnum
    granted: bool
    policy_version: str = "1.0.0"


# ── Audit Trail & Sovereignty Schemas ────────────────────────────────────────

class UserAuditLogItem(BaseModel):
    id: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAuditLogResponse(BaseModel):
    items: List[UserAuditLogItem]
    total: int
    page: int
    limit: int


class PurgeHistoryResponse(BaseModel):
    purged_count: int
    message: str

