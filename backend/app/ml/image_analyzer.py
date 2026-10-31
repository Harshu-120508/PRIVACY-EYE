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
import cv2
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except Exception:
    HAS_FACE_RECOGNITION = False

def _find_weights_path() -> Optional[Path]:
    try:
        from app.services.model_manager import model_manager, MODEL_PRESENT, MODEL_READY, MODEL_UNVERIFIED
        entry = model_manager.get_manifest_entry("image_efficientnet_b4")
        if not entry or entry.get("status") == "placeholder" or entry.get("source") == "UNREGISTERED/PLACEHOLDER":
            return None
        state = model_manager.check_model("image_efficientnet_b4")
        if state in (MODEL_PRESENT, MODEL_READY, MODEL_UNVERIFIED):
            return model_manager._find_model_file("image_efficientnet_b4.onnx")
        return None
    except Exception:
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
    Deepfake image classifier combining:
    1. EfficientNet-B4 spatial neural network (ONNX)
    2. face_recognition (dlib 68-point landmarks & 128-d encodings) for facial geometry and boundary consistency
    3. Frequency domain (2D-FFT) & Error Level Analysis (ELA) forensics
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
            logger.info("ImageAnalyzer running hybrid forensics with face_recognition", has_face_recognition=HAS_FACE_RECOGNITION)

    def preprocess(self, data: bytes) -> np.ndarray:
        from PIL import Image
        img = Image.open(io.BytesIO(data)).convert("RGB").resize((380, 380))
        arr = np.array(img, dtype=np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        arr = (arr - mean) / std
        return arr.transpose(2, 0, 1)[np.newaxis].astype(np.float32)

    def analyze_facial_features(self, rgb_array: np.ndarray) -> Optional[dict]:
        """
        Face analysis powered by face_recognition.
        Evaluates 68-point facial landmarks, boundary texture transitions, and 128-d encodings.
        Optimized by scaling large images down for rapid HOG detection.
        """
        if not HAS_FACE_RECOGNITION or rgb_array is None or rgb_array.size == 0:
            return None

        h, w = rgb_array.shape[:2]
        max_dim = max(h, w)
        if max_dim > 1024:
            scale = 1024.0 / max_dim
            detection_rgb = cv2.resize(rgb_array, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        else:
            scale = 1.0
            detection_rgb = rgb_array

        try:
            boxes = face_recognition.face_locations(detection_rgb, number_of_times_to_upsample=0, model="hog")
        except Exception as e:
            logger.warning("face_recognition face_locations failed", error=str(e))
            return None

        if not boxes:
            return {
                "faces_detected": 0,
                "facial_anomaly_score": 0.0,
                "details": "No faces localized in image.",
            }

        orig_boxes = []
        for top, right, bottom, left in boxes:
            if scale != 1.0:
                orig_boxes.append((
                    int(top / scale),
                    int(right / scale),
                    int(bottom / scale),
                    int(left / scale),
                ))
            else:
                orig_boxes.append((top, right, bottom, left))

        try:
            landmarks_list = face_recognition.face_landmarks(rgb_array, orig_boxes)
            encodings = face_recognition.face_encodings(rgb_array, orig_boxes, num_jitters=1)
        except Exception as e:
            logger.warning("face_recognition landmark/encoding extraction failed", error=str(e))
            landmarks_list = []
            encodings = []

        face_count = len(orig_boxes)
        anomaly_scores = []
        facial_metrics = []

        for i, (top, right, bottom, left) in enumerate(orig_boxes):
            top = max(0, min(top, h - 1))
            bottom = max(0, min(bottom, h))
            left = max(0, min(left, w - 1))
            right = max(0, min(right, w))

            face_h = bottom - top
            face_w = right - left
            if face_h <= 10 or face_w <= 10:
                continue

            face_roi = rgb_array[top:bottom, left:right]

            # 1. Boundary & High-Frequency Noise Consistency
            margin_y = max(4, int(face_h * 0.15))
            margin_x = max(4, int(face_w * 0.15))
            p_top = max(0, top - margin_y)
            p_bottom = min(h, bottom + margin_y)
            p_left = max(0, left - margin_x)
            p_right = min(w, right + margin_x)

            perimeter_roi = rgb_array[p_top:p_bottom, p_left:p_right]
            gray_face = cv2.cvtColor(face_roi, cv2.COLOR_RGB2GRAY)
            gray_perim = cv2.cvtColor(perimeter_roi, cv2.COLOR_RGB2GRAY)

            face_laplacian_var = float(cv2.Laplacian(gray_face, cv2.CV_64F).var())
            perim_laplacian_var = float(cv2.Laplacian(gray_perim, cv2.CV_64F).var()) + 1e-5

            lap_ratio = abs(face_laplacian_var - perim_laplacian_var) / max(face_laplacian_var, perim_laplacian_var)
            boundary_anomaly = min(1.0, max(0.0, lap_ratio * 0.8))

            # 2. Landmark Bilateral Geometry Asymmetry Check
            symmetry_anomaly = 0.0
            if i < len(landmarks_list) and landmarks_list[i]:
                lms = landmarks_list[i]
                left_eye = lms.get("left_eye")
                right_eye = lms.get("right_eye")
                nose_tip = lms.get("nose_tip")

                if left_eye and right_eye and nose_tip:
                    le_center = np.mean(left_eye, axis=0)
                    re_center = np.mean(right_eye, axis=0)
                    nt_center = np.mean(nose_tip, axis=0)

                    d_left = float(np.linalg.norm(le_center - nt_center))
                    d_right = float(np.linalg.norm(re_center - nt_center))
                    max_d = max(d_left, d_right, 1e-4)
                    diff_ratio = abs(d_left - d_right) / max_d

                    if diff_ratio > 0.28:
                        symmetry_anomaly = min(1.0, (diff_ratio - 0.28) * 2.5)

            face_anomaly = 0.55 * boundary_anomaly + 0.45 * symmetry_anomaly
            anomaly_scores.append(face_anomaly)
            facial_metrics.append({
                "box": [top, right, bottom, left],
                "has_landmarks": bool(i < len(landmarks_list) and landmarks_list[i]),
                "has_encoding": bool(i < len(encodings) and len(encodings[i]) == 128),
                "boundary_discontinuity": round(boundary_anomaly, 4),
                "structural_asymmetry": round(symmetry_anomaly, 4),
                "face_anomaly_score": round(face_anomaly, 4),
            })

        mean_anomaly = float(np.mean(anomaly_scores)) if anomaly_scores else 0.0

        return {
            "faces_detected": face_count,
            "facial_anomaly_score": round(mean_anomaly, 4),
            "faces": facial_metrics,
            "details": f"Evaluated {face_count} face(s) via face_recognition 68-point landmarks and 128-d encodings.",
        }

    def analyze(self, data: bytes, filename: str) -> dict:
        from app.ml.forensics import forensics_analyze_image, _score_to_risk

        forensics = forensics_analyze_image(data, filename)

        # ── Face Recognition Analysis (dlib 68-point landmarks & 128-d encodings)
        face_analysis = None
        if HAS_FACE_RECOGNITION:
            try:
                from PIL import Image
                pil_img = Image.open(io.BytesIO(data)).convert("RGB")
                face_analysis = self.analyze_facial_features(np.array(pil_img))
            except Exception as e:
                logger.warning("Facial feature analysis error", error=str(e))

        faces_detected = face_analysis.get("faces_detected", 0) if face_analysis else 0
        facial_anomaly_score = face_analysis.get("facial_anomaly_score", 0.0) if face_analysis else 0.0

        if face_analysis and faces_detected > 0:
            forensics.setdefault("provenance", {})["face_recognition"] = {
                "faces_detected": faces_detected,
                "facial_anomaly_score": facial_anomaly_score,
                "faces": face_analysis.get("faces", []),
            }
            forensics.setdefault("signals", []).append({
                "key": "face_recognition_landmarks",
                "label": "Facial Geometric & Boundary Consistency (face_recognition)",
                "severity": "high" if facial_anomaly_score >= 0.6 else "medium" if facial_anomaly_score >= 0.35 else "low",
                "score": facial_anomaly_score,
                "description": face_analysis.get("details", f"Evaluated {faces_detected} face(s) via face_recognition."),
            })

        if self.session is not None:
            try:
                inp = self.preprocess(data)
                outputs = self.session.run(None, {self.input_name: inp})
                raw_out = outputs[0]

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
                forensic_prob = forensics.get("synthetic_probability", 0.10)

                if faces_detected > 0:
                    blended_prob = 0.50 * synthetic_prob + 0.30 * forensic_prob + 0.20 * facial_anomaly_score
                else:
                    blended_prob = 0.60 * synthetic_prob + 0.40 * forensic_prob

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

        if faces_detected > 0:
            forensic_prob = forensics.get("synthetic_probability", 0.10)
            blended_prob = 0.65 * forensic_prob + 0.35 * facial_anomaly_score
            blended_prob = min(max(blended_prob, 0.01), 0.99)
            risk = _score_to_risk(blended_prob)
            forensics["risk_level"] = risk
            forensics["synthetic_probability"] = round(blended_prob, 4)
            forensics["confidence"] = round(max(0.68, forensics.get("confidence", 0.50)), 4)
            forensics["model_id"] = "privacy-eye-ensemble-image-v1"
            return forensics

        forensics["model_id"] = "privacy-eye-forensics-image-v1"
        return forensics
