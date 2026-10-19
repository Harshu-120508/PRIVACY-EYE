# Privacy Eye — Known Limitations & Risk Disclosures

In accordance with our strict truth-in-AI principles, this document transparently documents the technical, algorithmic, and operational boundaries of the Privacy Eye platform.

---

## 1. Probabilistic Nature of Detection

**Privacy Eye does not provide infallible or legally absolute determinations of media authenticity.**

All analysis outputs, risk levels (`LOW`, `SUSPICIOUS`, `HIGH`, `CRITICAL`), and predictions (`AUTHENTIC`, `MANIPULATED`, `SUSPICIOUS`, `UNDETERMINED`) represent **probabilistic indicators** based on observable digital signal artifacts and neural classification probabilities. They must not be interpreted as definitive statements of fact.

---

## 2. Modality-Specific Limitations

### 2.1 Image Forensics & Detection
1. **Aggressive Social Media Compression**: Messaging and social platforms (e.g. WhatsApp, Instagram, X) re-encode images using aggressive lossy JPEG compression. This wipes out delicate high-frequency noise distributions and resets Error Level Analysis (ELA) grids, increasing false-negative rates on compressed deepfakes.
2. **Sub-256px Resolutions**: Downscaled thumbnails or heavily cropped headshots do not contain sufficient pixel density for reliable Fourier (2D-FFT) grid analysis.
3. **Diffusion Model Evolution**: Modern generative models (e.g. Midjourney v6, Flux.1) exhibit significantly fewer periodic frequency grid artifacts than older GAN architectures (StyleGAN), necessitating continuous fine-tuning of neural detectors.

### 2.2 Video Analysis
1. **Low Bitrate Macroblocking**: Highly compressed video streams (low-bitrate H.264/H.265) create compression boundaries along 8x8 and 16x16 macroblock seams that can be mistaken for facial boundary splicing (false positives).
2. **Static Scenes**: Videos with negligible subject movement or static interview framing offer limited temporal frames for motion vector differencing.
3. **Face Occlusions & Extreme Angles**: Severe profile angles (> 45°) or obstruction by glasses, hands, or microphones degrade face alignment accuracy.

### 2.3 Audio Analysis
1. **Short Audio Duration**: Audio samples under 1.5 seconds do not contain enough speech phonemes to reliably estimate vocal tract continuity or fundamental frequency ($f_0$) pitch stability.
2. **Acoustic Noise & Room Reverb**: Echo, background music, or heavy environmental noise distorts Mel-frequency cepstral coefficients (MFCCs), frequently yielding an `UNDETERMINED` prediction.
3. **Analog Captures / Microphone Re-recording**: Playing synthetic audio through a physical loudspeaker and re-recording it via an analog microphone introduces physical room acoustics that mask vocoder artifacts.

### 2.4 Browser-Side Webcam Liveness (Live Scan)
1. **Ambient Lighting**: Low-light or high-contrast backlighting impedes browser facial landmark triangulation.
2. **Camera Sensor Frame Rates**: Low-end webcams operating below 15 FPS may drop frames during a rapid natural blink (which typically completes in 100–350 ms).
3. **User Accommodation**: Users with ptosis, involuntary eye twitches, or wearing dark-tinted glasses may register atypical Eye Aspect Ratios (EAR).

---

## 3. Operational & Hardware Dependencies

1. **Dual-Mode Fallback**: In default self-hosted setups where heavy GPU neural weights (`.onnx`) are not mounted in `backend/weights/`, the system gracefully operates on mathematical digital signal forensics (`privacy-eye-forensics-*-v1`). While highly effective at identifying compression splices, frequency anomalies, and spectral rolloff, forensic mode has lower sensitivity against state-of-the-art diffusion models than a multi-million parameter neural ensemble.
2. **Hardware Constraints**: Real-time multi-frame video inference at scale requires dedicated NVIDIA GPU acceleration (CUDA / TensorRT). Running inference on entry-level CPU instances introduces latency scaling with video length.
