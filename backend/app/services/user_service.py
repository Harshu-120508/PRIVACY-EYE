"""
Privacy Eye — User & Session Database Service
Handles Argon2id user registration, authentication verification, session lifecycle,
token rotation, password changes, and account deletion with relational integrity.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, delete
import structlog

from app.database.models import (
    User,
    UserSession,
    UserPreferences,
    PasswordResetToken,
    AuditLog,
    FaceTrainingSample,
    Report,
)
from app.schemas.schemas import UserRegisterRequest
from app.core.security import (
    hash_password,
    verify_password,
    validate_password_policy,
    generate_secure_token,
    hash_token,
    create_access_token,
)
from app.core.config import settings

logger = structlog.get_logger(__name__)


class UserService:
    async def get_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        normalized = email.strip().lower()
        result = await db.execute(select(User).where(User.email == normalized))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, body: UserRegisterRequest) -> User:
        """Create new database-backed user with Argon2id password hash."""
        validate_password_policy(body.password, body.confirm_password)
        normalized_email = body.email.strip().lower()

        user = User(
            id=str(uuid.uuid4()),
            email=normalized_email,
            hashed_password=hash_password(body.password),
            full_name=body.full_name.strip() if body.full_name else None,
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        await db.flush()

        # Create default preferences
        pref = UserPreferences(
            id=str(uuid.uuid4()),
            user_id=user.id,
            theme="dark",
            language="en",
            notifications_enabled=True,
            privacy_mode=True,
            cloud_processing_enabled=False,
        )
        db.add(pref)
        await db.flush()
        await db.refresh(user)
        return user

    async def create_session(
        self,
        db: AsyncSession,
        user: User,
        is_remember_me: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[UserSession, str, str]:
        """
        Creates a persistent server-side session in PostgreSQL/SQLite.
        Returns: (UserSession, access_token_jwt, raw_refresh_token)
        """
        session_id = str(uuid.uuid4())
        raw_refresh = generate_secure_token()
        refresh_hash = hash_token(raw_refresh)

        # TTL: 30 days if remember_me, 24 hours if regular session
        ttl_days = 30 if is_remember_me else 1
        expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)

        session = UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            is_remember_me=is_remember_me,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc),
        )
        db.add(session)

        # Issue access token
        access_token = create_access_token(
            subject=user.id,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            session_id=session_id,
        )

        await db.flush()
        return session, access_token, raw_refresh

    async def rotate_session(
        self, db: AsyncSession, raw_refresh_token: str
    ) -> Optional[Tuple[User, str, str]]:
        """
        Validates refresh token against database session and rotates it.
        Returns: (User, new_access_token, new_raw_refresh_token) or None
        """
        token_hash = hash_token(raw_refresh_token)
        now = datetime.now(timezone.utc)

        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.refresh_token_hash == token_hash,
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > now,
                )
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            return None

        user = await self.get_by_id(db, session.user_id)
        if not user or not user.is_active:
            return None

        # Rotate refresh token
        new_raw_refresh = generate_secure_token()
        session.refresh_token_hash = hash_token(new_raw_refresh)
        session.last_used_at = now

        new_access = create_access_token(
            subject=user.id,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            session_id=session.id,
        )
        await db.flush()
        return user, new_access, new_raw_refresh

    async def revoke_session(self, db: AsyncSession, session_id: str, user_id: str) -> bool:
        """Revoke a single specific session for a user."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.id == session_id,
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None),
                )
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.revoked_at = now
            await db.flush()
            return True
        return False

    async def revoke_all_sessions(self, db: AsyncSession, user_id: str) -> int:
        """Revoke all active sessions for a user (e.g. after password change)."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(UserSession)
            .where(and_(UserSession.user_id == user_id, UserSession.revoked_at.is_(None)))
            .values(revoked_at=now)
        )
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount

    async def get_active_sessions(
        self, db: AsyncSession, user_id: str, current_session_id: Optional[str] = None
    ) -> List[dict]:
        """Fetch list of non-revoked, unexpired sessions for user."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(UserSession)
            .where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None),
                    UserSession.expires_at > now,
                )
            )
            .order_by(UserSession.last_used_at.desc())
        )
        sessions = result.scalars().all()
        return [
            {
                "id": s.id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "is_current": s.id == current_session_id,
                "is_remember_me": s.is_remember_me,
                "created_at": s.created_at,
                "last_used_at": s.last_used_at,
                "expires_at": s.expires_at,
            }
            for s in sessions
        ]

    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
        confirm_password: Optional[str] = None,
    ) -> bool:
        """Verify current password, validate policy, and update to new Argon2id hash."""
        if not verify_password(current_password, user.hashed_password):
            return False

        validate_password_policy(new_password, confirm_password)
        user.hashed_password = hash_password(new_password)
        user.updated_at = datetime.now(timezone.utc)
        await db.flush()

        # Invalidate all active sessions across all devices
        await self.revoke_all_sessions(db, user.id)
        return True

    async def delete_account(
        self, db: AsyncSession, user: User, password_confirmation: str
    ) -> bool:
        """
        Verify password and execute full GDPR Article 17 Right to Erasure cascade:
        1. Permanently removes biometric samples and physically unlinks face crops from disk.
        2. Physically unlinks generated PDF report artifacts.
        3. Cleans up any orphaned upload chunks.
        4. Pseudonymizes / redacts historical audit entries so no plaintext PII remains.
        5. Deletes User entity (cascades to analyses, signals, sessions, consents, preferences, api_keys).
        """
        if not verify_password(password_confirmation, user.hashed_password):
            return False

        user_id = user.id

        # 1. Purge Face Training Samples & remove image crops from disk
        training_samples = (
            await db.execute(select(FaceTrainingSample).where(FaceTrainingSample.user_id == user_id))
        ).scalars().all()
        for sample in training_samples:
            if sample.image_path:
                try:
                    if os.path.exists(sample.image_path):
                        os.unlink(sample.image_path)
                except Exception as e:
                    logger.warning("Failed to unlink training face crop during erasure", path=sample.image_path, error=str(e))
        await db.execute(delete(FaceTrainingSample).where(FaceTrainingSample.user_id == user_id))

        # 2. Purge Report PDFs from disk
        reports = (
            await db.execute(select(Report).where(Report.user_id == user_id))
        ).scalars().all()
        for rep in reports:
            if rep.pdf_path:
                try:
                    if os.path.exists(rep.pdf_path):
                        os.unlink(rep.pdf_path)
                except Exception as e:
                    logger.warning("Failed to unlink report PDF during erasure", path=rep.pdf_path, error=str(e))

        # 3. Clean up orphaned temp files
        try:
            from app.services.file_service import file_service
            file_service.cleanup_orphaned_temp_files(max_age_seconds=0)
        except Exception as e:
            logger.warning("Temp cleanup during erasure error", error=str(e))

        # 4. Redact PII from historical AuditLog entries
        await db.execute(
            update(AuditLog)
            .where(AuditLog.user_id == user_id)
            .values(user_id=None, ip_address="0.0.0.0", user_agent=None)
        )

        # 5. Cascading deletion of User
        await db.delete(user)
        await db.flush()
        return True


user_service = UserService()
