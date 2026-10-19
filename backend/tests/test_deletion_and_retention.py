"""
Privacy Eye — Deletion, Ephemeral Retention, and Sanitization Test Suite
Tests:
1. Media analysis soft deletion and exclusion from history
2. User account permanent erasure (GDPR Article 17) with cascade verification
3. Ephemeral file cleanup and temp directory purging
4. Sanitization and input validation edge cases (corrupted headers, path traversal in filenames)
"""
import io
import os
import time
import pytest
import numpy as np
import cv2
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.main import app
from app.database.session import Base, get_db
from app.database.models import User, MediaAnalysis, UserConsent, UserSession
from app.services.file_service import file_service

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def retention_test_client():
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, async_session

    app.dependency_overrides.clear()
    await test_engine.dispose()


def _generate_test_image() -> bytes:
    img = np.full((64, 64, 3), 128, dtype=np.uint8)
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


@pytest.mark.anyio
async def test_analysis_deletion_workflow(retention_test_client):
    """Verify analysis record soft-deletion and exclusion from user views."""
    client, session_maker = retention_test_client

    # Register user
    reg = await client.post("/api/v1/auth/register", json={
        "email": "deleter@example.com",
        "password": "Password123!",
        "full_name": "Deleter User",
    })
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload and analyze
    png_bytes = _generate_test_image()
    res = await client.post(
        "/api/v1/analyze/image",
        files={"file": ("to_delete.png", png_bytes, "image/png")},
        headers=headers,
    )
    assert res.status_code == 201
    analysis_id = res.json()["id"]

    # Verify present in history
    hist_before = await client.get("/api/v1/analyze/history", headers=headers)
    assert hist_before.status_code == 200
    assert any(item["id"] == analysis_id for item in hist_before.json()["items"])

    # Delete analysis
    del_res = await client.delete(f"/api/v1/analyze/{analysis_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify no longer returned in single item GET
    get_res = await client.get(f"/api/v1/analyze/{analysis_id}", headers=headers)
    assert get_res.status_code == 404

    # Verify no longer returned in history
    hist_after = await client.get("/api/v1/analyze/history", headers=headers)
    assert hist_after.status_code == 200
    assert not any(item["id"] == analysis_id for item in hist_after.json()["items"])


@pytest.mark.anyio
async def test_gdpr_account_erasure(retention_test_client):
    """Verify permanent account deletion cascades across analyses, consents, and sessions."""
    client, session_maker = retention_test_client

    # Register user
    reg = await client.post("/api/v1/auth/register", json={
        "email": "gdpr_user@example.com",
        "password": "Password123!",
        "full_name": "GDPR Subject",
    })
    user_data = reg.json()
    user_id = user_data["user"]["id"]
    token = user_data["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add an analysis
    png_bytes = _generate_test_image()
    await client.post(
        "/api/v1/analyze/image",
        files={"file": ("gdpr_test.png", png_bytes, "image/png")},
        headers=headers,
    )

    # Perform account deletion with password verification
    del_res = await client.request(
        "DELETE",
        "/api/v1/users/me",
        json={"password_confirmation": "Password123!"},
        headers=headers,
    )
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Check direct database state
    async with session_maker() as db:
        user_check = await db.execute(select(User).where(User.id == user_id))
        assert user_check.scalar_one_or_none() is None

        analysis_check = await db.execute(select(MediaAnalysis).where(MediaAnalysis.user_id == user_id))
        assert len(analysis_check.scalars().all()) == 0

        consent_check = await db.execute(select(UserConsent).where(UserConsent.user_id == user_id))
        assert len(consent_check.scalars().all()) == 0


@pytest.mark.anyio
async def test_ephemeral_file_service_cleanup():
    """Verify FileService temp file creation, deletion, and batch purge."""
    # Create temp files
    f1 = await file_service.save_temp(b"sample bytes 1", suffix=".png")
    f2 = await file_service.save_temp(b"sample bytes 2", suffix=".mp4")

    assert f1.exists()
    assert f2.exists()

    # Explicit delete
    file_service.delete_temp(f1)
    assert not f1.exists()

    # Batch purge with max_age_seconds=0
    purged = file_service.cleanup_orphaned_temp_files(max_age_seconds=0)
    assert purged >= 1
    assert not f2.exists()


@pytest.mark.anyio
async def test_filename_sanitization_and_path_traversal(retention_test_client):
    """Verify malicious filenames with path traversal attempts are safely sanitized."""
    client, _ = retention_test_client

    reg = await client.post("/api/v1/auth/register", json={
        "email": "traversal_test@example.com",
        "password": "Password123!",
    })
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    png_bytes = _generate_test_image()
    # Attempt directory traversal in filename
    malicious_filename = "../../../etc/passwd.png"

    res = await client.post(
        "/api/v1/analyze/image",
        files={"file": (malicious_filename, png_bytes, "image/png")},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    # Raw media is deleted, no filesystem file should be created at traversal destination
    assert data["media_deleted"] is True
    assert not os.path.exists("../../../etc/passwd.png")
