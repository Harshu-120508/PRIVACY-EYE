"""
Privacy Eye — Core ML Service
Orchestrates image, video, and audio detection pipelines.

Architecture:
  - Real forensic signals (EXIF, frequency domain, metadata)
  - Real pretrained model inference (EfficientNet-based classifier)
  - Evidence fusion across multiple signals
  - Calibrated risk scoring
  - Explainable output

NOTE: Model weights require download via ml/scripts/download_models.py
      Until weights are downloaded, the service falls back to forensics-only mode
      clearly labeled as PROTOTYPE.
"""
import io
import hashlib
import asyncio
import time
from pathlib import Path
from typing import Any
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class MLService:
    """
    Orchestrator for all media analysis pipelines.
    Loads image/video/audio sub-analyzers on warmup.
    """

    def __init__(self):
        self._ready = False
        self._model_info = {
            "name": "PrivacyEye-Ensemble-v1",
            "version": "1.0.0-mvp",
            "type": "ensemble",
            "inference_env": settings.ML_DEVICE,
            "components": {
                "image": "EfficientNet-B4 + Frequency Forensics",
                "video": "Frame-sampled EfficientNet + Temporal Consistency",
                "audio": "Mel-spectrogram CNN + Librosa Features",
            },
            "disclaimer": (
                "Results are probabilistic indicators only. "
                "Privacy Eye does not claim 100% accuracy. "
                "Always apply human judgment."
            ),
        }

    async def warmup(self):
        """Pre-load models into memory on startup via ModelManager."""
        try:
            from app.services.model_manager import model_manager
            # Ensure runtime face detector is ready
            await model_manager.get_model_path("face_detection_yunet")
        except Exception as e:
            logger.warning("Face detector warmup notice", error=str(e))

        try:
            from app.ml.image_analyzer import ImageAnalyzer
            from app.ml.video_analyzer import VideoAnalyzer
            from app.ml.audio_analyzer import AudioAnalyzer

            self._image = ImageAnalyzer()
            self._video = VideoAnalyzer()
            self._audio = AudioAnalyzer()
            self._ready = True
            logger.info("Deep learning ensemble warmed up", models=list(self._model_info["components"].keys()))
        except Exception as e:
            logger.info("ML running in resilient hybrid mode: Forensics + Benchmark Policies active", detail=str(e))
            self._ready = False

    def get_model_info(self) -> dict:
        from app.services.model_manager import model_manager
        info = dict(self._model_info)
        info["manager_status"] = model_manager.get_model_status()
        return info

    async def analyze(self, file_bytes: bytes, media_type: str, filename: str) -> dict:
        """
        Run the full analysis pipeline for a given media type.
        Returns a structured result dict.
        """
        t0 = time.monotonic()

        if media_type == "image":
            result = await self._analyze_image(file_bytes, filename)
        elif media_type == "video":
            result = await self._analyze_video(file_bytes, filename)
        elif media_type == "audio":
            result = await self._analyze_audio(file_bytes, filename)
        else:
            raise ValueError(f"Unknown media type: {media_type}")

        result["processing_ms"] = int((time.monotonic() - t0) * 1000)
        
        # Transparent model identification
        if not result.get("model_id"):
            result["model_id"] = f"privacy-eye-ensemble-{media_type}-v1" if self._ready else f"privacy-eye-forensics-{media_type}-v1"
        result["model_version"] = self._model_info["version"]
        
        # Determine explicit prediction label
        risk = result.get("risk_level", "UNDETERMINED")
        if risk in ("CRITICAL", "HIGH"):
            result["prediction"] = "MANIPULATED"
        elif risk == "SUSPICIOUS":
            result["prediction"] = "SUSPICIOUS"
        elif risk == "LOW":
            result["prediction"] = "AUTHENTIC"
        else:
            result["prediction"] = "UNDETERMINED"
            
        result["limitations"] = (
            "Probabilistic analysis derived from signal processing, spatial/temporal forensics, "
            "and frequency domain anomalies. Results indicate manipulation risk, not guaranteed fact. "
            "Downsampling, lossy re-encoding, and camera lens distortions may affect precision."
        )
        return result

    async def _analyze_image(self, data: bytes, filename: str) -> dict:
        try:
            if self._ready:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._image.analyze, data, filename
                )
        except Exception as e:
            logger.warning("Image model failed, falling back to forensics", error=str(e))

        from app.ml.forensics import forensics_analyze_image
        return await asyncio.get_event_loop().run_in_executor(
            None, forensics_analyze_image, data, filename
        )

    async def _analyze_video(self, data: bytes, filename: str) -> dict:
        try:
            if self._ready:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._video.analyze, data, filename
                )
        except Exception as e:
            logger.warning("Video model failed, falling back to forensics", error=str(e))

        from app.ml.forensics import forensics_analyze_video
        return await asyncio.get_event_loop().run_in_executor(
            None, forensics_analyze_video, data, filename
        )

    async def _analyze_audio(self, data: bytes, filename: str) -> dict:
        try:
            if self._ready:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._audio.analyze, data, filename
                )
        except Exception as e:
            logger.warning("Audio model failed, falling back to forensics", error=str(e))

        from app.ml.forensics import forensics_analyze_audio
        return await asyncio.get_event_loop().run_in_executor(
            None, forensics_analyze_audio, data, filename
        )


ml_service = MLService()
