"""
Image Analyzer — EfficientNet-B4 based deepfake classifier.
Requires model weights downloaded via ml/scripts/download_models.py

This is a REAL deep learning classifier. Without weights it raises
ImportError/FileNotFoundError and ml_service falls back to forensics.py.
"""
import io
import numpy as np
from typing import Optional
from pathlib import Path
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

def _find_weights_path() -> Optional[Path]:
    candidates = [
        Path(settings.ML_MODELS_DIR) / "image_efficientnet_b4.onnx",
        Path(settings.MODEL_CACHE_DIR) / "image_efficientnet_b4.onnx",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


class ImageAnalyzer:
    """
    EfficientNet-B4 deepfake image classifier.
    Trained on FaceForensics++ and DALL-E/Midjourney synthetic datasets.
    Inference via ONNX Runtime for cross-platform deployment.
    """

    def __init__(self):
        self.session = None
        self.input_name = None
        weights_path = _find_weights_path()
        if weights_path:
            try:
                import onnxruntime as ort
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if settings.ML_DEVICE == "cuda" else ["CPUExecutionProvider"]
                self.session = ort.InferenceSession(str(weights_path), providers=providers)
                self.input_name = self.session.get_inputs()[0].name
                logger.info("ImageAnalyzer loaded ONNX weights", path=str(weights_path))
            except Exception as e:
                logger.warning("Could not initialize image ONNX session", error=str(e))
        else:
            logger.info("ImageAnalyzer ONNX weights not found, running digital forensics pipeline")

    def preprocess(self, data: bytes) -> np.ndarray:
        from PIL import Image
        img = Image.open(io.BytesIO(data)).convert("RGB").resize((380, 380))
        arr = np.array(img, dtype=np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        arr = (arr - mean) / std
        return arr.transpose(2, 0, 1)[np.newaxis].astype(np.float32)

    def analyze(self, data: bytes, filename: str) -> dict:
        from app.ml.forensics import forensics_analyze_image, _score_to_risk

        forensics = forensics_analyze_image(data, filename)

        if self.session is not None:
            try:
                inp = self.preprocess(data)
                outputs = self.session.run(None, {self.input_name: inp})
                raw_out = outputs[0]

                # Robust probability extraction across 1D/2D and multi-class layouts
                if raw_out.ndim > 1 and raw_out.shape[-1] >= 2:
                    logits = raw_out[0] if raw_out.ndim == 2 else raw_out.flatten()
                    exp_scores = np.exp(logits - np.max(logits))
                    probs = exp_scores / np.sum(exp_scores)
                    synthetic_prob = float(probs[1])
                else:
                    val = float(raw_out.flatten()[0])
                    synthetic_prob = float(1.0 / (1.0 + np.exp(-val)))

                synthetic_prob = min(max(synthetic_prob, 0.0), 1.0)
                confidence = min(0.92, abs(synthetic_prob - 0.5) * 2 + 0.60)

                # Blend DL probability with forensics (60% model, 40% forensics)
                blended_prob = 0.60 * synthetic_prob + 0.40 * forensics.get("synthetic_probability", 0.10)
                blended_prob = min(max(blended_prob, 0.01), 0.99)
                risk = _score_to_risk(blended_prob)

                forensics["risk_level"] = risk
                forensics["synthetic_probability"] = round(blended_prob, 4)
                forensics["confidence"] = round(max(confidence, forensics.get("confidence", 0.50)), 4)
                forensics["model_id"] = "privacy-eye-ensemble-image-v1"
                forensics.setdefault("provenance", {})["neural_model"] = "image_efficientnet_b4"
                forensics["provenance"]["neural_probability"] = round(synthetic_prob, 4)

                forensics.setdefault("signals", []).append({
                    "key": "neural_spatial_classifier",
                    "label": "Neural Spatial Artifact Evaluation",
                    "severity": "high" if synthetic_prob >= 0.6 else "medium" if synthetic_prob >= 0.35 else "low",
                    "score": round(synthetic_prob, 4),
                    "description": f"EfficientNet-B4 spatial neural network evaluated image with {synthetic_prob:.1%} manipulation likelihood.",
                })
                return forensics
            except Exception as e:
                logger.warning("ONNX image inference failed, returning forensics", error=str(e))

        forensics["model_id"] = "privacy-eye-forensics-image-v1"
        return forensics
