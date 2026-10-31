"""add user consent append-only ledger and data migration

Revision ID: 0002_user_consent_ledger
Revises: 0001_baseline
Create Date: 2026-10-31 23:15:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from datetime import datetime, timezone
import uuid

# revision identifiers, used by Alembic.
revision: str = '0002_user_consent_ledger'
down_revision: Union[str, None] = '0001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update user_consents table structure for append-only ledger
    with op.batch_alter_table("user_consents") as batch_op:
        batch_op.add_column(sa.Column("status", sa.String(20), nullable=False, server_default="withdrawn"))
        batch_op.add_column(sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
        batch_op.add_column(sa.Column("method", sa.String(20), nullable=False, server_default="UI"))
        batch_op.drop_constraint("uq_user_consent_purpose", type_="unique")
        batch_op.create_index("ix_user_consents_user_purpose_timestamp", ["user_id", "purpose", "timestamp"])

    # 2. Backfill status & timestamp on existing user_consents rows
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE user_consents
        SET status = CASE WHEN granted = 1 OR granted IS TRUE THEN 'granted' ELSE 'withdrawn' END,
            timestamp = COALESCE(granted_at, withdrawn_at, created_at, CURRENT_TIMESTAMP),
            method = 'UI'
        WHERE status IS NULL
    """))

    # 3. Data migration (Phase 5c): Map existing booleans in user_preferences onto user_consents ledger
    prefs = conn.execute(text("SELECT user_id, privacy_mode, cloud_processing_enabled FROM user_preferences")).fetchall()
    now_iso = datetime.now(timezone.utc).isoformat()

    for pref in prefs:
        u_id = pref[0]
        p_mode = bool(pref[1])
        c_proc = bool(pref[2])

        # Map privacy_mode onto SAVE_HISTORY
        existing_hist = conn.execute(
            text("SELECT id FROM user_consents WHERE user_id = :u AND purpose = 'SAVE_HISTORY'"),
            {"u": u_id}
        ).fetchone()
        if not existing_hist:
            save_hist_status = "withdrawn" if p_mode else "granted"
            conn.execute(
                text("""
                    INSERT INTO user_consents (id, user_id, purpose, status, granted, policy_version, timestamp, method, created_at, updated_at)
                    VALUES (:id, :u, 'SAVE_HISTORY', :st, :gr, '1.0.0', :ts, 'MIGRATION', :ts, :ts)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "u": u_id,
                    "st": save_hist_status,
                    "gr": 1 if save_hist_status == "granted" else 0,
                    "ts": now_iso,
                }
            )

        # Map cloud_processing_enabled onto EXTERNAL_AI_SHARING
        existing_ai = conn.execute(
            text("SELECT id FROM user_consents WHERE user_id = :u AND purpose = 'EXTERNAL_AI_SHARING'"),
            {"u": u_id}
        ).fetchone()
        if not existing_ai:
            ai_status = "granted" if c_proc else "withdrawn"
            conn.execute(
                text("""
                    INSERT INTO user_consents (id, user_id, purpose, status, granted, policy_version, timestamp, method, created_at, updated_at)
                    VALUES (:id, :u, 'EXTERNAL_AI_SHARING', :st, :gr, '1.0.0', :ts, 'MIGRATION', :ts, :ts)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "u": u_id,
                    "st": ai_status,
                    "gr": 1 if ai_status == "granted" else 0,
                    "ts": now_iso,
                }
            )


def downgrade() -> None:
    with op.batch_alter_table("user_consents") as batch_op:
        batch_op.drop_index("ix_user_consents_user_purpose_timestamp")
        batch_op.create_unique_constraint("uq_user_consent_purpose", ["user_id", "purpose"])
        batch_op.drop_column("method")
        batch_op.drop_column("timestamp")
        batch_op.drop_column("status")
