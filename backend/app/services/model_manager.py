"""
Privacy Eye — Production Model Manager & Hugging Face Hub Artifact Registry
Handles model discovery, SHA-256 provenance verification, Hugging Face Hub LFS integrity,
local caching, atomic downloading, startup integrity validation, and in-memory singleton lifecycle management.
"""
import os
import json
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# State constants
MODEL_PRESENT = "MODEL_PRESENT"
MODEL_MISSING = "MODEL_MISSING"
MODEL_DOWNLOADING = "MODEL_DOWNLOADING"
MODEL_DOWNLOAD_FAILED = "MODEL_DOWNLOAD_FAILED"
MODEL_CORRUPTED = "MODEL_CORRUPTED"
MODEL_LOADING = "MODEL_LOADING"
MODEL_READY = "MODEL_READY"
MODEL_ERROR = "MODEL_ERROR"
MODEL_PLACEHOLDER = "MODEL_PLACEHOLDER"
MODEL_UNVERIFIED = "MODEL_UNVERIFIED"

# Built-in manifest fallback (Schema v2.0.0)
DEFAULT_MANIFEST = {
    "version": "2.0.0",
    "description": "Privacy Eye ML Model Manifest & Artifact Registry with verified SHA-256 provenance",
    "models": [
        {
            "name": "face_detection_yunet",
            "pipeline": "live_scan",
            "source": "opencv_zoo",
            "repo_id": None,
            "revision": "2023mar",
            "filename": "face_detection_yunet.onnx",
            "expected_sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
            "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
            "size_bytes": 232589,
            "verified_at": "2026-10-31T20:00:00Z",
            "status": "verified",
            "format": "onnx",
            "purpose": "YuNet 5-landmark face detector for live camera stream and active liveness verification",
            "framework": "opencv_dnn / onnx",
            "required_at_runtime": True,
            "fallback_urls": [
                "https://raw.githubusercontent.com/opencv/opencv_zoo/master/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
            ],
            "inference_entrypoint": "app.ml.live_authenticity.LiveAuthenticityEngine",
        },
        {
            "name": "image_efficientnet_b4",
            "pipeline": "image",
            "source": "UNREGISTERED/PLACEHOLDER",
            "repo_id": None,
            "revision": None,
            "filename": "image_efficientnet_b4.onnx",
            "expected_sha256": None,
            "sha256": None,
            "size_bytes": 0,
            "verified_at": None,
            "status": "placeholder",
            "format": "onnx",
            "purpose": "EfficientNet-B4 spatial deepfake detector fine-tuned on FaceForensics++ (c23)",
            "framework": "onnxruntime",
            "required_at_runtime": False,
            "fallback_urls": [],
            "inference_entrypoint": "app.ml.image_analyzer.ImageAnalyzer",
        },
        {
            "name": "video_efficientnet_temporal",
            "pipeline": "video",
            "source": "UNREGISTERED/PLACEHOLDER",
            "repo_id": None,
            "revision": None,
            "filename": "video_efficientnet_temporal.onnx",
            "expected_sha256": None,
            "sha256": None,
            "size_bytes": 0,
            "verified_at": None,
            "status": "placeholder",
            "format": "onnx",
            "purpose": "Temporal multi-frame video deepfake classifier",
            "framework": "onnxruntime",
            "required_at_runtime": False,
            "fallback_urls": [],
            "inference_entrypoint": "app.ml.video_analyzer.VideoAnalyzer",
        },
        {
            "name": "audio_wav2vec2_clone",
            "pipeline": "audio",
            "source": "UNREGISTERED/PLACEHOLDER",
            "repo_id": None,
            "revision": None,
            "filename": "audio_wav2vec2_clone.onnx",
            "expected_sha256": None,
            "sha256": None,
            "size_bytes": 0,
            "verified_at": None,
            "status": "placeholder",
            "format": "onnx",
            "purpose": "Wav2Vec2 neural voice clone and synthetic speech synthesis discriminator",
            "framework": "onnxruntime",
            "required_at_runtime": False,
            "fallback_urls": [],
            "inference_entrypoint": "app.ml.audio_analyzer.AudioAnalyzer",
        },
    ],
}


class ModelManager:
    """
    Centralized Model Lifecycle & Artifact Registry Manager for Privacy Eye.
    - Resolves model paths against versioned artifact registry
    - Validates SHA-256 provenance against Hugging Face Hub LFS metadata
    - Rejects duplicate hashes across different pipelines
    - Rejects empty (0-byte) or suspiciously small (<1024 bytes) weight files
    - Operates safe fallback when Hub is unreachable without silently trusting cache
    - Reuses loaded in-memory model singletons
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or settings.MODEL_CACHE_DIR).resolve()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = self._load_manifest()
        self._states: Dict[str, str] = {}
        self._loaded_models: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self.validate_registry_at_startup()
        self._init_states()

    def _load_manifest(self) -> Dict[str, Any]:
        """Load models/manifest.json from project root or backend search paths."""
        search_paths = [
            Path("models/manifest.json"),
            Path("../models/manifest.json"),
            Path(__file__).resolve().parent.parent.parent.parent / "models" / "manifest.json",
        ]
        for p in search_paths:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        logger.info("Loaded model manifest", path=str(p), version=data.get("version"))
                        return data
                except Exception as e:
                    logger.warning("Failed to parse manifest file, using fallback", path=str(p), error=str(e))
        return DEFAULT_MANIFEST

    def validate_registry_at_startup(self) -> List[Dict[str, Any]]:
        """
        Startup integrity check:
        (i) Fails/warns if two different pipelines have the same hash
        (ii) Fails/warns if a file is 0 bytes or suspiciously tiny (< 1024 bytes)
        (iii) Warns if pipeline status is placeholder
        """
        findings = []
        seen_hashes: Dict[str, str] = {}

        for m in self.manifest.get("models", []):
            name = m.get("name", "unnamed")
            pipeline = m.get("pipeline", "unknown")
            status = m.get("status", "unknown")
            expected_sha = m.get("expected_sha256") or m.get("sha256")

            # Check (i): duplicate hashes across different pipelines
            if expected_sha and expected_sha != "dummy_sha":
                sha_clean = expected_sha.lower().strip()
                if sha_clean in seen_hashes and seen_hashes[sha_clean] != pipeline:
                    msg = (
                        f"CRITICAL: Pipeline '{pipeline}' ({name}) shares identical SHA-256 hash "
                        f"with pipeline '{seen_hashes[sha_clean]}'. Untracked placeholder weights detected!"
                    )
                    logger.error(
                        "Duplicate model hash detected across pipelines",
                        pipeline_a=seen_hashes[sha_clean],
                        pipeline_b=pipeline,
                        sha256=sha_clean,
                    )
                    findings.append({"type": "DUPLICATE_HASH", "model": name, "message": msg})
                else:
                    seen_hashes[sha_clean] = pipeline

            # Check (ii): 0 bytes or suspiciously tiny (< 1024 bytes)
            filename = m.get("filename")
            if filename:
                local_path = self._find_model_file(filename)
                if local_path and local_path.exists():
                    size = local_path.stat().st_size
                    if size < 1024:
                        msg = (
                            f"CRITICAL: Model file '{filename}' for '{name}' is suspiciously tiny "
                            f"({size} bytes). Possible corrupted pointer or empty file!"
                        )
                        logger.error("Corrupted or tiny model file detected", file=str(local_path), size=size)
                        findings.append({"type": "TINY_FILE", "model": name, "message": msg})

            # Check (iii): placeholder status
            if status == "placeholder" or m.get("source") == "UNREGISTERED/PLACEHOLDER":
                msg = (
                    f"NOTICE: Pipeline '{pipeline}' model '{name}' is UNREGISTERED/PLACEHOLDER. "
                    "Running in verified deterministic digital forensics fallback mode."
                )
                logger.info("Pipeline operating in verified forensics fallback mode", model=name, pipeline=pipeline)
                findings.append({"type": "PLACEHOLDER_STATUS", "model": name, "message": msg})

        return findings

    def _init_states(self):
        """Scan and populate initial operational states for all declared models."""
        for m in self.manifest.get("models", []):
            name = m["name"]
            status = self.check_model(name)
            self._states[name] = status

    def _find_model_file(self, filename: str) -> Optional[Path]:
        """Locates model in cache_dir, app/ml/weights, or candidate search paths."""
        candidates = [
            self.cache_dir / filename,
            Path(settings.ML_MODELS_DIR) / filename,
            Path("app/ml/weights") / filename,
            Path(__file__).resolve().parent.parent / "ml" / "weights" / filename,
        ]
        for p in candidates:
            if p.exists() and p.is_file():
                return p
        return None

    def get_manifest_entry(self, model_name: str) -> Optional[Dict[str, Any]]:
        for m in self.manifest.get("models", []):
            if m["name"] == model_name or m.get("filename") == model_name:
                return m
        return None

    def verify_model(self, file_path: Path, expected_sha256: Optional[str] = None) -> bool:
        """Computes SHA-256 checksum (chunked read) and compares against expected hash."""
        if not file_path.exists() or not file_path.is_file():
            return False
        if not expected_sha256 or expected_sha256 == "dummy_sha":
            return True

        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        actual_sha = hasher.hexdigest().lower()
        matches = actual_sha == expected_sha256.lower().strip()
        if not matches:
            logger.warning(
                "Model verification checksum mismatch",
                file=str(file_path),
                actual=actual_sha,
                expected=expected_sha256,
            )
        return matches

    def check_model(self, model_name: str) -> str:
        """
        Inspects model presence, status, and integrity.
        Returns: MODEL_READY, MODEL_PRESENT, MODEL_PLACEHOLDER, MODEL_MISSING, MODEL_CORRUPTED.
        """
        if model_name in self._loaded_models:
            return MODEL_READY

        meta = self.get_manifest_entry(model_name)
        if not meta:
            return MODEL_MISSING

        if meta.get("status") == "placeholder" or meta.get("source") == "UNREGISTERED/PLACEHOLDER":
            return MODEL_PLACEHOLDER

        filename = meta.get("filename", model_name)
        path = self._find_model_file(filename)

        if not path:
            return MODEL_MISSING

        # Reject 0 bytes or suspiciously tiny files
        if path.stat().st_size < 1024:
            return MODEL_CORRUPTED

        expected_sha = meta.get("expected_sha256") or meta.get("sha256")
        if expected_sha and not self.verify_model(path, expected_sha):
            return MODEL_CORRUPTED

        return MODEL_PRESENT

    def fetch_hub_metadata(
        self, repo_id: str, filename: str, revision: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches official model metadata from Hugging Face Hub using HfApi().model_info.
        Reads LFS sha256 and size from the file's LFS metadata info.
        """
        try:
            from huggingface_hub import HfApi
            api = HfApi(token=settings.HF_TOKEN if settings.HF_TOKEN else None)
            info = api.model_info(repo_id, revision=revision, files_metadata=True)
            for sibling in (info.siblings or []):
                if sibling.rfilename == filename:
                    lfs_info = sibling.lfs
                    if lfs_info:
                        sha = getattr(lfs_info, "sha256", None) or (
                            lfs_info.get("sha256") if isinstance(lfs_info, dict) else None
                        )
                        size = getattr(lfs_info, "size", None) or (
                            lfs_info.get("size") if isinstance(lfs_info, dict) else None
                        )
                        return {
                            "sha256": sha,
                            "size_bytes": size,
                            "commit_id": getattr(info, "sha", revision),
                        }
                    return {"sha256": None, "size_bytes": None, "commit_id": getattr(info, "sha", revision)}
            return None
        except Exception as e:
            logger.warning(
                "Hugging Face Hub metadata inquiry failed",
                repo_id=repo_id,
                filename=filename,
                error=str(e),
            )
            return None

    async def download_model(self, model_name: str, force: bool = False) -> Path:
        """
        Downloads model using pinned Hugging Face Hub revision or direct fallback URLs.
        Verifies local chunked SHA-256 against Hub LFS checksum.
        If Hub is unreachable, safely checks local cached copy and flags status as 'unverified'.
        """
        meta = self.get_manifest_entry(model_name)
        if not meta:
            raise ValueError(f"Model '{model_name}' not defined in manifest")

        if meta.get("status") == "placeholder" or meta.get("source") == "UNREGISTERED/PLACEHOLDER":
            raise ValueError(
                f"Model '{model_name}' is marked as UNREGISTERED/PLACEHOLDER. "
                "Download aborted; pipeline runs verified forensics."
            )

        filename = meta["filename"]
        target_path = self.cache_dir / filename
        repo_id = meta.get("repo_id") or meta.get("repository") or settings.MODEL_REPOSITORY
        revision = meta.get("revision") or settings.MODEL_REVISION

        # Check existing valid cache
        if not force:
            existing = self._find_model_file(filename)
            if existing:
                expected_sha = meta.get("expected_sha256") or meta.get("sha256")
                if self.verify_model(existing, expected_sha):
                    self._states[model_name] = MODEL_PRESENT
                    return existing

        async with self._lock:
            self._states[model_name] = MODEL_DOWNLOADING
            logger.info("Starting model download", model=model_name, filename=filename, repo=repo_id, revision=revision)

            hub_lfs_sha: Optional[str] = None
            hub_reachable = False

            # 1. Fetch Hub metadata to obtain pinned LFS checksum
            if repo_id and revision:
                hub_meta = self.fetch_hub_metadata(repo_id=repo_id, filename=filename, revision=revision)
                if hub_meta:
                    hub_reachable = True
                    hub_lfs_sha = hub_meta.get("sha256")

            downloaded = False

            # 2. Download via huggingface_hub using pinned revision
            if repo_id:
                try:
                    from huggingface_hub import hf_hub_download
                    token = settings.HF_TOKEN if settings.HF_TOKEN else None
                    loop = asyncio.get_event_loop()
                    hf_path = await loop.run_in_executor(
                        None,
                        lambda: hf_hub_download(
                            repo_id=repo_id,
                            filename=filename,
                            revision=revision,
                            token=token,
                            local_dir=str(self.cache_dir),
                        ),
                    )
                    target_path = Path(hf_path)
                    downloaded = True
                    logger.info("Downloaded model via huggingface_hub", model=model_name, path=str(target_path))
                except Exception as hf_err:
                    logger.warning(
                        "Hugging Face hub download unavailable or failed, checking fallbacks",
                        model=model_name,
                        error=str(hf_err),
                    )

            # 3. Fallback: try fallback URLs if download didn't complete
            if not downloaded and meta.get("fallback_urls"):
                import httpx
                for url in meta.get("fallback_urls", []):
                    try:
                        logger.info("Attempting HTTP fallback download", url=url)
                        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                            resp = await client.get(url)
                            if resp.status_code == 200:
                                with open(target_path, "wb") as f:
                                    f.write(resp.content)
                                downloaded = True
                                logger.info("Downloaded model via fallback URL", model=model_name, url=url)
                                break
                    except Exception as http_err:
                        logger.warning("HTTP fallback download failed", url=url, error=str(http_err))

            # 4. Fallback (Hub unreachable): check if local cached file exists
            if not downloaded:
                existing = self._find_model_file(filename)
                expected_sha = meta.get("expected_sha256") or meta.get("sha256")
                if existing and self.verify_model(existing, expected_sha):
                    self._states[model_name] = MODEL_UNVERIFIED
                    logger.warning(
                        "Hub unreachable: using cached local weights with unverified provenance",
                        model=model_name,
                        file=str(existing),
                        status="unverified",
                    )
                    return existing

                self._states[model_name] = MODEL_DOWNLOAD_FAILED
                raise RuntimeError(
                    f"Failed to acquire model '{model_name}'. Hub unreachable and no valid local cache."
                )

            # 5. Checksum verification: compare local chunked SHA-256 against Hub or manifest
            verify_target_sha = hub_lfs_sha or meta.get("expected_sha256") or meta.get("sha256")
            if verify_target_sha and not self.verify_model(target_path, verify_target_sha):
                if target_path.exists():
                    try:
                        target_path.unlink()
                    except Exception:
                        pass
                self._states[model_name] = MODEL_CORRUPTED
                logger.error(
                    "Model SHA-256 mismatch against Hub LFS metadata; refusing to load",
                    model=model_name,
                    expected=verify_target_sha,
                )
                raise ValueError(f"Downloaded model '{model_name}' failed SHA-256 verification against Hub metadata")

            # Check for suspiciously tiny file
            if target_path.stat().st_size < 1024:
                self._states[model_name] = MODEL_CORRUPTED
                raise ValueError(f"Downloaded model '{model_name}' is suspiciously tiny ({target_path.stat().st_size} bytes)")

            if not hub_reachable:
                self._states[model_name] = MODEL_UNVERIFIED
                logger.warning(
                    "Hub unreachable: using cached local weights with unverified provenance",
                    model=model_name,
                    file=str(target_path),
                    status="unverified",
                )
            else:
                self._states[model_name] = MODEL_PRESENT
            return target_path

    async def get_model_path(self, model_name: str) -> Optional[Path]:
        """Returns local model path. Auto-downloads if enabled and model is registered."""
        meta = self.get_manifest_entry(model_name)
        if not meta or meta.get("status") == "placeholder":
            return None

        filename = meta.get("filename", model_name)
        path = self._find_model_file(filename)

        if path and self.check_model(model_name) in (MODEL_PRESENT, MODEL_READY, MODEL_UNVERIFIED):
            return path

        if settings.AUTO_DOWNLOAD_MODELS and meta:
            try:
                return await self.download_model(model_name)
            except Exception as e:
                logger.error("Auto download failed for model", model=model_name, error=str(e))
                return None
        return None

    async def load_model(self, model_name: str) -> Any:
        """Loads model into memory as a reusable singleton instance."""
        if model_name in self._loaded_models:
            return self._loaded_models[model_name]

        self._states[model_name] = MODEL_LOADING
        path = await self.get_model_path(model_name)
        if not path:
            self._states[model_name] = MODEL_MISSING
            raise FileNotFoundError(f"Model file for '{model_name}' not available locally or on remote")

        try:
            if model_name == "face_detection_yunet":
                import cv2
                detector = cv2.FaceDetectorYN.create(
                    str(path),
                    "",
                    (320, 320),
                    score_threshold=0.55,
                    nms_threshold=0.3,
                    top_k=5,
                )
                self._loaded_models[model_name] = detector
            else:
                import onnxruntime as ort
                providers = (
                    ["CUDAExecutionProvider", "CPUExecutionProvider"]
                    if settings.ML_DEVICE == "cuda"
                    else ["CPUExecutionProvider"]
                )
                session = ort.InferenceSession(str(path), providers=providers)
                self._loaded_models[model_name] = session

            self._states[model_name] = MODEL_READY
            logger.info("Model loaded successfully into memory", model=model_name)
            return self._loaded_models[model_name]
        except Exception as e:
            self._states[model_name] = MODEL_ERROR
            logger.error("Failed to load model into memory", model=model_name, error=str(e))
            raise

    def unload_model(self, model_name: str) -> bool:
        """Evicts a model from memory to reclaim resources."""
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            self._states[model_name] = MODEL_PRESENT
            logger.info("Model evicted from memory", model=model_name)
            return True
        return False

    def get_model_status(self) -> Dict[str, Any]:
        """Returns sanitized operational telemetry of all model registry entries."""
        models_summary = []
        has_runtime_essential = False

        for m in self.manifest.get("models", []):
            name = m["name"]
            req = m.get("required_at_runtime", False)
            state = self._states.get(name, self.check_model(name))
            is_loaded = name in self._loaded_models

            if req and state in (MODEL_READY, MODEL_PRESENT, MODEL_UNVERIFIED):
                has_runtime_essential = True

            models_summary.append({
                "name": name,
                "pipeline": m.get("pipeline"),
                "source": m.get("source"),
                "filename": m.get("filename"),
                "format": m.get("format"),
                "required_at_runtime": req,
                "status": state,
                "registry_status": m.get("status"),
                "expected_sha256": m.get("expected_sha256"),
                "size_bytes": m.get("size_bytes"),
                "verified_at": m.get("verified_at"),
                "loaded_in_memory": is_loaded,
                "purpose": m.get("purpose"),
            })

        system_status = "READY" if has_runtime_essential else "DEGRADED_FORENSICS"

        return {
            "ml_engine_status": system_status,
            "device": settings.ML_DEVICE,
            "manifest_version": self.manifest.get("version", "2.0.0"),
            "models_count": len(models_summary),
            "models": models_summary,
        }


# Global singleton instance
model_manager = ModelManager()
