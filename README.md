# Privacy Eye 👁️

> **AI Can Fake It. Privacy Eye Can Check It.**

Privacy Eye is a production-grade digital authenticity and deepfake detection platform. Built for forensic media verification, high-speed live camera streams, and enterprise defense, it combines deep neural networks with deterministic spatial, temporal, biometric, and frequency-domain digital signal forensics.

---

## 1. System Architecture

```text
                                PRIVACY EYE
                                     │
               ┌─────────────────────┴─────────────────────┐
               │                                           │
         FRONTEND (Next.js 14)                     BACKEND (FastAPI)
         Interactive Dashboard & Privacy Center     Container / Cloud Run / Railway
               │                                           │
         HTTPS Requests                      ┌─────────────┼─────────────┐
         (Live Camera Stream)                │             │             │
               │                        PostgreSQL     Model Cache   MCP Server
               └──────────────────────►  (Database)    (ONNX/Weights) (Claude/IDE)
```

- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Dark Theme.
  - Dedicated public Privacy Policy page at [`/privacy`](frontend/app/privacy/page.tsx).
  - Unbundled, purpose-specific consent management at [`/dashboard/privacy`](frontend/app/dashboard/privacy/page.tsx).
  - Real-time webcam liveness & EAR blink tracker at [`/dashboard/live-scan`](frontend/app/dashboard/live-scan/page.tsx).
  - Authentic file upload analysis with real progress at [`/dashboard/analysis`](frontend/app/dashboard/analysis/page.tsx).
- **Backend**: FastAPI, Python 3.11+, Uvicorn, SQLAlchemy 2.0 Async ORM (PostgreSQL & SQLite), OpenCV, ONNX Runtime, Librosa.
- **Model Context Protocol (MCP)**: Embedded MCP server (`app.mcp.server`) exposing 8 approved forensic capabilities to AI assistants (Claude Desktop, Cursor, Antigravity IDE).
- **Privacy & Security**: Ephemeral media processing in RAM/temp storage with immediate unlinking. Passwords hashed with Argon2id; JWT tokens rotated on refresh; granular server-enforced consent checks.

---

## 2. Real AI Inference & Dual-Mode Forensics

Privacy Eye guarantees **zero fabricated results, zero simulated timers, and zero fake confidence scores**. Detection operates via a dual-mode engine:

1. **Pretrained Neural Inference**: When weights (`.onnx`) are mounted in `backend/weights/`, high-throughput neural classification is performed.
2. **Deterministic Digital Signal Forensics**: When neural weights are absent, the engine executes rigorous algorithmic signal analysis:
   - **Images**: 2D Fast Fourier Transform (2D-FFT) power spectrum analysis for periodic GAN grids + Error Level Analysis (ELA) JPEG re-quantization deltas.
   - **Video**: Inter-frame temporal variance differencing + 8x8 block Discrete Cosine Transform (DCT) compression seam detection across keyframes.
   - **Audio**: Librosa Mel-frequency cepstral coefficients (MFCCs), fundamental frequency ($f_0$) pitch stability, and spectral rolloff.

Every result provides model transparency: `model_id`, `model_version`, `prediction` (`AUTHENTIC`, `MANIPULATED`, `SUSPICIOUS`, `UNDETERMINED`), calibrated risk level, explainable signals, and documented limitations.

---

## 3. Model Context Protocol (MCP) Server

Privacy Eye includes an integrated MCP server adhering to the official Model Context Protocol Python SDK (`mcp` v2.3.0).

### Available Tools:
1. `get_detection_capabilities` — Inspect supported formats, modalities, and limits.
2. `analyze_image` — Submit base64 image bytes for real deepfake/forensic evaluation.
3. `analyze_video` — Submit base64 video bytes for temporal & compression seam analysis.
4. `analyze_audio` — Submit base64 audio bytes for synthetic speech & pitch stability checks.
5. `get_analysis_status` — Query job status (`PENDING`, `PROCESSING`, `COMPLETE`, `FAILED`).
6. `get_analysis_result` — Retrieve structured predictions, signals, and limitations.
7. `get_model_status` — Inspect active models, engine mode, and device allocations.
8. `get_privacy_settings` — Review ephemeral processing policies and data governance rules.

Run standalone MCP server:
```bash
cd backend
python -m app.mcp.server
```
See [`docs/MCP_INTEGRATION.md`](docs/MCP_INTEGRATION.md) for Claude Desktop and IDE setup instructions.

---

## 4. Local Development

### Prerequisites
- Node.js 18+ & npm
- Python 3.11+
- PostgreSQL 15+ (or SQLite for local testing)

### Quick Start with Docker Compose
```bash
git clone https://github.com/Hasrhu/privacy-eye.git
cd privacy-eye
docker compose up -d
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/health`
- Readiness Probe: `http://localhost:8000/ready`

### Manual Local Setup

#### Backend (FastAPI)
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
pip install mcp>=2.0.0
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
`

#### Database Migrations (Alembic)
Privacy Eye uses Alembic for schema version control and migrations:

`ash
cd backend

# Apply all migrations to head (fresh database)
python -m alembic upgrade head

# Stamp an existing database matching current models (zero recreation)
python -m alembic stamp head

# Generate a new autogenerated migration after updating SQLAlchemy models
python -m alembic revision --autogenerate -m "describe_changes"

# Roll back one migration step
python -m alembic downgrade -1

# Inspect current schema version
python -m alembic current
```

#### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

---

## 5. Automated Testing & Verification

The backend includes a comprehensive 62-test automated test suite covering authentication, real inference pipelines, MCP tool invocation, consent enforcement, GDPR Article 17 account erasure, and temporary file purging.

```bash
cd backend
python -m pytest tests -v
```
All 62 tests pass in ~11 seconds. See [`docs/TESTING.md`](docs/TESTING.md).

For frontend TypeScript verification:
```bash
cd frontend
npm run type-check
```
0 errors found.

---

## 6. Complete Documentation Index

- [`docs/PROJECT_AUDIT.md`](docs/PROJECT_AUDIT.md) — Initial codebase audit, identified gaps, and remediation log.
- [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) — Service architecture, Mermaid topology, and layer breakdown.
- [`docs/AI_MODEL_PIPELINE.md`](docs/AI_MODEL_PIPELINE.md) — Dual-mode inference, digital forensics, and training specifications.
- [`docs/MCP_INTEGRATION.md`](docs/MCP_INTEGRATION.md) — Model Context Protocol tool specifications and client configurations.
- [`docs/PRIVACY_DATA_FLOW.md`](docs/PRIVACY_DATA_FLOW.md) — Data lifecycle, storage guarantees, and GDPR deletion protocols.
- [`docs/SECURITY.md`](docs/SECURITY.md) — Threat model, Argon2id parameters, and OWASP Top 10 countermeasures.
- [`docs/TESTING.md`](docs/TESTING.md) — Automated testing matrix, fixture generation, and verified test runs.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Deployment instructions, environment variables, and Docker Compose.
- [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) — Transparent disclosure of algorithmic boundaries and risks.

---

## 7. License & Governance

Licensed under the Apache-2.0 License. See `LICENSE` for details.
