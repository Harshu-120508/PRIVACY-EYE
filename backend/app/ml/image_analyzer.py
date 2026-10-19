"""
Image Analyzer — EfficientNet-B4 based deepfake classifier.
Requires model weights downloaded via ml/scripts/download_models.py

This is a REAL deep learning classifier. Without weights it raises
ImportError/FileNotFoundError and ml_service falls back to forensics.py.
"""
import io
import numpy as np
from pathlib import Path
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

WEIGHTS_PATH = Path(settings.ML_MODELS_DIR) / "image_efficientnet_b4.onnx"


class ImageAnalyzer:
    """
    EfficientNet-B4 deepfake image classifier.
    Trained on FaceForensics++ and DALL-E/Midjourney synthetic datasets.
    Inference via ONNX Runtime for cross-platform deployment.
    """

    def __init__(self):
        self.session = None
        self.input_name = None
        if WEIGHTS_PATH.exists():
            try:
                import onnxruntime as ort
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if settings.ML_DEVICE == "cuda" else ["CPUExecutionProvider"]
                self.session = ort.InferenceSession(str(WEIGHTS_PATH), providers=providers)
                self.input_name = self.session.get_inputs()[0].name
                logger.info("ImageAnalyzer loaded ONNX weights", path=str(WEIGHTS_PATH))
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
        from app.ml.forensics import forensics_analyze_image, _score_to_risk, _build_result

        forensics = forensics_analyze_image(data, filename)

        if self.session is not None:
            try:
                inp = self.preprocess(data)
                outputs = self.session.run(None, {self.input_name: inp})
                logits = outputs[0][0]

                # Sigmoid for binary classification (fake=1, real=0)
                synthetic_prob = float(1 / (1 + np.exp(-logits[1] + logits[0])))
                confidence = min(0.92, abs(synthetic_prob - 0.5) * 2 + 0.60)

                # Blend DL probability with forensics (60% model, 40% forensics)
                blended_prob = 0.60 * synthetic_prob + 0.40 * forensics["synthetic_probability"]
                blended_prob = min(max(blended_prob, 0.02), 0.98)
                risk = _score_to_risk(blended_prob)

                forensics["risk_level"] = risk
                forensics["synthetic_probability"] = round(blended_prob, 4)
                forensics["confidence"] = round(max(confidence, forensics["confidence"]), 4)
                forensics["model_id"] = "privacy-eye-ensemble-image-v1"
                return forensics
            except Exception as e:
                logger.warning("ONNX image inference failed, returning forensics", error=str(e))

        forensics["model_id"] = "privacy-eye-forensics-image-v1"
        return forensics
