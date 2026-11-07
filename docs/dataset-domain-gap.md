# Domain Gap Analysis: Public Research Datasets vs. Privacy Eye Live-Scan

**Author**: Senior ML/Security Engineer  
**Date**: 2026-11-07  
**Scope**: Presentation Attack Detection (PAD), Deepfake Face-Swap, and Audio Heuristics

---

## 1. Privacy Eye Baseline Operational Environment

Before comparing external datasets, we define the exact production environment of the Privacy Eye live-scan engine:
- **Input Stream**: Browser WebRTC webcam (`navigator.mediaDevices.getUserMedia`).
- **Transport & Compression**: Client-side canvas capture sending `image/jpeg` at quality **0.85** over WebSocket.
- **Resolution**: $640 \times 480$ pixels.
- **Frame Rate**: ~4.5 frames per second (variable based on client event loop and network jitter).
- **Acoustics**: Browser WebRTC audio stream (typically 48 kHz downsampled or Opus compressed with browser AEC and noise suppression).
- **Live Attack Surfaces**:
  1. Screen replay attacks (iPhone OLED, iPad, 4K PC monitors).
  2. Physical printed photos (color laser, inkjet, paper masks).
  3. Real-time virtual camera face-swaps (e.g. Deep-Live-Cam, OBS Virtual Camera stream injection).

---

## 2. Dataset-by-Dataset Domain Gap Comparison

| Dataset | Modality | Native Resolution & FPS | Compression & Format | Sensor / Camera Type | Key Domain Gaps vs. Privacy Eye Live-Scan | Impact on Signal Evaluation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Idiap Replay-Attack** | Video (PAD) | $320 \times 240$ @ ~25 FPS | Motion JPEG (.mov) | 2008-era MacBook built-in webcam | Resolution ($320 \times 240$) is half our $640 \times 480$; older displays (iPhone 3GS/4, iPad 1); fixed frame rate. | Excellent for webcam optical blur and hand-held jitter; subpixel pitch differs on older LCD screens vs modern OLED displays. |
| **OULU-NPU** | Video (PAD) | $1920 \times 1080$ @ 30 FPS | H.264 / MP4 | 6 smartphone front cameras | Smartphone lenses have different focal lengths and ISP sharpening than laptop webcams; $1080p$ is $3\times$ higher resolution. | Requires downscaling to $640 \times 480$ and re-encoding at JPEG q0.85 via `eval_live_scan.py` virtual clock to simulate live transport. |
| **CelebA-Spoof** | Images (PAD) | Variable (cropped face bounding boxes) | Mixed JPEG / PNG | 24 PC/phone/tablet sensors | Still images only; no temporal continuity, no eye blinking, no micro-motion. | Cannot evaluate blink engine or temporal stability; valid ONLY for per-frame spatial signals (Moiré, boundary seam). |
| **FaceForensics++** | Video (Deepfake) | 720p / 1080p @ 30 FPS | H.264 (C23, C40, Raw) | Professional YouTube videos / Studio | Studio lighting, broadcast lenses, offline post-production face swaps; no real-time stream artifacts. | High-quality source masks may conceal seam artifacts that appear in real-time frame generators. |
| **DFDC** | Video (Deepfake) | Mostly 1080p @ 30 FPS | H.264 MP4 | Diverse mobile & laptop webcams (3,426 actors) | Domestic backgrounds closely match home webcams, but encoded at standard video bitrates rather than per-frame JPEG q0.85. | Best available public proxy for domestic environments and diverse lighting, but lacks virtual-cam driver latency. |
| **ASVspoof 2019** | Audio (TTS / Replay) | 16 kHz / 48 kHz Lossless FLAC | Uncompressed / FLAC | Studio recording microphones (VCTK corpus) | Studio microphone acoustics; completely lacks room reverberation, laptop fan noise, and browser AEC compression. | Measures theoretical discrimination of spectral flatness / pitch jitter; will exhibit lower noise floors than live browser mic audio. |

---

## 3. Methodological Guardrails: What Results May and May Not Do

### Permitted Uses of Public Dataset Benchmarks:
1. **Signal Discrimination Ranking**: Measure AUROC on held-out test splits to confirm whether a signal provides statistically significant separation ($p < 0.05$, AUROC $> 0.50$).
2. **Identification of Inverted or Broken Heuristics**: Formally isolate signals that perform at or below chance level ($\text{AUROC} \approx 0.50$) or correlate with noise rather than spoofing.
3. **Moiré Peak Detector Comparison**: Objectively compare the legacy outer/inner FFT energy ratio against the Phase 2 periodic-peak detector on screen replay test splits.

### Prohibited Uses (Hard Constraints):
1. **Never Set Final Production Thresholds**: Operating thresholds tuned on $1080p$ H.264 video or $320 \times 240$ MJPEG must NOT be deployed as production cutoffs for $640 \times 480$ JPEG q0.85 streams.
2. **Never Claim Production Accuracy**: Public dataset test figures must be explicitly labelled:
   `PUBLIC DATA - DOMAIN SHIFTED (NOT PRODUCTION ACCURACY)`.
3. **Final Calibration Requirement**: Production thresholds and fusion weights must be fitted on genuine consented recordings captured directly through Privacy Eye's frontend pipeline (`tools/DATA_COLLECTION.md`), including live virtual camera face swaps.

