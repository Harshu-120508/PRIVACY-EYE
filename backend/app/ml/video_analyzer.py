"""
Video Analyzer — frame-sampled temporal consistency, landmark stability, and DCT compression seams.
Seamlessly blends deep temporal neural inference (ONNX) with OpenCV temporal forensics.
"""
from pathlib import Path
from typing import Optional, List, Tuple
import os
import tempfile
import numpy as np
import cv2
import structlog

from app.core.config import settings
from app.ml.forensics import forensics_analyze_video, _score_to_risk

logger = structlog.get_logger(__name__)

try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except Exception:
    HAS_FACE_RECOGNITION = False


def _find_video_weights_path() -> Optional[Path]:
    candidates = [
        Path(settings.ML_MODELS_DIR) / "video_efficientnet_temporal.onnx",
        Path(settings.MODEL_CACHE_DIR) / "video_efficientnet_temporal.onnx",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


class VideoAnalyzer:
    """
    Video manipulation detector combining:
    1. Temporal inter-frame variance and smoothness anomalies
    2. 8x8 DCT compression block boundary seams
    3. Inter-frame brightness and illumination flicker
    4. face_recognition (dlib 128-d encodings) inter-frame identity stability and jitter detection
    5. Multi-frame neural ONNX inference when weights are downloaded
    """

    def __init__(self):
        self.session = None
        self.input_name = None
        self.input_shape = None
        weights_path = _find_video_weights_path()
        if weights_path:
            try:
                import onnxruntime as ort
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if settings.ML_DEVICE == "cuda" else ["CPUExecutionProvider"]
                self.session = ort.InferenceSession(str(weights_path), providers=providers)
                inp = self.session.get_inputs()[0]
                self.input_name = inp.name
                self.input_shape = inp.shape
                logger.info("VideoAnalyzer loaded ONNX weights", path=str(weights_path), input_shape=self.input_shape)
            except Exception as e:
                logger.warning("Could not initialize video ONNX session", error=str(e))
        else:
            logger.info("VideoAnalyzer running temporal forensics with face_recognition", has_face_recognition=HAS_FACE_RECOGNITION)

    def sample_frames(self, data: bytes, max_samples: int = 16) -> List[np.ndarray]:
        """Extract equidistant keyframes from video bytes using OpenCV."""
        frames: List[np.ndarray] = []
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(data)
            tmp_path = f.name

        try:
            cap = cv2.VideoCapture(tmp_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count <= 0:
                # Fallback: read sequentially if frame count property is unavailable
                while len(frames) < max_samples:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    frames.append(frame)
            else:
                sample_indices = np.linspace(0, max(frame_count - 1, 0), min(max_samples, frame_count), dtype=int)
                for idx in sample_indices:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        frames.append(frame)
            cap.release()
        except Exception as e:
            logger.warning("Failed to extract frames for neural video inference", error=str(e))
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

        return frames

    def preprocess_frame(self, frame: np.ndarray, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
        """Resize, color-convert, and ImageNet-normalize a single video frame."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, target_size, interpolation=cv2.INTER_AREA)
        arr = np.array(resized, dtype=np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr = (arr - mean) / std
        return arr.transpose(2, 0, 1)  # (C, H, W)

    def infer_onnx(self, frames: List[np.ndarray]) -> Tuple[float, float]:
        """
        Run multi-frame neural inference.
        Supports both 4D batched frame classifiers and 5D spatio-temporal video models.
        """
        if not frames or self.session is None:
            return 0.10, 0.50

        processed = [self.preprocess_frame(f) for f in frames]
        batch_arr = np.stack(processed, axis=0)  # (N, C, H, W)

        # Adapt input layout based on model definition
        if self.input_shape and len(self.input_shape) == 5:
            # Spatio-temporal model expecting (1, N, C, H, W) or (1, C, N, H, W)
            if self.input_shape[1] in (1, 3):  # Channel dimension is 1
                tensor = batch_arr.transpose(1, 0, 2, 3)[np.newaxis].astype(np.float32)
            else:  # Sequence dimension is 1
                tensor = batch_arr[np.newaxis].astype(np.float32)
        else:
            # 4D batched representation
            tensor = batch_arr.astype(np.float32)

        outputs = self.session.run(None, {self.input_name: tensor})
        raw_out = outputs[0]

        # Extract probability across multi-class softmax or binary sigmoid
        if raw_out.ndim > 1 and raw_out.shape[-1] >= 2:
            exp_scores = np.exp(raw_out - np.max(raw_out, axis=-1, keepdims=True))
            probs = exp_scores[..., 1] / np.sum(exp_scores, axis=-1)
            synthetic_prob = float(np.mean(probs))
        else:
            val = float(np.mean(raw_out))
            synthetic_prob = float(1.0 / (1.0 + np.exp(-val)))

        synthetic_prob = min(max(synthetic_prob, 0.0), 1.0)
        confidence = min(0.94, abs(synthetic_prob - 0.5) * 2 + 0.62)
        return synthetic_prob, confidence

    def analyze_facial_temporal_consistency(self, frames: List[np.ndarray]) -> Optional[dict]:
        """
        Temporal face stability analysis using face_recognition (dlib 128-d encodings).
        Evaluates:
        1. Inter-frame facial identity embedding Euclidean distance stability
        2. Deepfake face-swap identity drift / jitter across sampled frames
        Optimized by scaling frame width to 640px during face localization.
        """
        if not HAS_FACE_RECOGNITION or not frames:
            return None

        tracked_encodings: List[np.ndarray] = []
        frame_detections = 0

        for frame in frames:
            if frame is None or frame.size == 0:
                continue

            h, w = frame.shape[:2]
            if w > 640:
                scale = 640.0 / w
                small_frame = cv2.resize(frame, (640, int(h * scale)), interpolation=cv2.INTER_AREA)
            else:
                scale = 1.0
                small_frame = frame

            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            try:
                boxes = face_recognition.face_locations(rgb_small, number_of_times_to_upsample=0, model="hog")
            except Exception as e:
                logger.warning("Video frame face_locations failed", error=str(e))
                continue

            if not boxes:
                continue

            # Select largest face in frame
            primary_box = max(boxes, key=lambda b: (b[2] - b[0]) * (b[1] - b[3]))
            if scale != 1.0:
                top, right, bottom, left = primary_box
                orig_box = (
                    int(top / scale),
                    int(right / scale),
                    int(bottom / scale),
                    int(left / scale),
                )
            else:
                orig_box = primary_box

            rgb_full = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                encs = face_recognition.face_encodings(rgb_full, [orig_box], num_jitters=1)
                if encs:
                    tracked_encodings.append(encs[0])
                    frame_detections += 1
            except Exception as e:
                logger.warning("Video frame face_encodings failed", error=str(e))

        if len(tracked_encodings) < 2:
            return {
                "faces_tracked_frames": frame_detections,
                "facial_temporal_jitter_score": 0.0,
                "details": f"Faces detected in {frame_detections} frame(s), insufficient temporal pairs.",
            }

        pairwise_distances = []
        for i in range(len(tracked_encodings) - 1):
            dist = float(face_recognition.face_distance([tracked_encodings[i]], tracked_encodings[i + 1])[0])
            pairwise_distances.append(dist)

        mean_dist = float(np.mean(pairwise_distances))
        max_dist = float(np.max(pairwise_distances))
        std_dist = float(np.std(pairwise_distances))

        # Authentic video of same person typically yields mean_dist < 0.32
        # Deepfake face swaps typically yield identity shifts with mean_dist > 0.38 or spikes > 0.55
        if mean_dist > 0.38 or max_dist > 0.55:
            jitter_score = min(1.0, max(0.0, (mean_dist - 0.30) / 0.35 + (max_dist - 0.45) * 0.5))
        else:
            jitter_score = min(0.30, max(0.0, mean_dist * 0.5))

        return {
            "faces_tracked_frames": frame_detections,
            "pairwise_distances": [round(d, 4) for d in pairwise_distances],
            "identity_distance_mean": round(mean_dist, 4),
            "identity_distance_max": round(max_dist, 4),
            "identity_distance_std": round(std_dist, 4),
            "facial_temporal_jitter_score": round(jitter_score, 4),
            "details": (
                f"Tracked facial identity across {frame_detections} keyframes. "
                f"Mean identity encoding distance: {mean_dist:.3f}, max drift: {max_dist:.3f}."
            ),
        }

    def analyze(self, data: bytes, filename: str) -> dict:
        """
        Full video analysis pipeline:
        1. Executes OpenCV temporal forensics (temporal diff, 8x8 DCT blocking, flicker)
        2. Evaluates face_recognition temporal identity embedding stability across keyframes
        3. If neural weights available, runs multi-frame ONNX temporal inference
        4. Fuses forensic, facial, and neural signals with transparent provenance
        """
        forensics = forensics_analyze_video(data, filename)

        frames = self.sample_frames(data) if (HAS_FACE_RECOGNITION or self.session is not None) else []

        face_temporal = None
        if HAS_FACE_RECOGNITION and frames:
            try:
                face_temporal = self.analyze_facial_temporal_consistency(frames)
            except Exception as e:
                logger.warning("Facial temporal consistency analysis error", error=str(e))

        faces_tracked = face_temporal.get("faces_tracked_frames", 0) if face_temporal else 0
        jitter_score = face_temporal.get("facial_temporal_jitter_score", 0.0) if face_temporal else 0.0

        if face_temporal and faces_tracked >= 2:
            forensics.setdefault("provenance", {})["face_recognition_temporal"] = {
                "faces_tracked_frames": faces_tracked,
                "identity_distance_mean": face_temporal.get("identity_distance_mean", 0.0),
                "identity_distance_max": face_temporal.get("identity_distance_max", 0.0),
                "identity_distance_std": face_temporal.get("identity_distance_std", 0.0),
                "jitter_score": jitter_score,
            }
            forensics.setdefault("signals", []).append({
                "key": "facial_identity_temporal_stability",
                "label": "Inter-Frame Facial Identity Stability (face_recognition)",
                "severity": "high" if jitter_score >= 0.60 else "medium" if jitter_score >= 0.35 else "low",
                "score": jitter_score,
                "description": face_temporal.get("details", f"Tracked facial identity across {faces_tracked} frames."),
            })

        if self.session is not None:
            try:
                if frames:
                    neural_prob, neural_conf = self.infer_onnx(frames)
                    forensic_prob = forensics.get("synthetic_probability", 0.10)

                    if faces_tracked >= 2:
                        blended_prob = 0.45 * neural_prob + 0.30 * forensic_prob + 0.25 * jitter_score
                    else:
                        blended_prob = 0.60 * neural_prob + 0.40 * forensic_prob

                    blended_prob = min(max(blended_prob, 0.01), 0.99)
                    risk = _score_to_risk(blended_prob)

                    forensics["risk_level"] = risk
                    forensics["synthetic_probability"] = round(blended_prob, 4)
                    forensics["confidence"] = round(max(neural_conf, forensics.get("confidence", 0.50)), 4)
                    forensics["model_id"] = "privacy-eye-ensemble-video-v1"

                    forensics.setdefault("provenance", {})["neural_model"] = "video_efficientnet_temporal"
                    forensics["provenance"]["neural_probability"] = round(neural_prob, 4)
                    forensics["provenance"]["neural_frames_evaluated"] = len(frames)

                    forensics.setdefault("signals", []).append({
                        "key": "temporal_neural_classifier",
                        "label": "Neural Temporal Inconsistency Evaluation",
                        "severity": "high" if neural_prob >= 0.6 else "medium" if neural_prob >= 0.35 else "low",
                        "score": round(neural_prob, 4),
                        "description": (
                            f"Multi-frame temporal neural network scored {neural_prob:.1%} manipulation likelihood "
                            f"across {len(frames)} sampled frames."
                        ),
                    })
                    return forensics
            except Exception as e:
                logger.warning("ONNX video inference failed, returning forensics", error=str(e))

        if faces_tracked >= 2:
            forensic_prob = forensics.get("synthetic_probability", 0.10)
            blended_prob = 0.65 * forensic_prob + 0.35 * jitter_score
            blended_prob = min(max(blended_prob, 0.01), 0.99)
            risk = _score_to_risk(blended_prob)
            forensics["risk_level"] = risk
            forensics["synthetic_probability"] = round(blended_prob, 4)
            forensics["confidence"] = round(max(0.72, forensics.get("confidence", 0.50)), 4)
            forensics["model_id"] = "privacy-eye-ensemble-video-v1"
            return forensics

        forensics["model_id"] = "privacy-eye-forensics-video-v1"
        return forensics
