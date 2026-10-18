# Privacy Eye — Stage 1: Project Audit

> **Audited by:** Dexter  
> **Date:** 2026-10-18  
> **Git Branch:** `main` (clean working tree, no uncommitted changes)  
> **Commit:** `46c1467` — _fix(frontend): resolve backend rewrite URL destination to prevent 404 proxy loop_

---

## 1. Repository Overview

| Item | Value |
|---|---|
| **Root path** | `C:\Users\harsh\PRIVACY-EYE` |
| **Structure** | Monorepo — `frontend/` (Next.js 14) + `backend/` (FastAPI/Python) |
| **Frontend deploy target** | Vercel (`vercel.json`) |
| **Backend deploy target** | Railway (`railway.toml`, `nixpacks.toml`, `Dockerfile`) |
| **Database** | PostgreSQL 15 (Docker Compose) / SQLite fallback for local dev |
| **ML model storage** | Hugging Face Hub (`privacy-eye/privacy-eye-models`) |
| **CI/CD** | GitHub Actions (3 workflows: `backend.yml`, `frontend.yml`, `nextjs.yml`) |
| **Git remotes** | `origin` → GitHub (`Hasrhu/privacy-eye`) |
| **Active branches** | `main`, plus 4 remote backups/experiments |
| **Total commits** | 14 meaningful feature commits |

---

## 2. Technology Stack

### Frontend
| Tech | Version | Purpose |
|---|---|---|
| Next.js | 14.2.5 | App Router, SSR, routing |
| React | 18.3.1 | UI components |
| TypeScript | 5.5.2 | Type safety |
| Tailwind CSS | 3.4.4 | Styling (dark frosted glassmorphism design system) |
| Framer Motion | 11.2.12 | Animations |
| Axios | 1.7.2 | HTTP client |
| Zustand | 4.5.2 | State management |
| React Hook Form | 7.52.1 | Form handling |
| React Dropzone | 14.2.3 | File uploads |
| Recharts | 2.12.7 | Dashboard charts |
| Lucide React | 0.395.0 | Icons |
| js-cookie | 3.0.5 | Cookie-based JWT token management |

### Backend
| Tech | Version | Purpose |
|---|---|---|
| FastAPI | 0.111.0 | REST API framework |
| Python | 3.11+ | Runtime |
| Uvicorn | 0.30.1 | ASGI server |
| SQLAlchemy | 2.0.30 (async) | ORM |
| Alembic | 1.13.1 | Database migrations |
| asyncpg | 0.29.0 | Async PostgreSQL driver |
| Pydantic | 2.7.1 | Data validation |
| python-jose | 3.3.0 | JWT signing/verification |
| argon2-cffi | 23.1+ | Argon2id password hashing |
| bcrypt (passlib) | 1.7.4 | Legacy password compat |
| structlog | 24.2.0 | Structured logging |
| httpx | 0.27.0 | Async HTTP client |
| tenacity | 8.3.0 | Retry logic |

### ML / AI
| Tech | Version | Purpose |
|---|---|---|
| PyTorch | 2.3.1 | Model training framework |
| ONNX Runtime | 1.18.0 | Cross-platform inference |
| OpenCV | 4.9.0 | Face detection (YuNet), image processing |
| Transformers | 4.41.2 | Pretrained model access |
| timm | 1.0.3 | EfficientNet model zoo |
| Librosa | 0.10.2 | Audio feature extraction |
| scikit-learn | 1.5.0 | Evaluation metrics |
| google-generativeai | 0.7.2 | Gemini AI agent integration |

### Infrastructure
| Tech | Purpose |
|---|---|
| Docker Compose | Local multi-service orchestration (Postgres + Backend + Frontend) |
| Railway | Backend deployment (Dockerfile-based) |
| Vercel | Frontend deployment (Next.js) |
| Hugging Face Hub | ML model artifact storage |
| PostgreSQL 15 | Production database |

---

## 3. Architecture Diagram

```text
                          PRIVACY EYE ARCHITECTURE
                                    |
              +---------------------+---------------------+
              |                                           |
        FRONTEND (Next.js 14)                     BACKEND (FastAPI)
        Deploy: Vercel                            Deploy: Railway
              |                                           |
        Pages:                                   Modules:
        - / (Landing - 3D Hero)                  - api/v1/routes/
        - /auth/login                              - auth.py
        - /auth/register                           - analysis.py
        - /auth/forgot-password                    - live_scan.py
        - /dashboard (Main)                        - reports.py
        - /dashboard/analysis                      - users.py
        - /dashboard/analysis/[id]                 - admin.py
        - /dashboard/history                       - dataset.py
        - /dashboard/live-scan                   - core/ (config, security, middleware, logging)
        - /dashboard/reports                     - database/ (session, 12 ORM models)
        - /dashboard/settings                    - services/ (ml, model_manager, user, file, report)
        - /dashboard/privacy                     - ml/ (forensics, image, video, audio, live, eye, blink, screen)
        - /dashboard/security                    - dataset/ (splitter, calibration, quality, augmentation, taxonomy, ood)
        - /dashboard/developer
        - /dashboard/assistant
```

---

## 4. Database Schema (12+ Tables)

| Table | Purpose | Key Fields |
|---|---|---|
| `users` | User accounts | id, email, hashed_password, role, is_active, is_verified |
| `sessions` | Login sessions | user_id, refresh_token_hash, ip_address, revoked_at |
| `user_preferences` | Theme/privacy settings | privacy_mode, cloud_processing_enabled |
| `password_reset_tokens` | Password reset flow | token_hash, expires_at, used_at |
| `api_keys` | Developer API keys | key_hash, usage_count |
| `model_versions` | ML model registry | accuracy, precision, recall, f1_score |
| `media_analysis` | Core scan records | media_type, risk_level, synthetic_probability, confidence |
| `analysis_signals` | Detection signals per scan | signal_key, severity, score |
| `reports` | Generated reports | title, summary, pdf_path, report_json |
| `audit_logs` | Immutable audit trail | action, resource_type, ip_address |
| `face_training_samples` | Consent-based training data | consent_given, category_label |
| `dataset_records` | Dataset governance | source_dataset, license_terms, split |
| `failure_cases` | Hard negative mining | true_label, prediction, confidence |
| `model_registry` | Model governance | status, license, weights_license, checksum |
| `live_sessions` | Live camera sessions | stream_fps, total_frames_analyzed |

---

## 5. Authentication System (Well Implemented)

| Feature | Status |
|---|---|
| Registration with email/password | Working |
| Argon2id password hashing | Working |
| JWT access + refresh tokens | Working |
| Dual auth (Bearer header + HttpOnly cookie) | Working |
| Session management (list/revoke) | Working |
| Logout / Logout-all | Working |
| Password change | Working |
| Forgot password / reset token flow | Working |
| Role-based access (USER, ADMIN, ENTERPRISE) | Working |
| Legacy bcrypt fallback | Working |
| Rate limiting middleware | Working |
| Request ID middleware | Working |

---

## 6. ML / AI Pipeline Status

### Currently Working (Real Implementation)
- Forensic analysis: EXIF metadata, frequency domain (DCT/DFT), compression artifacts, color histogram
- Live camera face detection (YuNet ONNX - auto-downloads)
- Eye blink detection (EAR algorithm)
- Screen/replay detection (Moire pattern, reflection, bezel)
- Presentation attack detection (multi-signal liveness)

### Requires Model Weights (Placeholder Entries)
| Model | Size | Status |
|---|---|---|
| `face_detection_yunet.onnx` | 232 KB | Auto-downloads from OpenCV Zoo |
| `image_efficientnet_b4.onnx` | ~78 MB | Placeholder SHA - needs real weights |
| `video_efficientnet_temporal.onnx` | ~157 MB | Placeholder SHA - needs real weights |
| `audio_wav2vec2_clone.onnx` | ~377 MB | Placeholder SHA - needs real weights |

**Critical Note:** All 4 models share the same SHA-256 hash in the manifest, confirming the 3 large models are placeholder entries. The system correctly falls back to forensics-only mode.

---

## 7. Security Assessment

### Good Practices in Place
- Argon2id password hashing (OWASP recommended)
- JWT with configurable expiry and refresh rotation
- CORS configured with origin restrictions
- Rate limiting middleware
- File type and size validation
- Secure HTTP headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)
- Audit logging for security actions
- IDOR protection (queries scoped to current user)
- Secrets excluded from Git

### Issues Needing Attention
| Issue | Severity |
|---|---|
| No CSRF protection for cookie-based auth | Medium |
| No Content Security Policy header | Medium |
| TrustedHostMiddleware allows `*` | Low |
| No Alembic migration files | Medium |
| JWT in JS-accessible cookies (not HttpOnly) | Medium |
| No email verification implementation | Low |
| Admin panel is skeletal | Low |

---

## 8. Existing Tests (7 files, ~1,219 lines)

| File | Lines | Scope |
|---|---|---|
| `test_authentication_system.py` | 315 | Auth flows, JWT, sessions |
| `test_benchmarks.py` | 138 | Performance benchmarks |
| `test_dataset_api.py` | 108 | Dataset CRUD API |
| `test_dataset_system.py` | 284 | Dataset splitting |
| `test_eye_blink_screen.py` | 280 | Eye blink and screen detection |
| `test_model_manager.py` | 51 | Model manager basics |
| `test_scan.py` | 43 | Basic scan integration |

---

## 9. Documentation (23 files)

Extensive coverage of architecture, authentication, ML strategy, model selection, dataset governance, deployment, evaluation, confidence scoring, and more.

---

## 10. Gap Analysis

### Critical
1. No Alembic migration history (tables via create_all only)
2. 3 of 4 ONNX model weights are placeholder entries
3. Admin panel is skeletal

### Moderate
4. No CSRF protection
5. No Content Security Policy
6. JWT stored in JS-readable cookies
7. Video/audio analyzers are pass-through stubs
8. No background task queue for large uploads
9. No email verification flow
10. No frontend test coverage
11. No production error tracking

### Low
12. No WebSocket upload progress
13. No feature flags
14. Docker Compose deprecated version key

---

## 11. Recommended Stage 2 Actions

1. Fix JWT cookie storage (HttpOnly)
2. Create initial Alembic migration
3. Fix duplicate httpx in requirements.txt
4. Remove deprecated docker-compose version key
5. Add CSRF protection
6. Add Content Security Policy header
7. Restrict TrustedHostMiddleware

These are all safe, non-breaking changes.

---

> **Status:** Stage 1 COMPLETE. Ready for Stage 2 upon approval.
