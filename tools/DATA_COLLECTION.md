# Privacy Eye — Real Data Collection Protocol & Benchmark Specification

> **CRITICAL REQUIREMENT**: All recorded benchmark datasets must be stored **OUTSIDE** this repository (e.g., `C:\privacy_eye_dataset` or `../dataset`). Never commit private biometric data, videos, or raw photos into git.

---

## 1. Directory Structure Expected by `evaluation/eval_live_scan.py`

The evaluation harness expects a root directory where every subfolder corresponds to a ground-truth class. `"real"` is the only bona fide label; all other folders represent presentation attack types:

```text
C:\privacy_eye_dataset\
├── real\
│   ├── subject01_daylight_noglasses.mp4
│   ├── subject02_warm_glasses.mp4
│   └── ... (>= 30 unique individuals)
├── attack_screen\
│   ├── screen_iphone_oled_subj01.mp4
│   ├── screen_ipad_lcd_subj02.mp4
│   └── screen_monitor_subj03.mp4
├── attack_print\
│   ├── print_matte_color_subj01.mp4
│   └── print_glossy_photo_subj02.mp4
├── attack_faceswap\
│   ├── faceswap_deeplivecam_subj01.mp4
│   └── faceswap_simswap_subj02.mp4
└── attack_ai\
    ├── ai_gen_runway_subj01.mp4
    └── ai_gen_sora_subj02.mp4
```

Supported formats: `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv`, `.jpg`, `.jpeg`, `.png`, `.webp`.

---

## 2. Collection Requirements for Bona Fide Subjects (`real/`)

To support statistical validity and Phase 4 fairness slices, record **at least 30 distinct consented individuals**:

1. **Demographic & Visual Diversity**:
   - **Skin Tones**: Balanced representation across Fitzpatrick types I through VI.
   - **Eyewear**: Subjects with glasses (clear lenses, anti-reflective coatings, thick dark frames) and without glasses.
   - **Headwear / Accessories**: Hats, hijabs, turbans, varied hairstyles, and facial hair.
2. **Environmental Conditions**:
   - **Lighting**: Bright natural daylight, warm indoor LED, harsh overhead fluorescent, and low-light / side-lit conditions.
   - **Backgrounds**: Flat walls, cluttered office/home environments, windows with exterior light, and bookshelves with vertical lines.
3. **Capture Devices**:
   - Built-in laptop webcams (720p).
   - External USB webcams (1080p, e.g., Logitech).
   - Phone cameras streaming via virtual webcam.
4. **Behavior / Action in Clip**:
   - Duration: **10 to 20 seconds** per clip.
   - Natural blinking (normal physiological blink rate of 12–20 blinks/minute).
   - Natural micro-head movements (gentle pitch/yaw turns of 5°–15°).

---

## 3. Attack Sample Collection Requirements

### A. Digital Screen Replay (`attack_screen/`)
- Display the subject's face on:
  - OLED smartphones (e.g., iPhone, Samsung Galaxy with PenTile subpixel matrices).
  - LCD / IPS tablets (e.g., iPad).
  - Desktop LCD monitors.
- Position the screen in front of the webcam at normal viewing distance (30–60 cm).
- Include variations: holding screen stationary, slight screen tilt (testing specular glare), and screen framing face with bezel visible.

### B. Printed Photo Attacks (`attack_print/`)
- High-resolution color printouts of the subject's face on:
  - Standard matte paper.
  - Glossy photo paper.
- Test held stationary in front of camera, as well as manually warped/bent printouts.

### C. Live Face-Swap Attacks (`attack_faceswap/`)
- Real-time digital face-swaps applied over a live webcam feed using tools such as:
  - Deep-Live-Cam.
  - SimSwap / Roop / InsightFace.
- Target must be a consenting participant.

### D. AI-Generated Synthetic Faces (`attack_ai/`)
- Photorealistic AI-generated human face videos (e.g., modern diffusion models, video GANs).

---

## 4. Technical Emulation Settings

The evaluation harness (`eval_live_scan.py`) precisely reproduces the production live-scan frontend pipeline:
- **Resolution**: Resized to 640 × 480.
- **Compression**: Encoded as JPEG quality 0.85 (`canvas.toDataURL('image/jpeg', 0.85)`).
- **Sampling Rate**: ~4.5 FPS (1 frame every ~220 ms).
- **Virtual Clock**: Video timestamps drive the engine's internal timers to eliminate workstation processing speed jitter.

---

## 5. How to Run Evaluation

From the repository root:

```powershell
python evaluation/eval_live_scan.py `
    --backend C:\Users\harsh\PRIVACY-EYE\backend `
    --data C:\privacy_eye_dataset `
    --yunet C:\Users\harsh\PRIVACY-EYE\backend\app\ml\weights\face_detection_yunet.onnx `
    --out evaluation_results
```

### Outputs Produced:
- `evaluation_results/frames.csv`: Per-frame raw signal telemetry (`sig_moire_ratio`, `sig_peak_to_median`, `sig_ela_std`, `sig_edge_energy`, `sig_bezel_vertical_lines`).
- `evaluation_results/clips.csv`: Per-clip decisions, accept times, and reason codes.
- `evaluation_results/summary.txt`: Bona fide acceptance rate, BPCER, APCER per attack type, and per-signal empirical AUROC.

