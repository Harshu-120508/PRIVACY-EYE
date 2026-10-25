# Privacy Eye — AI Model & Forensic Signal Pipeline

This document details the machine learning and digital forensics pipeline powering Privacy Eye, covering model provenance, algorithmic signal extraction, confidence calibration, limitations, and future training pipeline specifications.

---

## 1. Dual-Mode Architecture Overview

Privacy Eye implements a resilient dual-mode architecture:
1. **Pretrained Neural Inference Mode**: When exported neural network weights (`.onnx`) are present in `backend/weights/`, the engine runs high-throughput deep neural net inference using ONNX Runtime.
2. **Deterministic Digital Signal Forensics Mode**: When neural weights are absent (or during offline/resource-constrained operation), the engine executes rigorous, mathematically proven signal processing algorithms to detect compression seams, spectral anomalies, and temporal jitter.

Fabricated confidence scores or simulated mock timers are strictly prohibited. The system explicitly discloses whether analysis was completed via neural model inference or digital signal forensics.

---

## 2. Modality Specifications

### 2.1 Image Analysis Pipeline

```
Raw Image Bytes (JPEG, PNG, WEBP)
            │
            ▼
[Header & Magic Byte Validation]
            │
            ├──► Neural Path (weights/image_detector.onnx available):
            │       - Resize to 224x224 / 299x299
            │       - Normalize (ImageNet mean & std)
            │       - Run ONNX Runtime session
            │       - Model ID: `privacy-eye-ensemble-image-v1`
            │
            └──► Forensic Path (Default fallback):
                    - 2D-FFT Azimuthal Power Spectrum Analysis (detects GAN periodic grid artifacts)
                    - Error Level Analysis (ELA) with 95% JPEG re-quantization difference
                    - Metadata/C2PA signature inspection
                    - Model ID: `privacy-eye-forensics-image-v1`
```

- **Output Predictions**:
  - `AUTHENTIC`: Low high-frequency anomalies, uniform compression grid.
  - `SUSPICIOUS`: Borderline high-frequency power or localized ELA variance.
  - `MANIPULATED`: Pronounced periodic spectral peaks or high ELA compression difference.
  - `UNDETERMINED`: Resolution below minimum threshold or excessive noise obscuring forensic signals.
- **Model Limitations**:
  - Social media recompression (e.g. WhatsApp, X) suppresses high-frequency forensic artifacts.
  - Heavily downscaled images (< 256x256) lack sufficient spatial resolution for reliable ELA analysis.

---

### 2.2 Video Analysis Pipeline

```
Raw Video Stream (MP4, MOV, WEBM)
            │
            ▼
[OpenCV VideoCapture & Frame Sampler]
            │ (Extracts 10-15 equidistant keyframes)
            │
            ├──► Neural Path (weights/video_detector.onnx available):
            │       - Face detection & alignment per frame
            │       - Sequence embedding (3D-CNN / TimeSformer)
            │       - Model ID: `privacy-eye-ensemble-video-v1`
            │
            └──► Forensic Path (Default fallback):
                    - Temporal Frame Differencing (detects inter-frame flickering & ghosting)
                    - 8x8 Block DCT Grid Inconsistency (detects spliced face boundaries)
                    - Temporal variance standard deviation analysis
                    - Model ID: `privacy-eye-forensics-video-v1`
```

- **Limitations**:
  - High video compression (low bitrate H.264/H.265) introduces natural macroblocking that can elevate false-positive rates for DCT seam analysis.
  - Static videos with minimal movement yield insufficient inter-frame variance.

---

### 2.3 Audio Analysis Pipeline

```
Raw Audio Stream (WAV, MP3, OGG, FLAC)
            │
            ▼
[Librosa Audio Processing (16 kHz Resample)]
            │
            ├──► Neural Path (weights/audio_detector.onnx available):
            │       - Compute Log-Mel / LFCC spectrogram
            │       - AASIST / RawNet2 ONNX classification
            │       - Model ID: `privacy-eye-ensemble-audio-v1`
            │
            └──► Forensic Path (Default fallback):
                    - Short-Time Fourier Transform (STFT)
                    - Mel-Frequency Cepstral Coefficients (MFCC, 13 coefficients)
                    - Pitch Stability (Fundamental Frequency f0 standard deviation via autocorrelation)
                    - Spectral Rolloff & Centroid uniformity (detects vocoder synthesis cutoffs)
                    - Model ID: `privacy-eye-forensics-audio-v1`
```

- **Limitations**:
  - High background acoustic noise or reverberation skews pitch stability metrics.
  - Short clips (< 1.5 seconds) provide inadequate phoneme distribution for vocal tract consistency checks.

---

### 2.4 Real-Time Webcam Liveness & Presentation Attack Defense

- **Face Landmark & Geometric Tracking**: OpenCV `FaceDetectorYN` (YuNet ONNX model, automatically downloaded to `app/ml/weights/face_detection_yunet.onnx`). Tracks 5-point facial landmarks (right eye, left eye, nose tip, right mouth corner, left mouth corner).
- **Ocular Blink Analysis (EAR)**:
  $$EAR = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 \cdot ||p_1 - p_4||}$$
  Natural blinks produce an EAR drop below 0.21 lasting 100–350 ms. Monitored across a non-punitive 30-second rolling window to accommodate natural variance in blink frequency.
- **Screen Replay & Presentation Attack Defense**:
  - **2D-FFT Moiré Frequency Grids**: Detects high-frequency periodic interference fringes characteristic of camera sensors capturing LCD/OLED subpixel grids.
  - **Bezel Boundary Detection**: Hough line transform and rectangular boundary checks identifying physical monitor frames or smartphone edges.
  - **Specular Glare Analysis**: Dynamic Laplacian variance tracking specular highlights and environmental reflection anomalies across frames.

---

## 3. Recommended Upstream Models & Provenance

When deploying production neural weights, the following models are recommended based on open research licenses, commercial compatibility, and proven academic benchmarks:

| Modality | Model Architecture | Academic Benchmark / Source | Weights License | Recommended Checkpoint |
| :--- | :--- | :--- | :--- | :--- |
| **Image** | EfficientNet-B4 / ConvNeXt-Tiny | FaceForensics++, Celeb-DF v2 | Apache 2.0 / MIT | ONNX fp16 |
| **Video** | 3D-ResNet / TimeSformer | DeepFake Detection Challenge (DFDC) | MIT / CC-BY-NC 4.0 | ONNX int8/fp16 |
| **Audio** | AASIST (Graph Attention) | ASVspoof 2019 / 2021 Logical Access | BSD-3-Clause | PyTorch / ONNX |

---

## 4. Model Training & Validation Specifications

For organizations fine-tuning or retraining proprietary models on the Privacy Eye platform, the following training protocol is required:

1. **Dataset Sourcing & Licensing**:
   - Only datasets with explicit research or commercial permissions (e.g. FaceForensics++, Celeb-DF, ASVspoof, WildDeepfake) may be ingested.
   - User-uploaded media must **never** be added to training corpuses without explicit opt-in consent (`MODEL_TRAINING`).
2. **Identity Leakage Prevention**:
   - Splits (Train / Val / Test) must be **subject-disjoint** (i.e., frames or clips of the same actor or speaker cannot appear in both training and test sets).
3. **Data Deduplication**:
   - Perceptual image hashing (pHash) and audio acoustic fingerprinting must be executed before ingestion to prevent duplicate samples from distorting validation metrics.
4. **Evaluation Metrics**:
   - Standard metrics: Precision, Recall, F1 Score, ROC-AUC.
   - Fairness & calibration: False Positive Rate (FPR) at fixed Detection Error Tradeoff (DET) points (e.g. FPR ≤ 1%), Equal Error Rate (EER), and Brier calibration score.
5. **No Universal Detection Claims**:
   - Model cards must document known failure modes (e.g., unseen generative architectures like Flux or Sora, low-light imagery, strong compression). Universal 100% deepfake detection claims are scientifically invalid and strictly prohibited.
