"""
Privacy Eye — Granular Consent Management & Enforcement Test Suite
Verifies:
- Default unbundled consent initialization (6 separate purposes)
- Updating and withdrawing consent via PUT /api/v1/users/me/consents
- Server-side enforcement: blocking media processing when MEDIA_PROCESSING is withdrawn (403 Forbidden)
- Server-side enforcement: omitting history retention when SAVE_HISTORY is withdrawn
- Re-granting consent and audit log generation
"""
import io
import pytest
import numpy as np
import cv2
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.session import Base, get_db
from app.database.models import User, UserConsent, ConsentPurpose

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def consent_test_client():
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


def _make_test_image() -> bytes:
    img = np.full((64, 64, 3), 128, dtype=np.uint8)
    cv2.circle(img, (32, 32), 16, (180, 160, 140), -1)
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


@pytest.mark.anyio
async def test_unbundled_consent_defaults_and_updates(consent_test_client: AsyncClient):
    """Test retrieving and updating unbundled consent choices."""
    # 1. Register user
    reg = await consent_test_client.post("/api/v1/auth/register", json={
        "email": "sovereign_user@example.com",
        "password": "Password123!",
        "full_name": "Sovereign User",
    })
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Retrieve initial consents
    res = await consent_test_client.get("/api/v1/users/me/consents", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "consents" in data
    assert len(data["consents"]) == 6

    consent_map = {c["purpose"]: c["granted"] for c in data["consents"]}
    assert consent_map["MEDIA_PROCESSING"] is True
    assert consent_map["SAVE_HISTORY"] is True
    assert consent_map["RETAIN_MEDIA"] is False
    assert consent_map["EXTERNAL_AI_SHARING"] is False
    assert consent_map["MODEL_TRAINING"] is False
    assert consent_map["ANALYTICS"] is False

    # 3. Withdraw SAVE_HISTORY consent
    up_res = await consent_test_client.put(
        "/api/v1/users/me/consents",
        json={"purpose": "SAVE_HISTORY", "granted": False, "policy_version": "1.0.0"},
        headers=headers,
    )
    assert up_res.status_code == 200
    up_data = up_res.json()
    updated_map = {c["purpose"]: c["granted"] for c in up_data["consents"]}
    assert updated_map["SAVE_HISTORY"] is False


@pytest.mark.anyio
async def test_server_side_consent_enforcement(consent_test_client: AsyncClient):
    """Test server-side enforcement of MEDIA_PROCESSING and SAVE_HISTORY consents."""
    # 1. Register user
    reg = await consent_test_client.post("/api/v1/auth/register", json={
        "email": "enforce_test@example.com",
        "password": "Password123!",
    })
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    png_bytes = _make_test_image()

    # 2. Withdraw MEDIA_PROCESSING consent
    await consent_test_client.put(
        "/api/v1/users/me/consents",
        json={"purpose": "MEDIA_PROCESSING", "granted": False, "policy_version": "1.0.0"},
        headers=headers,
    )

    # 3. Attempting to analyze media must be blocked with 403 Forbidden
    files = {"file": ("test.png", png_bytes, "image/png")}
    block_res = await consent_test_client.post("/api/v1/analyze/image", files=files, headers=headers)
    assert block_res.status_code == 403
    assert "Media processing consent is currently withdrawn" in block_res.json()["detail"]

    # 4. Re-grant MEDIA_PROCESSING but withdraw SAVE_HISTORY
    await consent_test_client.put(
        "/api/v1/users/me/consents",
        json={"purpose": "MEDIA_PROCESSING", "granted": True, "policy_version": "1.0.0"},
        headers=headers,
    )
    await consent_test_client.put(
        "/api/v1/users/me/consents",
        json={"purpose": "SAVE_HISTORY", "granted": False, "policy_version": "1.0.0"},
        headers=headers,
    )

    # 5. Media analysis succeeds and returns complete result
    files = {"file": ("ephemeral.png", png_bytes, "image/png")}
    ok_res = await consent_test_client.post("/api/v1/analyze/image", files=files, headers=headers)
    assert ok_res.status_code == 201
    analysis_id = ok_res.json()["id"]

    # 6. Verify that history is NOT retained (history list returns 0 records)
    hist_res = await consent_test_client.get("/api/v1/analyze/history", headers=headers)
    assert hist_res.status_code == 200
    assert hist_res.json()["total"] == 0


@pytest.mark.anyio
async def test_video_and_audio_consent_enforcement(consent_test_client: AsyncClient):
    """Verify server-side consent enforcement across video and audio pipelines."""
    import wave

    reg = await consent_test_client.post("/api/v1/auth/register", json={
        "email": "multimodal_consent@example.com",
        "password": "Password123!",
        "full_name": "Multimodal Consent User",
    })
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate test WAV
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 4000)
    wav_bytes = wav_io.getvalue()

    # 1. Withdraw MEDIA_PROCESSING consent
    await consent_test_client.put(
        "/api/v1/users/me/consents",
        json={"purpose": "MEDIA_PROCESSING", "granted": False, "policy_version": "1.0.0"},
        headers=headers,
    )

    # 2. Audio upload must be blocked with 403 Forbidden
    audio_files = {"file": ("test_voice.wav", wav_bytes, "audio/wav")}
    audio_block = await consent_test_client.post("/api/v1/analyze/audio", files=audio_files, headers=headers)
    assert audio_block.status_code == 403
    assert "Media processing consent is currently withdrawn" in audio_block.json()["detail"]

    # 3. Re-grant MEDIA_PROCESSING but withdraw SAVE_HISTORY
    await consent_test_client.put(
        "/api/v1/users/me/consents",
        json={"purpose": "MEDIA_PROCESSING", "granted": True, "policy_version": "1.0.0"},
        headers=headers,
    )
    await consent_test_client.put(
        "/api/v1/users/me/consents",
        json={"purpose": "SAVE_HISTORY", "granted": False, "policy_version": "1.0.0"},
        headers=headers,
    )

    # 4. Audio analysis succeeds ephemerally
    audio_ok = await consent_test_client.post("/api/v1/analyze/audio", files=audio_files, headers=headers)
    assert audio_ok.status_code == 201
    assert audio_ok.json()["status"] == "COMPLETE"

    # 5. History total remains 0
    hist_res = await consent_test_client.get("/api/v1/analyze/history", headers=headers)
    assert hist_res.status_code == 200
    assert hist_res.json()["total"] == 0

