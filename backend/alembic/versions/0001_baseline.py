"""
Baseline migration — Privacy Eye initial schema.

This migration establishes the baseline for all existing tables that were
previously auto-created via SQLAlchemy `create_all()`. For existing databases
that already have these tables, stamp this revision without running it:

    alembic stamp 0001_baseline

For fresh databases, run normally:

    alembic upgrade head

Revision ID: 0001_baseline
Revises: (none)
Create Date: 2026-10-18
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all Privacy Eye tables from scratch (for fresh databases)."""

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(320), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("role", sa.Enum("USER", "ADMIN", "ENTERPRISE", name="userrole"), default="USER"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("scans_used_this_month", sa.Integer, default=0),
        sa.Column("scans_limit", sa.Integer, default=20),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── sessions ───────────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False, index=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("is_remember_me", sa.Boolean, default=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── user_preferences ───────────────────────────────────────────────────
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("theme", sa.String(20), default="dark"),
        sa.Column("language", sa.String(10), default="en"),
        sa.Column("notifications_enabled", sa.Boolean, default=True),
        sa.Column("privacy_mode", sa.Boolean, default=True),
        sa.Column("cloud_processing_enabled", sa.Boolean, default=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    # ── password_reset_tokens ──────────────────────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(64), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # ── api_keys ───────────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("usage_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── model_versions ─────────────────────────────────────────────────────
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("accuracy", sa.Float, nullable=True),
        sa.Column("precision", sa.Float, nullable=True),
        sa.Column("recall", sa.Float, nullable=True),
        sa.Column("f1_score", sa.Float, nullable=True),
        sa.Column("roc_auc", sa.Float, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("name", "version", name="uq_model_name_version"),
    )

    # ── media_analysis ─────────────────────────────────────────────────────
    op.create_table(
        "media_analysis",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("media_type", sa.Enum("IMAGE", "VIDEO", "AUDIO", name="mediatype"), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("file_sha256", sa.String(64), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("status", sa.Enum("PENDING", "PROCESSING", "COMPLETE", "FAILED", name="analysisstatus"), default="PENDING"),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_ms", sa.Integer, nullable=True),
        sa.Column("risk_level", sa.Enum("LOW", "SUSPICIOUS", "HIGH", "CRITICAL", "UNDETERMINED", name="risklevel"), nullable=True),
        sa.Column("synthetic_probability", sa.Float, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("model_version_id", sa.String(36), sa.ForeignKey("model_versions.id"), nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("raw_scores", sa.JSON, nullable=True),
        sa.Column("provenance_info", sa.JSON, nullable=True),
        sa.Column("media_deleted", sa.Boolean, default=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_media_analysis_user_created", "media_analysis", ["user_id", "created_at"])
    op.create_index("ix_media_analysis_risk", "media_analysis", ["risk_level"])

    # ── analysis_signals ───────────────────────────────────────────────────
    op.create_table(
        "analysis_signals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("media_analysis.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_key", sa.String(100), nullable=False),
        sa.Column("signal_label", sa.String(200), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
    )

    # ── reports ────────────────────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_id", sa.String(36), sa.ForeignKey("media_analysis.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("recommendations", sa.Text, nullable=True),
        sa.Column("report_json", sa.JSON, nullable=True),
        sa.Column("pdf_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # ── audit_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("detail", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_audit_logs_user_action", "audit_logs", ["user_id", "action"])

    # ── face_training_samples ──────────────────────────────────────────────
    op.create_table(
        "face_training_samples",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column("consent_given", sa.Boolean, nullable=False),
        sa.Column("category_label", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("quality_score", sa.Float, nullable=False),
        sa.Column("image_path", sa.String(500), nullable=True),
        sa.Column("landmarks_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # ── dataset_records ────────────────────────────────────────────────────
    op.create_table(
        "dataset_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sample_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("source_dataset", sa.String(100), nullable=False),
        sa.Column("license_terms", sa.String(100), nullable=False),
        sa.Column("subject_id", sa.String(100), nullable=True, index=True),
        sa.Column("video_id", sa.String(100), nullable=True),
        sa.Column("generator_family", sa.String(50), nullable=True),
        sa.Column("manipulation_type", sa.String(50), nullable=True),
        sa.Column("device_class", sa.String(50), nullable=True),
        sa.Column("environment_type", sa.String(50), nullable=True),
        sa.Column("resolution", sa.String(20), nullable=True),
        sa.Column("fps", sa.Integer, default=30),
        sa.Column("true_label", sa.String(50), nullable=False),
        sa.Column("split", sa.String(50), default="train", index=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("sha256_checksum", sa.String(64), nullable=True),
        sa.Column("consent_verified", sa.Boolean, default=True),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_dataset_category_split", "dataset_records", ["category", "split"])

    # ── failure_cases ──────────────────────────────────────────────────────
    op.create_table(
        "failure_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("failure_id", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("input_type", sa.String(50), nullable=False),
        sa.Column("device", sa.String(50), nullable=True),
        sa.Column("resolution", sa.String(20), nullable=True),
        sa.Column("environment", sa.String(50), nullable=True),
        sa.Column("true_label", sa.String(50), nullable=False),
        sa.Column("prediction", sa.String(50), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("is_verified_by_human", sa.Boolean, default=False),
        sa.Column("reviewed_by", sa.String(100), nullable=True),
        sa.Column("added_to_training_set", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # ── model_registry ─────────────────────────────────────────────────────
    op.create_table(
        "model_registry",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), default="EXPERIMENTAL"),
        sa.Column("license", sa.String(100), nullable=False),
        sa.Column("weights_license", sa.String(100), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("ece_score", sa.Float, nullable=True),
        sa.Column("brier_score", sa.Float, nullable=True),
        sa.Column("latency_ms", sa.Float, nullable=True),
        sa.Column("approved_by", sa.String(100), nullable=True),
        sa.Column("metrics_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    # ── live_sessions ──────────────────────────────────────────────────────
    op.create_table(
        "live_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("device_info", sa.String(200), nullable=True),
        sa.Column("stream_fps", sa.Float, nullable=True),
        sa.Column("resolution", sa.String(50), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), default="ACTIVE"),
        sa.Column("total_frames_analyzed", sa.Integer, default=0),
        sa.Column("avg_latency_ms", sa.Float, nullable=True),
    )


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("live_sessions")
    op.drop_table("model_registry")
    op.drop_table("failure_cases")
    op.drop_index("ix_dataset_category_split", table_name="dataset_records")
    op.drop_table("dataset_records")
    op.drop_table("face_training_samples")
    op.drop_index("ix_audit_logs_user_action", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("reports")
    op.drop_table("analysis_signals")
    op.drop_index("ix_media_analysis_risk", table_name="media_analysis")
    op.drop_index("ix_media_analysis_user_created", table_name="media_analysis")
    op.drop_table("media_analysis")
    op.drop_table("model_versions")
    op.drop_table("api_keys")
    op.drop_table("password_reset_tokens")
    op.drop_table("user_preferences")
    op.drop_table("sessions")
    op.drop_table("users")

    # Drop enum types
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mediatype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="analysisstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="risklevel").drop(op.get_bind(), checkfirst=True)
