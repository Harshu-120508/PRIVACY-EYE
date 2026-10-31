"""
Unit tests for ModelManager, Hugging Face Hub provenance, and startup integrity checks (Phase 2).
"""
import pytest
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.model_manager import (
    ModelManager,
    MODEL_PRESENT,
    MODEL_READY,
    MODEL_MISSING,
    MODEL_PLACEHOLDER,
    MODEL_CORRUPTED,
    MODEL_UNVERIFIED,
)
from app.core.config import settings
from app.ml.image_analyzer import _find_weights_path
from app.ml.video_analyzer import _find_video_weights_path
from app.ml.audio_analyzer import _find_audio_weights_path


def test_model_manager_manifest_loading():
    """Verify manifest v2.0.0 structure and required fields."""
    mm = ModelManager()
    manifest = mm.manifest
    assert manifest.get("version") == "2.0.0"
    assert "models" in manifest
    assert len(manifest["models"]) >= 4

    required_keys = {
        "name", "pipeline", "source", "repo_id", "revision",
        "filename", "expected_sha256", "size_bytes", "verified_at", "status",
    }
    for m in manifest["models"]:
        for k in required_keys:
            assert k in m, f"Key '{k}' missing from model '{m.get('name')}'"

    yunet = mm.get_manifest_entry("face_detection_yunet")
    assert yunet is not None
    assert yunet["status"] == "verified"
    assert yunet["pipeline"] == "live_scan"
    assert yunet["expected_sha256"] == "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"

    # Placeholder pipelines
    for p_name in ["image_efficientnet_b4", "video_efficientnet_temporal", "audio_wav2vec2_clone"]:
        p_entry = mm.get_manifest_entry(p_name)
        assert p_entry is not None
        assert p_entry["status"] == "placeholder"
        assert p_entry["source"] == "UNREGISTERED/PLACEHOLDER"
        assert p_entry["expected_sha256"] is None


def test_model_manager_sanitized_status():
    mm = ModelManager()
    status = mm.get_model_status()
    assert "ml_engine_status" in status
    assert "device" in status
    assert "models" in status
    assert "token" not in str(status).lower()
    assert "secret" not in str(status).lower()


def test_model_manager_sha256_verification(tmp_path: Path):
    mm = ModelManager(cache_dir=str(tmp_path))
    test_file = tmp_path / "sample.bin"
    test_file.write_bytes(b"privacy-eye-integrity-test")

    expected_sha = hashlib.sha256(b"privacy-eye-integrity-test").hexdigest()

    assert mm.verify_model(test_file, expected_sha) is True
    assert mm.verify_model(test_file, "wrong_hash") is False


def test_startup_check_detects_duplicate_hashes(tmp_path: Path):
    """Startup check must detect identical hashes across different pipelines."""
    mm = ModelManager(cache_dir=str(tmp_path))
    shared_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    mm.manifest = {
        "version": "2.0.0",
        "models": [
            {
                "name": "model_pipeline_a",
                "pipeline": "pipeline_a",
                "expected_sha256": shared_hash,
                "status": "verified",
            },
            {
                "name": "model_pipeline_b",
                "pipeline": "pipeline_b",
                "expected_sha256": shared_hash,
                "status": "verified",
            },
        ],
    }
    findings = mm.validate_registry_at_startup()
    dup_findings = [f for f in findings if f["type"] == "DUPLICATE_HASH"]
    assert len(dup_findings) == 1
    assert "Duplicate model hash detected" in dup_findings[0]["message"] or "shares identical" in dup_findings[0]["message"]


def test_startup_check_detects_tiny_corrupted_file(tmp_path: Path):
    """Startup check must detect 0-byte or suspiciously tiny files (< 1024 bytes)."""
    tiny_file = tmp_path / "corrupted_model.onnx"
    tiny_file.write_bytes(b"corrupt pointer")  # 15 bytes

    mm = ModelManager(cache_dir=str(tmp_path))
    mm.manifest = {
        "version": "2.0.0",
        "models": [
            {
                "name": "tiny_model",
                "pipeline": "image",
                "filename": "corrupted_model.onnx",
                "status": "verified",
            }
        ],
    }
    findings = mm.validate_registry_at_startup()
    tiny_findings = [f for f in findings if f["type"] == "TINY_FILE"]
    assert len(tiny_findings) == 1
    assert "suspiciously tiny" in tiny_findings[0]["message"]


def test_startup_check_flags_placeholder_models(tmp_path: Path):
    """Startup check must log notice for unregistered placeholder models."""
    mm = ModelManager(cache_dir=str(tmp_path))
    mm.manifest = {
        "version": "2.0.0",
        "models": [
            {
                "name": "test_placeholder",
                "pipeline": "audio",
                "source": "UNREGISTERED/PLACEHOLDER",
                "status": "placeholder",
            }
        ],
    }
    findings = mm.validate_registry_at_startup()
    placeholder_findings = [f for f in findings if f["type"] == "PLACEHOLDER_STATUS"]
    assert len(placeholder_findings) == 1


@pytest.mark.asyncio
async def test_download_model_rejects_placeholder(tmp_path: Path):
    """Calling download_model on placeholder weights must raise ValueError."""
    mm = ModelManager(cache_dir=str(tmp_path))
    with pytest.raises(ValueError, match="marked as UNREGISTERED/PLACEHOLDER"):
        await mm.download_model("image_efficientnet_b4")


@pytest.mark.asyncio
async def test_offline_fallback_sets_unverified_status(tmp_path: Path):
    """When Hub is unreachable, valid cached local copy is used with status 'MODEL_UNVERIFIED'."""
    mm = ModelManager(cache_dir=str(tmp_path))
    content = b"valid model binary content" * 100  # > 1024 bytes
    file_sha = hashlib.sha256(content).hexdigest()
    model_file = tmp_path / "cached_model.onnx"
    model_file.write_bytes(content)

    mm.manifest = {
        "version": "2.0.0",
        "models": [
            {
                "name": "cached_model",
                "pipeline": "image",
                "filename": "cached_model.onnx",
                "repo_id": "nonexistent/repo",
                "revision": "abc1234",
                "expected_sha256": file_sha,
                "status": "verified",
            }
        ],
    }

    # Simulate Hub unreachable
    with patch("huggingface_hub.HfApi.model_info", side_effect=Exception("Connection timed out")):
        result_path = await mm.download_model("cached_model", force=True)
        assert result_path == model_file
        assert mm._states["cached_model"] == MODEL_UNVERIFIED


@pytest.mark.asyncio
async def test_download_sha256_mismatch_refuses_load(tmp_path: Path):
    """When downloaded file SHA does not match expected, reject and set MODEL_CORRUPTED."""
    mm = ModelManager(cache_dir=str(tmp_path))
    downloaded_content = b"fake downloaded data" * 100
    model_file = tmp_path / "mismatch_model.onnx"
    model_file.write_bytes(downloaded_content)

    mm.manifest = {
        "version": "2.0.0",
        "models": [
            {
                "name": "mismatch_model",
                "pipeline": "image",
                "filename": "mismatch_model.onnx",
                "repo_id": "some/repo",
                "revision": "abc1234",
                "expected_sha256": "expected_different_sha256_hash",
                "status": "verified",
            }
        ],
    }

    with patch.object(mm, "fetch_hub_metadata", return_value={"sha256": "expected_different_sha256_hash"}):
        with patch("huggingface_hub.hf_hub_download", return_value=str(model_file)):
            with pytest.raises(ValueError, match="failed SHA-256 verification"):
                await mm.download_model("mismatch_model", force=True)
            assert mm._states["mismatch_model"] == MODEL_CORRUPTED


def test_path_wrappers_respect_placeholder_registry():
    """Analyzers must return None for weights paths when models are marked placeholder."""
    assert _find_weights_path() is None
    assert _find_video_weights_path() is None
    assert _find_audio_weights_path() is None
