"""
Privacy Eye — Model Context Protocol (MCP) Server Test Suite
Verifies all 8 MCP tools, strict schema validation, security bounds, and error handling.
"""
import io
import base64
import wave
import pytest
import numpy as np
import cv2

from app.mcp.server import (
    get_detection_capabilities,
    analyze_image,
    analyze_video,
    analyze_audio,
    get_analysis_status,
    get_analysis_result,
    get_model_status,
    get_privacy_settings,
    _verify_magic_bytes,
    _decode_base64_payload,
)


def _create_test_image_b64() -> str:
    """Generate a valid base64 PNG image."""
    img = np.full((64, 64, 3), 120, dtype=np.uint8)
    cv2.circle(img, (32, 32), 16, (180, 160, 140), -1)
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def _create_test_audio_b64() -> str:
    """Generate a valid base64 PCM WAV."""
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 4000)
    return base64.b64encode(wav_io.getvalue()).decode("utf-8")


def _create_test_video_b64() -> str:
    """Generate a valid base64 MP4 video."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        tmp_path = f.name
    try:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(tmp_path, fourcc, 10.0, (120, 120))
        for i in range(5):
            frame = np.full((120, 120, 3), 60 + i * 10, dtype=np.uint8)
            cv2.circle(frame, (60, 60), 20, (180, 160, 140), -1)
            out.write(frame)
        out.release()
        with open(tmp_path, "rb") as rf:
            raw = rf.read()
            return base64.b64encode(raw).decode("utf-8")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)



@pytest.mark.anyio
async def test_mcp_get_detection_capabilities():
    """Verify MCP detection capabilities tool."""
    caps = await get_detection_capabilities()
    assert caps["platform"] == "Privacy Eye"
    assert "image" in caps["supported_media"]
    assert "video" in caps["supported_media"]
    assert "audio" in caps["supported_media"]
    assert "privacy_guarantees" in caps
    assert "0 Bytes" in caps["privacy_guarantees"]["media_retention"]


@pytest.mark.anyio
async def test_mcp_get_model_status():
    """Verify MCP model status tool."""
    status = await get_model_status()
    assert "active_ensemble" in status
    assert "models" in status
    assert "disclaimer" in status


@pytest.mark.anyio
async def test_mcp_get_privacy_settings():
    """Verify MCP privacy settings tool."""
    settings = await get_privacy_settings()
    assert settings["policy_version"] == "1.0.0"
    assert settings["raw_media_persisted"] is False
    assert len(settings["unbundled_consent_purposes"]) >= 5
    assert "erasure" in settings["rights"]


@pytest.mark.anyio
async def test_mcp_analyze_image_success():
    """Verify successful real inference through MCP analyze_image."""
    img_b64 = _create_test_image_b64()
    result = await analyze_image(image_base64=img_b64, filename="sample.png")

    assert result["status"] == "COMPLETED"
    assert result["media_type"] == "IMAGE"
    assert result["model_id"] is not None
    assert result["prediction"] in ("AUTHENTIC", "MANIPULATED", "SUSPICIOUS", "UNDETERMINED")
    assert 0.0 <= result["synthetic_probability"] <= 1.0
    assert result["confidence_score"] >= 0.0
    assert result["limitations"] is not None
    assert isinstance(result["signals"], list)


@pytest.mark.anyio
async def test_mcp_analyze_image_invalid_payload():
    """Verify graceful error reporting when image payload is malformed or invalid."""
    # 1. Non-base64 string
    res_malformed = await analyze_image(image_base64="not-a-valid-base64-content!")
    assert res_malformed["status"] == "FAILED"
    assert res_malformed["error_code"] == "ERR_MCP_IMAGE_ANALYSIS_FAILED"
    assert res_malformed["confidence_score"] == 0.0

    # 2. Valid base64 but invalid magic bytes (e.g. plain text)
    txt_b64 = base64.b64encode(b"This is just a text file").decode("utf-8")
    res_invalid_type = await analyze_image(image_base64=txt_b64)
    assert res_invalid_type["status"] == "FAILED"
    assert "File signature does not match" in res_invalid_type["error_message"]


@pytest.mark.anyio
async def test_mcp_analyze_audio_success():
    """Verify successful acoustic feature analysis through MCP analyze_audio."""
    wav_b64 = _create_test_audio_b64()
    result = await analyze_audio(audio_base64=wav_b64, filename="sample.wav")

    assert result["status"] == "COMPLETED"
    assert result["media_type"] == "AUDIO"
    assert result["model_id"] is not None
    assert result["prediction"] is not None
    assert result["confidence_score"] >= 0.0
    assert result["limitations"] is not None


@pytest.mark.anyio
async def test_mcp_analyze_video_success():
    """Verify successful video analysis through MCP analyze_video."""
    vid_b64 = _create_test_video_b64()
    result = await analyze_video(video_base64=vid_b64, filename="sample.mp4")

    assert result["status"] == "COMPLETED"
    assert result["media_type"] == "VIDEO"
    assert result["model_id"] is not None
    assert result["prediction"] in ("AUTHENTIC", "MANIPULATED", "SUSPICIOUS", "UNDETERMINED")
    assert 0.0 <= result["synthetic_probability"] <= 1.0
    assert result["confidence_score"] >= 0.0
    assert result["limitations"] is not None
    assert isinstance(result["signals"], list)


@pytest.mark.anyio
async def test_mcp_analyze_video_invalid_payload():
    """Verify video error handling on corrupted base64 or non-video bytes."""
    res_malformed = await analyze_video(video_base64="not-a-valid-base64-payload!")
    assert res_malformed["status"] == "FAILED"
    assert res_malformed["error_code"] == "ERR_MCP_VIDEO_ANALYSIS_FAILED"

    txt_b64 = base64.b64encode(b"not a video file payload").decode("utf-8")
    res_invalid_type = await analyze_video(video_base64=txt_b64)
    assert res_invalid_type["status"] == "FAILED"
    assert "File signature does not match" in res_invalid_type["error_message"]


@pytest.mark.anyio
async def test_mcp_get_analysis_status_and_result_validation():
    """Verify strict UUID validation and not found handling in MCP query tools."""
    # 1. Invalid UUID format
    status_invalid = await get_analysis_status(analysis_id="not-a-uuid")
    assert status_invalid["status"] == "FAILED"
    assert status_invalid["error_code"] == "ERR_INVALID_ID_FORMAT"

    # 2. Non-existent UUID
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    status_not_found = await get_analysis_status(analysis_id=fake_uuid)
    assert status_not_found["status"] == "NOT_FOUND"

    result_not_found = await get_analysis_result(analysis_id=fake_uuid)
    assert result_not_found["status"] == "NOT_FOUND"


def test_magic_byte_verification_helpers():
    """Verify format signature security checks."""
    assert _verify_magic_bytes(b"\x89PNG\r\n\x1a\n\x00\x00", "image") is True
    assert _verify_magic_bytes(b"\xFF\xD8\xFF\xE0\x00\x10", "image") is True
    assert _verify_magic_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt ", "audio") is True
    assert _verify_magic_bytes(b"MALICIOUS_EXE_PAYLOAD", "image") is False
    assert _verify_magic_bytes(b"SHORT", "image") is False
