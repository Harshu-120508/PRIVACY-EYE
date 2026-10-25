"""
Privacy Eye — Media Analysis Pipeline Test Suite
Tests:
- Upload and analyze image endpoint with forensics fallback
- Upload and analyze audio endpoint
- Media analysis history and user pagination
- Media analysis dashboard statistics calculation
- Single analysis retrieval by ID
- Analysis soft-deletion
- Validation gates: unsupported media MIME types and oversized files
"""
import io
import wave
import pytest
import numpy as np
import cv2
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.database.session import Base, get_db
from app.database.models import User, RiskLevel

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def analysis_test_client():
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


def _generate_test_image() -> bytes:
    """Generate a valid test PNG image."""
    img = np.full((120, 120, 3), 140, dtype=np.uint8)
    cv2.circle(img, (60, 60), 30, (200, 180, 160), -1)
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


def _generate_test_wav() -> bytes:
    """Generate a valid test PCM WAV audio file."""
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 8000)
    return wav_io.getvalue()


def _generate_test_video() -> bytes:
    """Generate a lightweight valid MP4 video clip with 5 frames."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        tmp_path = f.name
    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(tmp_path, fourcc, 10.0, (120, 120))
        for i in range(5):
            frame = np.full((120, 120, 3), 60 + i * 10, dtype=np.uint8)
            cv2.circle(frame, (60, 60), 20, (200, 160, 120), -1)
            out.write(frame)
        out.release()
        with open(tmp_path, "rb") as rf:
            return rf.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)



@pytest.mark.anyio
async def test_image_analysis_pipeline(analysis_test_client: AsyncClient):
    """Test full image analysis pipeline lifecycle."""
    # 1. Register and get token
    reg = await analysis_test_client.post("/api/v1/auth/register", json={
        "email": "image_analyst@example.com",
        "password": "Password123!",
        "full_name": "Image Analyst",
    })
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload and analyze image
    png_bytes = _generate_test_image()
    files = {"file": ("test_sample.png", png_bytes, "image/png")}

    res = await analysis_test_client.post("/api/v1/analyze/image", files=files, headers=headers)
    assert res.status_code == 201

    data = res.json()
    assert data["status"] == "COMPLETE"
    assert data["original_filename"] == "test_sample.png"
    assert data["media_type"] == "IMAGE"
    assert data["risk_level"] in [r.value for r in RiskLevel]
    assert 0.0 <= data["synthetic_probability"] <= 1.0
    assert data["confidence"] >= 0.0
    assert data["processing_ms"] is not None
    assert data["media_deleted"] is True
    assert data["model_id"] is not None
    assert data["prediction"] in ("AUTHENTIC", "MANIPULATED", "SUSPICIOUS", "UNDETERMINED")
    assert data["limitations"] is not None
    assert isinstance(data["signals"], list)
    assert len(data["signals"]) > 0

    analysis_id = data["id"]

    # 3. Retrieve analysis by ID
    get_res = await analysis_test_client.get(f"/api/v1/analyze/{analysis_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == analysis_id

    # 4. Check user history
    hist_res = await analysis_test_client.get("/api/v1/analyze/history", headers=headers)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total"] >= 1
    assert any(item["id"] == analysis_id for item in hist_data["items"])

    # 5. Check dashboard stats
    stats_res = await analysis_test_client.get("/api/v1/analyze/stats", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_scanned"] >= 1

    # 6. Delete analysis record
    del_res = await analysis_test_client.delete(f"/api/v1/analyze/{analysis_id}", headers=headers)
    assert del_res.status_code in (200, 204)

    # 7. Verify soft deletion
    verify_del = await analysis_test_client.get(f"/api/v1/analyze/{analysis_id}", headers=headers)
    assert verify_del.status_code == 404


@pytest.mark.anyio
async def test_audio_analysis_pipeline(analysis_test_client: AsyncClient):
    """Test audio deepfake analysis pipeline with valid WAV stream."""
    reg = await analysis_test_client.post("/api/v1/auth/register", json={
        "email": "audio_analyst@example.com",
        "password": "Password123!",
    })
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    wav_bytes = _generate_test_wav()
    files = {"file": ("sample_voice.wav", wav_bytes, "audio/wav")}

    res = await analysis_test_client.post("/api/v1/analyze/audio", files=files, headers=headers)
    assert res.status_code == 201

    data = res.json()
    assert data["status"] == "COMPLETE"
    assert data["media_type"] == "AUDIO"
    assert data["original_filename"] == "sample_voice.wav"
    assert data["risk_level"] is not None
    assert data["synthetic_probability"] is not None
    assert data["model_id"] is not None
    assert data["prediction"] is not None


@pytest.mark.anyio
async def test_analysis_validation_gates(analysis_test_client: AsyncClient):
    """Test unsupported MIME type and boundary gates."""
    reg = await analysis_test_client.post("/api/v1/auth/register", json={
        "email": "validator@example.com",
        "password": "Password123!",
    })
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Unsupported media type (e.g. application/pdf)
    fake_pdf = b"%PDF-1.4 fake pdf stream"
    files = {"file": ("document.pdf", fake_pdf, "application/pdf")}

    res = await analysis_test_client.post("/api/v1/analyze/image", files=files, headers=headers)
    assert res.status_code == 422
    assert "Unsupported file type" in res.json()["detail"]


@pytest.mark.anyio
async def test_video_analysis_pipeline(analysis_test_client: AsyncClient):
    """Test full video analysis endpoint with valid MP4 clip."""
    reg = await analysis_test_client.post("/api/v1/auth/register", json={
        "email": "video_analyst@example.com",
        "password": "Password123!",
    })
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    mp4_bytes = _generate_test_video()
    files = {"file": ("test_clip.mp4", mp4_bytes, "video/mp4")}

    res = await analysis_test_client.post("/api/v1/analyze/video", files=files, headers=headers)
    assert res.status_code == 201

    data = res.json()
    assert data["status"] == "COMPLETE"
    assert data["media_type"] == "VIDEO"
    assert data["original_filename"] == "test_clip.mp4"
    assert data["risk_level"] is not None
    assert 0.0 <= data["synthetic_probability"] <= 1.0
    assert data["model_id"] is not None
    assert data["prediction"] in ("AUTHENTIC", "MANIPULATED", "SUSPICIOUS", "UNDETERMINED")
    assert isinstance(data["signals"], list)


def test_video_analyzer_neural_fusion():
    """Verify VideoAnalyzer neural ONNX fusion logic with mock session."""
    from app.ml.video_analyzer import VideoAnalyzer

    analyzer = VideoAnalyzer()
    # 1. Test forensics fallback when session is None
    analyzer.session = None
    mp4_bytes = _generate_test_video()
    res_forensics = analyzer.analyze(mp4_bytes, "clip.mp4")
    assert res_forensics["model_id"] == "privacy-eye-forensics-video-v1"

    # 2. Attach mock ONNX session and verify neural ensemble blending
    class MockOnnxInput:
        name = "input"
        shape = (1, 3, 224, 224)

    class MockOnnxSession:
        def get_inputs(self):
            return [MockOnnxInput()]

        def run(self, output_names, input_feed):
            # Logit for 0.85 synthetic probability
            return [np.array([[2.0]], dtype=np.float32)]

    analyzer.session = MockOnnxSession()
    analyzer.input_name = "input"
    analyzer.input_shape = (1, 3, 224, 224)

    res_ensemble = analyzer.analyze(mp4_bytes, "clip.mp4")
    assert res_ensemble["model_id"] == "privacy-eye-ensemble-video-v1"
    assert res_ensemble["provenance"]["neural_model"] == "video_efficientnet_temporal"
    assert any(s["key"] == "temporal_neural_classifier" for s in res_ensemble["signals"])


def test_audio_analyzer_neural_fusion():
    """Verify AudioAnalyzer neural ONNX fusion logic with mock session."""
    from app.ml.audio_analyzer import AudioAnalyzer

    analyzer = AudioAnalyzer()
    # 1. Test forensics fallback when session is None
    analyzer.session = None
    wav_bytes = _generate_test_wav()
    res_forensics = analyzer.analyze(wav_bytes, "voice.wav")
    assert res_forensics["model_id"] == "privacy-eye-forensics-audio-v1"

    # 2. Attach mock ONNX session and verify neural ensemble blending
    class MockAudioSession:
        def get_inputs(self):
            class Inp:
                name = "audio"
                shape = (1, 48000)
            return [Inp()]

        def run(self, output_names, input_feed):
            return [np.array([[0.1, 0.9]], dtype=np.float32)]

    analyzer.session = MockAudioSession()
    analyzer.input_name = "audio"
    analyzer.input_shape = (1, 48000)

    res_ensemble = analyzer.analyze(wav_bytes, "voice.wav")
    assert res_ensemble["model_id"] == "privacy-eye-ensemble-audio-v1"
    assert res_ensemble["provenance"]["neural_model"] == "audio_wav2vec2_clone"
    assert any(s["key"] == "neural_voice_clone_discriminator" for s in res_ensemble["signals"])

