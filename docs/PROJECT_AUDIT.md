# Privacy Eye — Comprehensive Project Audit & Baseline System Map

> **Audited by:** Dexter (Senior Full-Stack, AI/ML, Cybersecurity Architect, MCP & Privacy Engineer)  
> **Date:** 2026-10-19  
> **Repository:** `C:\Users\harsh\PRIVACY-EYE`  
> **Active Branch:** `main` (Clean working tree, up-to-date with `origin/main`)  
> **Verification Status:** 48/48 Backend Pytest Tests Passing, Frontend TypeScript (tsc) 0 Errors  

---

## 1. Executive Summary

Privacy Eye is an AI and forensic detection platform designed to identify manipulated, synthetic, and deepfake media across images, videos, audio, and live camera streams.

This audit evaluates the repository against production prototype standards:
1. **Zero Hallucination / Zero Simulation Policy:** Every detection score must reflect real mathematical and model inference operations. Fake timers, hardcoded predictions, and simulated stages must be eradicated.
2. **Model Availability & Truthful Status:** Explicitly disclose whether an inference was produced by an ONNX neural model, classical digital signal processing / frequency forensics, or if it failed / is unsupported.
3. **Model Context Protocol (MCP) Server:** Implement a secure, scoped MCP server allowing AI agents to interact with approved Privacy Eye detection pipelines.
4. **Transparent Consent & Data Sovereignty:** Implement granular, unbundled consent controls (detection, history saving, optional media retention, external AI sharing, model improvement opt-in) with server-side enforcement.
5. **Public Truthful Privacy Policy:** Provide an accessible, legal-grade `/privacy` page detailing real data flows, ephemeral buffer lifecycles, and user rights.

---

## 2. Architecture & Tech Stack Inventory

```text
                                PRIVACY EYE TOPOLOGY
                                          |
                +-------------------------+-------------------------+
                |                                                   |
      FRONTEND (Next.js 14.2.5)                             BACKEND (FastAPI 0.111.0)
      App Router, Tailwind CSS, Zustand, Framer Motion      Python 3.14 / Uvicorn / Async SQLAlchemy
                |                                                   |
        +-------+-------+                                   +-------+-------+
        |               |                                   |               |
    Public Pages   Dashboard Pages                     REST Endpoints   ML & Forensics
    - /            - /dashboard                        - /auth          - YuNet (ONNX)
    - /privacy     - /dashboard/analysis               - /analyze       - 2D-FFT / ELA
    - /auth/login  - /dashboard/live-scan              - /live-scan     - OpenCV Frame Diff
    - /auth/reg    - /dashboard/privacy                - /reports       - Librosa Spectral
                   - /dashboard/history                - /users         - MCP Server (Stdio/SSE)
```

### Technology Matrix

| Layer | Component | Version | Role in Platform |
|---|---|---|---|
| **Frontend** | Next.js App Router | 14.2.5 | Modern React 18 SSR & CSR UI |
| **Frontend** | Tailwind CSS | 3.4.4 | Frosted dark glassmorphism UI design system |
| **Frontend** | Framer Motion & Lucide | 11.2 / 0.395 | Interactive UI motion, micro-animations, icons |
| **Frontend** | Axios & js-cookie | 1.7.2 / 3.0.5 | Authenticated API transport, CSRF & JWT handling |
| **Backend** | FastAPI & Uvicorn | 0.111 / 0.30 | High-performance asynchronous API engine |
| **Backend** | SQLAlchemy & Alembic | 2.0.30 / 1.13.1 | Async ORM with migration management |
| **Backend** | Pydantic v2 | 2.7.1 | Strict schema validation and serialization |
| **Backend** | Argon2id & python-jose | 23.1 / 3.3.0 | Secure password hashing & JWT token management |
| **ML Engine** | ONNX Runtime | 1.18.0 | Cross-platform deep learning tensor execution |
| **CV Engine** | OpenCV (`cv2`) | 4.9.0 / 5.0.0 | FaceDetectorYN (YuNet), image/video decoding |
| **Audio** | Librosa & SoundFile | 0.10.2 / 0.12.1 | Mel-spectrogram, spectral flatness, zero-crossing |
| **Database** | SQLite / PostgreSQL | 3 / 15 | Relational storage for users, audits, & consent |

---

## 3. Deep Forensic Audit of Detection Features

| Feature | Endpoint / Module | Implementation Type | True Status & Verification |
|---|---|---|---|
| **Live Face Detection** | `/api/v1/live-scan/frame`<br>`app/ml/live_authenticity.py` | Real Model (ONNX) | **Real.** Uses OpenCV `FaceDetectorYN` with `face_detection_yunet.onnx`. Auto-downloads from official OpenCV Zoo if missing. Tested in `test_eye_blink_screen.py`. |
| **Live Blink Verification** | `app/ml/eye_analyzer.py`<br>`app/ml/blink_engine.py` | Real CV Algorithm | **Real.** Uses Sobel gradient filters and pupil-to-sclera contrast ratios. Non-punitive 30-second window verified in tests. |
| **Live Replay Attack Defense** | `app/ml/screen_detector.py` | Real CV Algorithm | **Real.** Uses 2D-FFT Moiré frequency grid detection, rectangular bezel boundary checks, and specular glare variance. |
| **Benchmark Policies** | `app/ml/benchmarks.py` | Real Rule Engine | **Real.** Silent-Face anti-spoofing policy, FaceForensics compression baselines, and FFHQ texture distribution baselines. |
| **Image Analysis** | `/api/v1/analyze/image`<br>`app/ml/forensics.py` | Real Digital Forensics | **Real Forensics.** 2D-FFT inner/outer ratio, Error Level Analysis (ELA), quadrant noise standard deviation, EXIF metadata tampering checks. EfficientNet ONNX weights fallback to forensics. |
| **Video Analysis** | `/api/v1/analyze/video`<br>`app/ml/forensics.py` | Real Video Forensics | **Real Forensics.** Frame extraction with `cv2.VideoCapture` (samples 16 frames), inter-frame absolute difference mean & variance, 8x8 DCT compression block boundaries, inter-frame brightness flicker. |
| **Audio Analysis** | `/api/v1/analyze/audio`<br>`app/ml/forensics.py` | Real Audio Forensics | **Real Forensics.** Spectral flatness, Mel-spectrogram variance, pitch stability, zero-crossing rate via Librosa/SoundFile. |

---

## 4. Identified Defects, Simulated Workflows & Deficiencies

### 4.1 Fabricated Progress in Frontend Media Upload
- **Location:** `frontend/app/dashboard/analysis/page.tsx` (Lines 112–115)
- **Defect:** `setInterval` cycles through fake scanning stages (`SCAN_STAGES`) every 1200ms regardless of actual server processing state.
- **Remediation:** Remove fake interval timer. Tie progress indicator directly to real upload progression and backend job status.

### 4.2 Missing Schema Transparency Fields
- **Location:** `backend/app/schemas/schemas.py` and `backend/app/database/models.py`
- **Defect:** `AnalysisResponse` and `MediaAnalysis` lack explicit attributes for:
  - `model_id` (identifier of the model or forensic pipeline executed)
  - `model_version` (semantic version of the detector)
  - `prediction` (`AUTHENTIC`, `MANIPULATED`, `SYNTHETIC`, `SUSPICIOUS`, or `UNDETERMINED`)
  - `limitations` (human-readable technical boundaries)
  - `error_code` (standardized machine error codes on failure)
  - `AnalysisStatus.UNSUPPORTED` (explicit status for incompatible formats)
- **Remediation:** Add missing schema attributes to reflect truth in inference results.

### 4.3 Missing Public Privacy Policy Page
- **Location:** `frontend/app/privacy/page.tsx` (Missing)
- **Defect:** No public Privacy Policy exists at `/privacy`. Legal notices, data lifecycle disclosures, and contact channels are inaccessible to non-authenticated visitors and registration flows.
- **Remediation:** Create a comprehensive, truthful, and accessible `/privacy` page.

### 4.4 Missing Granular Consent System
- **Location:** `backend/app/database/models.py`
- **Defect:** User preferences only contain two coarse boolean flags (`privacy_mode`, `cloud_processing_enabled`). There is no purpose-specific `UserConsent` entity tracking:
  1. Processing media for detection (necessary service basis)
  2. Saving analysis history (optional)
  3. Retaining uploaded media (optional, disabled by default)
  4. Sharing media with external AI providers (optional, disabled by default)
  5. Using media for model training/improvement (optional opt-in)
  6. Optional product analytics
- **Remediation:** Implement `UserConsent` database model, migration, CRUD API routes, and backend enforcement middleware blocking unauthorized data retention or history logging.

### 4.5 Missing Model Context Protocol (MCP) Server
- **Location:** `backend/app/mcp/` (Missing)
- **Defect:** No MCP server exists to expose approved Privacy Eye capabilities to external AI clients.
- **Remediation:** Build a standards-compliant MCP server exposing 8 tools:
  1. `get_detection_capabilities`
  2. `analyze_image`
  3. `analyze_video`
  4. `analyze_audio`
  5. `get_analysis_status`
  6. `get_analysis_result`
  7. `get_model_status`
  8. `get_privacy_settings`
  Enforce strict schema validation, API key authentication, tenant isolation, and zero media leakage.

---

## 5. Security & Privacy Lifecycle Assessment

1. **In-Memory Buffering:** Uploaded media is processed directly from memory (`UploadFile.read()`) or temporary files that are deleted via `try...finally: os.unlink(tmp_path)` immediately after inference.
2. **Ephemeral Media Storage:** `media_deleted = True` is marked on all analyses; no raw image, video, or audio payloads are stored permanently in the database or filesystem.
3. **Authentication & Session Security:** Argon2id password hashing, JWT access/refresh token rotation, HttpOnly cookie flags, and CSRF double-submit token validation are active.
4. **Tenant Isolation:** All database queries for analyses, reports, and sessions are strictly scoped by `current_user.id`.

---

## 6. Action Plan for Remaining Stages

- **Stage 2:** Remove simulated progress loops in frontend, enforce structured result schemas, add `UNSUPPORTED` status and error handling.
- **Stage 3:** Deepen real AI inference pipelines in `video_analyzer.py` and `audio_analyzer.py` to seamlessly blend neural ONNX and spectral forensics with transparent provenance.
- **Stage 4:** Implement and test the Model Context Protocol (MCP) server.
- **Stage 5:** Implement the public Privacy Policy page (`/privacy`) and granular Consent Management system with server-side enforcement.
- **Stage 6:** Strengthen media purge guarantees, account erasure workflows (GDPR Article 17), and audit trails.
- **Stage 7:** Build automated test coverage for new endpoints, MCP tools, and consent rules; run and verify complete test suite.
- **Stage 8:** Finalize documentation (`AI_MODEL_PIPELINE.md`, `MCP_INTEGRATION.md`, `PRIVACY_DATA_FLOW.md`, `SECURITY.md`, `KNOWN_LIMITATIONS.md`, etc.).
