"""
Audio Analyzer — Wav2Vec2 voice clone detection + Mel-spectrogram & pitch forensics.
Seamlessly blends deep acoustic neural inference (ONNX) with Librosa spectral forensics.
"""
from pathlib import Path
from typing import Optional, Tuple
import io
import numpy as np
import structlog

from app.core.config import settings
from app.ml.forensics import forensics_analyze_audio, _score_to_risk

logger = structlog.get_logger(__name__)


def _find_audio_weights_path() -> Optional[Path]:
    candidates = [
        Path(settings.ML_MODELS_DIR) / "audio_wav2vec2_clone.onnx",
        Path(settings.MODEL_CACHE_DIR) / "audio_wav2vec2_clone.onnx",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


class AudioAnalyzer:
    """
    Audio manipulation and synthetic voice detector combining:
    1. Spectral flatness and noise-like spectrum identification
    2. Mel-spectrogram variance and low-dispersion TTS patterns
    3. Pitch stability and synthetic pitch quantization
    4. Zero-crossing rate distribution
    5. Neural voice-clone ONNX model inference when weights are downloaded
    """

    def __init__(self):
        self.session = None
        self.input_name = None
        self.input_shape = None
        weights_path = _find_audio_weights_path()
        if weights_path:
            try:
                import onnxruntime as ort
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if settings.ML_DEVICE == "cuda" else ["CPUExecutionProvider"]
                self.session = ort.InferenceSession(str(weights_path), providers=providers)
                inp = self.session.get_inputs()[0]
                self.input_name = inp.name
                self.input_shape = inp.shape
                logger.info("AudioAnalyzer loaded ONNX weights", path=str(weights_path), input_shape=self.input_shape)
            except Exception as e:
                logger.warning("Could not initialize audio ONNX session", error=str(e))
        else:
            logger.info("AudioAnalyzer running verified acoustic signal forensics (ONNX weights not present)")

    def load_audio(self, data: bytes, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
        """Load audio payload with multi-tier fallback (librosa -> soundfile -> wave)."""
        audio_io = io.BytesIO(data)

        # 1. Try librosa if available
        try:
            import librosa
            y, sr = librosa.load(audio_io, sr=target_sr, mono=True, duration=60.0)
            return y.astype(np.float32), sr
        except Exception:
            pass

        # 2. Try soundfile if available
        try:
            import soundfile as sf
            audio_io.seek(0)
            y_sf, sr = sf.read(audio_io, dtype="float32", always_2d=False)
            y = y_sf if y_sf.ndim == 1 else y_sf.mean(axis=1)
            return y.astype(np.float32), sr
        except Exception:
            pass

        # 3. Standard library wave fallback (works in all Python environments)
        import wave
        audio_io.seek(0)
        with wave.open(audio_io, "rb") as wf:
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            sr = wf.getframerate()
            frames = wf.readframes(wf.getnframes())

            if sampwidth == 2:
                raw_int = np.frombuffer(frames, dtype=np.int16)
                y = raw_int.astype(np.float32) / 32768.0
            elif sampwidth == 1:
                raw_int = np.frombuffer(frames, dtype=np.uint8)
                y = (raw_int.astype(np.float32) - 128.0) / 128.0
            elif sampwidth == 4:
                raw_int = np.frombuffer(frames, dtype=np.int32)
                y = raw_int.astype(np.float32) / 2147483648.0
            else:
                y = np.frombuffer(frames, dtype=np.float32)

            if channels > 1:
                y = y.reshape(-1, channels).mean(axis=1)

            return y.astype(np.float32), sr

    def preprocess_audio(self, y: np.ndarray, sr: int = 16000) -> np.ndarray:
        """
        Preprocess audio into the expected input tensor format.
        Supports both raw waveform inputs and 2D Log-Mel spectrogram matrices.
        """
        # Normalize waveform amplitude
        max_abs = float(np.max(np.abs(y))) if len(y) > 0 else 1.0
        y_norm = y / (max_abs + 1e-7)

        # Inspect input shape if known
        if self.input_shape and len(self.input_shape) >= 3:
            try:
                import librosa
                mel = librosa.feature.melspectrogram(y=y_norm, sr=sr, n_mels=80, n_fft=1024, hop_length=512)
                mel_db = librosa.power_to_db(mel, ref=np.max)
                std = float(mel_db.std())
                mel_norm = (mel_db - mel_db.mean()) / (std + 1e-6)
            except Exception:
                # Fast numpy FFT spectrogram fallback
                n_fft = 512
                hop = 256
                n_samples = len(y_norm)
                if n_samples < n_fft:
                    padded = np.pad(y_norm, (0, n_fft - n_samples))
                else:
                    padded = y_norm
                num_frames = max(1, (len(padded) - n_fft) // hop + 1)
                stride_frames = np.lib.stride_tricks.sliding_window_view(padded[:(num_frames - 1) * hop + n_fft], n_fft)[::hop]
                fft_mag = np.abs(np.fft.rfft(stride_frames, n=n_fft))
                mel_norm = fft_mag.T[:80, :] if fft_mag.T.shape[0] >= 80 else np.pad(fft_mag.T, ((0, 80 - fft_mag.T.shape[0]), (0, 0)))
                mel_norm = (mel_norm - mel_norm.mean()) / (mel_norm.std() + 1e-6)

            if len(self.input_shape) == 4:
                return mel_norm[np.newaxis, np.newaxis, ...].astype(np.float32)
            return mel_norm[np.newaxis, ...].astype(np.float32)

        # Default raw waveform representation (e.g. Wav2Vec2/RawNet: 1, sequence_length)
        target_len = 48000
        if len(y_norm) < target_len:
            pad_width = target_len - len(y_norm)
            y_padded = np.pad(y_norm, (0, pad_width), mode="constant")
        else:
            y_padded = y_norm[:target_len]

        return y_padded[np.newaxis, :].astype(np.float32)

    def infer_onnx(self, audio_tensor: np.ndarray) -> Tuple[float, float]:
        """Run neural voice-clone inference via ONNX session."""
        if self.session is None:
            return 0.08, 0.50

        outputs = self.session.run(None, {self.input_name: audio_tensor})
        raw_out = outputs[0]

        # Extract probability across multi-class softmax or binary sigmoid
        if raw_out.ndim > 1 and raw_out.shape[-1] >= 2:
            logits = raw_out[0] if raw_out.ndim == 2 else raw_out.flatten()
            exp_scores = np.exp(logits - np.max(logits))
            probs = exp_scores / np.sum(exp_scores)
            synthetic_prob = float(probs[1])
        else:
            val = float(raw_out.flatten()[0])
            synthetic_prob = float(1.0 / (1.0 + np.exp(-val)))

        synthetic_prob = min(max(synthetic_prob, 0.0), 1.0)
        confidence = min(0.93, abs(synthetic_prob - 0.5) * 2 + 0.62)
        return synthetic_prob, confidence

    def analyze(self, data: bytes, filename: str) -> dict:
        """
        Full audio analysis pipeline:
        1. Executes Librosa acoustic forensics (spectral flatness, mel variance, ZCR, pause timing)
        2. If neural weights available, runs ONNX voice-clone inference
        3. Fuses acoustic and neural signals with transparent provenance
        """
        forensics = forensics_analyze_audio(data, filename)

        if self.session is not None:
            try:
                y, sr = self.load_audio(data)
                audio_tensor = self.preprocess_audio(y, sr)
                neural_prob, neural_conf = self.infer_onnx(audio_tensor)
                forensic_prob = forensics.get("synthetic_probability", 0.08)

                # Evidence fusion: 60% neural acoustic model + 40% spectral forensics
                blended_prob = 0.60 * neural_prob + 0.40 * forensic_prob
                blended_prob = min(max(blended_prob, 0.01), 0.99)
                risk = _score_to_risk(blended_prob)

                forensics["risk_level"] = risk
                forensics["synthetic_probability"] = round(blended_prob, 4)
                forensics["confidence"] = round(max(neural_conf, forensics.get("confidence", 0.50)), 4)
                forensics["model_id"] = "privacy-eye-ensemble-audio-v1"

                forensics.setdefault("provenance", {})["neural_model"] = "audio_wav2vec2_clone"
                forensics["provenance"]["neural_probability"] = round(neural_prob, 4)

                forensics.setdefault("signals", []).append({
                    "key": "neural_voice_clone_discriminator",
                    "label": "Neural Voice Clone Classification",
                    "severity": "high" if neural_prob >= 0.6 else "medium" if neural_prob >= 0.35 else "low",
                    "score": round(neural_prob, 4),
                    "description": f"Neural acoustic model scored {neural_prob:.1%} synthetic voice / TTS clone likelihood.",
                })
                return forensics
            except Exception as e:
                logger.warning("ONNX audio inference failed, returning forensics", error=str(e))

        forensics["model_id"] = "privacy-eye-forensics-audio-v1"
        return forensics
