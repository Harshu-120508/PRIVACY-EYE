# Privacy Eye — Automated Testing & Verification Guide

This document documents the test architecture, automated suites, fixture generation, test coverage metrics, and verification instructions for Privacy Eye.

---

## 1. Test Architecture & Directory Layout

The automated test suite is located in `backend/tests/` and built using `pytest`, `pytest-asyncio`, `httpx`, and in-memory `aiosqlite`.

```
backend/tests/
├── conftest.py                       # Global test configuration and fixtures
├── test_authentication_system.py     # Argon2id registration, login, token refresh, sessions (8 tests)
├── test_analysis_pipeline.py         # Image, video, audio analysis, history, limits (3 tests)
├── test_consent_system.py            # Granular unbundled consent & server enforcement (2 tests)
├── test_deletion_and_retention.py    # GDPR Art. 17 erasure, soft-delete, temp file purge (4 tests)
├── test_mcp_server.py                # 8 MCP tools, payload caps, UUID validation, IDOR checks (8 tests)
├── test_live_scan_api.py             # Liveness sessions, blink detection endpoints (5 tests)
├── test_eye_blink_screen.py          # EAR calculation, blink state machine, thresholds (9 tests)
├── test_reports_api.py               # PDF and JSON authenticity report exports (3 tests)
├── test_dataset_system.py            # Dataset splits, deduplication, governance (7 tests)
├── test_dataset_api.py               # Dataset admin endpoints and permissions (3 tests)
├── test_model_manager.py             # Dual-mode engine warmup, status, fallback (3 tests)
├── test_admin_and_verification.py    # Admin verification, RBAC gates (2 tests)
└── test_benchmarks.py                # Latency, throughput, and calibration tests (5 tests)
```

**Total Active Test Suite: 62 automated tests.**

---

## 2. Test Execution & Verified Results

To run the full backend test suite:

```bash
cd backend
python -m pytest tests -v
```

### Verified Run Output (Python 3.14 / pytest 9.1.1):
```
tests/test_admin_and_verification.py ..                                  [  3%]
tests/test_analysis_pipeline.py ...                                      [  8%]
tests/test_authentication_system.py ........                             [ 20%]
tests/test_benchmarks.py .....                                           [ 29%]
tests/test_consent_system.py ..                                          [ 32%]
tests/test_dataset_api.py ...                                            [ 37%]
tests/test_dataset_system.py .......                                     [ 48%]
tests/test_deletion_and_retention.py ....                                [ 54%]
tests/test_eye_blink_screen.py .........                                 [ 69%]
tests/test_live_scan_api.py .....                                        [ 77%]
tests/test_mcp_server.py ........                                        [ 90%]
tests/test_model_manager.py ...                                          [ 95%]
tests/test_reports_api.py ...                                            [100%]

============================= 62 passed in 11.13s =============================
```

---

## 3. Verified Capabilities Matrix

| Requirement | Test File | Status | Verification Details |
| :--- | :--- | :--- | :--- |
| **Valid & Invalid Media Validation** | `test_analysis_pipeline.py` | PASS | Rejects unapproved MIME types (`422`) and oversized payloads (`413`). |
| **Real Inference & Forensics Fallback** | `test_analysis_pipeline.py`, `test_model_manager.py` | PASS | Dual-mode: executes 2D-FFT/ELA/Librosa when ONNX weights are not mounted. |
| **MCP Tool Execution & Payload Bounds** | `test_mcp_server.py` | PASS | All 8 MCP tools execute with structured outputs; rejects oversize base64 streams. |
| **Consent Withdrawal Enforcement** | `test_consent_system.py` | PASS | Blocking analysis (`403 FORBIDDEN`) when `MEDIA_PROCESSING` is withdrawn. Suppresses history when `SAVE_HISTORY` is withdrawn. |
| **Analysis Soft-Deletion** | `test_deletion_and_retention.py` | PASS | Marks `deleted_at`, excludes from history lists and single queries (`404`). |
| **GDPR Account Erasure** | `test_deletion_and_retention.py` | PASS | Password-confirmed cascade deletion wipes user, sessions, consents, analyses, and signals. |
| **Ephemeral Temp Media Purging** | `test_deletion_and_retention.py` | PASS | `FileService.cleanup_orphaned_temp_files` cleanly unlinks disk files. |
| **Path Traversal Sanitization** | `test_deletion_and_retention.py` | PASS | Filenames with `../../` are safely UUID-aliased; no arbitrary disk write occurs. |

---

## 4. Frontend Verification & Type Safety

To verify TypeScript contracts and compile-time type safety across the frontend:

```bash
cd frontend
npm run type-check
```

**Result: 0 errors.**
All API response types, consent schemas, and model transparency fields conform to `frontend/types/index.ts`.
