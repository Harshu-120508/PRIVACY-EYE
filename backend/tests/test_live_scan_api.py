"""
Privacy Eye — Live Camera Face Authenticity API Test Suite
Tests:
- POST /api/v1/live/frame with synthetic camera frame
- POST /api/v1/live/challenge for active liveness challenge generation
- POST /api/v1/live/save-audit to persist live authenticity audit record
- POST /api/v1/live/consent-response for privacy-first training pool
- GET  /api/v1/live/training-stats for pool telemetry
- RBAC protection: rejection of unauthenticated frame submissions (401)
- Edge case: corrupted/invalid base64 image decoding
"""
import base64
import time
import pytest
import numpy as np
import cv2
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.session import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def live_test_client():
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
        yield client

    app.dependency_overrides.clear()
    await test_engine.dispose()


def _get_test_frame_base64() -> str:
    """Generate a valid base64-encoded JPEG test camera frame."""
    frame = np.full((320, 320, 3), 130, dtype=np.uint8)
    cv2.ellipse(frame, (160, 160), (70, 90), 0, 0, 360, (180, 160, 140), -1)
    cv2.circle(frame, (130, 140), 10, (240, 240, 240), -1)
    cv2.circle(frame, (190, 140), 10, (240, 240, 240), -1)
    _, buf = cv2.imencode(".jpg", frame)
    return base64.b64encode(buf.tobytes()).decode("utf-8")


async def _get_auth_headers(client: AsyncClient, email: str = "camera_user@example.com") -> dict:
    """Helper to register and return authorization headers."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Camera Operator",
    })
    token = reg.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_live_frame_analysis_endpoint(live_test_client: AsyncClient):
    """Test camera frame ingestion and real-time authenticity evaluation."""
    headers = await _get_auth_headers(live_test_client, "frame_operator@example.com")
    sess_id = f"test_session_{int(time.time())}"
    frame_b64 = _get_test_frame_base64()

    res = await live_test_client.post(
        "/api/v1/live/frame",
        json={
            "session_id": sess_id,
            "image_base64": f"data:image/jpeg;base64,{frame_b64}",
            "run_challenge": False,
        },
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "assessment" in data
    assert "confidence" in data
    assert "processing_ms" in data


@pytest.mark.anyio
async def test_live_challenge_generation(live_test_client: AsyncClient):
    """Test generating a random interactive challenge (e.g. turn head or smile)."""
    headers = await _get_auth_headers(live_test_client, "challenge_operator@example.com")
    sess_id = f"test_challenge_sess_{int(time.time())}"
    res = await live_test_client.post(
        "/api/v1/live/challenge",
        params={"session_id": sess_id},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "type" in data
    assert "label" in data


@pytest.mark.anyio
async def test_live_save_audit_and_consent(live_test_client: AsyncClient):
    """Test saving live session audit record and consent response."""
    headers = await _get_auth_headers(live_test_client, "audit_operator@example.com")
    sess_id = f"test_audit_sess_{int(time.time())}"

    # 1. Save audit session
    audit_payload = {
        "session_id": sess_id,
        "assessment": "GENUINE_LIVE_HUMAN",
        "category_label": "GENUINE LIVE HUMAN",
        "confidence": 92.5,
        "quality_index": 78,
        "signals": [{"key": "texture", "label": "Micro-texture authentic", "severity": "low"}],
        "explanation": "High biological consistency observed.",
        "consent_given": True,
    }
    save_res = await live_test_client.post("/api/v1/live/save-audit", json=audit_payload, headers=headers)
    assert save_res.status_code == 201
    assert save_res.json()["status"] == "SAVED"
    assert "analysis_id" in save_res.json()

    # 2. Submit consent response
    consent_payload = {
        "session_id": sess_id,
        "consent_given": True,
        "category_label": "GENUINE LIVE HUMAN",
        "confidence": 92.5,
        "quality_score": 78.0,
    }
    consent_res = await live_test_client.post("/api/v1/live/consent-response", json=consent_payload, headers=headers)
    assert consent_res.status_code == 200
    assert consent_res.json()["consent_given"] is True
    assert consent_res.json()["status"] == "CONTRIBUTED"

    # 3. Check training pool stats
    stats_res = await live_test_client.get("/api/v1/live/training-stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "consented_samples" in stats


@pytest.mark.anyio
async def test_live_frame_corrupted_payload(live_test_client: AsyncClient):
    """Test corrupted or invalid image base64 handling with authenticated client."""
    headers = await _get_auth_headers(live_test_client, "corrupt_test@example.com")
    res = await live_test_client.post(
        "/api/v1/live/frame",
        json={
            "session_id": "test_corrupted",
            "image_base64": "invalid_base64_string",
        },
        headers=headers,
    )
    # The endpoint catches bad decoding cleanly (400 Bad Request)
    assert res.status_code == 400
    assert "Invalid base64" in res.json()["detail"]


@pytest.mark.anyio
async def test_unauthenticated_live_access_rejected(live_test_client: AsyncClient):
    """Test that live camera frame processing rejects unauthenticated calls."""
    res = await live_test_client.post(
        "/api/v1/live/frame",
        json={
            "session_id": "anon_session",
            "image_base64": "data:image/jpeg;base64,abc",
        },
    )
    assert res.status_code == 401
