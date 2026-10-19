# Privacy Eye — Data Flow & Privacy Architecture

This document maps the complete data lifecycle across Privacy Eye. It details how data enters the system, where it is computed, how long it is stored, and how it is permanently purged.

---

## 1. Core Privacy Principles

1. **Ephemeral Media Processing**: User media (images, videos, audio) uploaded for authenticity inspection is processed in volatile memory (RAM) or scoped ephemeral storage. Raw media is **never** retained in long-term databases or object stores.
2. **Zero Secondary Use Without Explicit Consent**: Media submitted for deepfake scanning is **never** used for model retraining, product analytics, or advertising unless explicit, unbundled opt-in consent is granted.
3. **Decoupled Identity & Signals**: Analysis metadata (hash, signals, risk score) is isolated from authentication credentials and raw user identifiers.
4. **Enforceable User Control (GDPR Article 17 / CCPA)**: Users can withdraw consent at any time, soft-delete individual analyses from their audit log, or permanently wipe their entire account, cascade-deleting all historical records.

---

## 2. Complete Data Category Lifecycle Matrix

| Data Category | Collection Point | Purpose | Processing Location | Storage Location & Retention | Deletion Behavior | Third-Party Transfers | Legal Basis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **User Media (Image / Video / Audio)** | Dashboard Upload (`/api/v1/analyze/*`) or MCP client | Deepfake & AI-generation forensic analysis | Local Backend Server (RAM & `/tmp/privacy_eye_uploads`) | **Zero retention**. Ephemeral files are unlinked immediately after inference completes or fails. Lifetime < 60 seconds. | Instant unlinking (`path.unlink()`). Orphan sweeper purges any leftover files on startup/shutdown. | **None**. Processed entirely on-premise / self-hosted container. | Contract necessity / Explicit User Consent (`MEDIA_PROCESSING`) |
| **Account Credentials** | Registration (`/api/v1/auth/register`) | User identification & authentication | Backend Auth Module | Database (`users` table). Passwords hashed using Argon2id (salt + memory cost 64MB). Lifetime: Account lifetime. | Cascade deletion immediately upon account erasure request (`DELETE /api/v1/users/me`). | None | Contract necessity |
| **Session & Refresh Tokens** | Login / Token Refresh | Session authorization & token rotation | Backend Security Middleware | Database (`sessions` table). Token hashes stored with SHA-256 (raw secrets never stored). 24h (regular) or 30 days (remember-me). | Revoked immediately on logout; purged during cleanup routines. | None | Legitimate interest (security) |
| **Analysis Metadata & Signals** | Backend Inference Pipeline | Dashboard audit history, explainability, reports | Backend Database | Database (`media_analysis`, `analysis_signals`). Stored until deleted by user. | Soft-deleted on user request (`deleted_at = now()`), permanently dropped on account erasure. Excluded if `SAVE_HISTORY` consent is off. | None | Explicit User Consent (`SAVE_HISTORY`) |
| **Granular Consents** | Privacy Center (`/dashboard/privacy`) | Enforcing user rights & compliance tracking | Backend Users Route | Database (`user_consents` table). Stored with policy version, timestamp, and IP hash. | Overwritten on update, cascade-deleted on account closure. | None | Legal obligation (GDPR Art. 7) |
| **Security Audit Logs** | System Event Bus | Fraud prevention, brute-force mitigation, audit trail | Backend Application | Database (`audit_logs` table). Anonymized action logs. Retention: 90 days rolling. | Anonymized (user_id set to NULL if account deleted). Purged after retention window. | None | Legitimate interest (system integrity) |
| **Live Facial Landmarks (Webcam)** | Client-side Browser (`/dashboard/live-scan`) | Real-time blink & liveness detection | Client Web Browser (Canvas / Web Workers) | **Never leaves browser**. Landmark coordinates computed in browser memory. | Destroyed upon closing or refreshing browser tab. | None | Explicit User Consent |

---

## 3. Ephemeral File Lifecycle & Storage Guarantees

```
[User Browser / MCP Client]
            │
            ▼ (TLS 1.3 Encrypted Stream)
[FastAPI /analyze/ Endpoint]
            │
            ├─► 1. Verify Granular Consent (MEDIA_PROCESSING)
            ├─► 2. Validate MIME Type & Magic Bytes
            ├─► 3. Save to Temporary Path (/tmp/privacy_eye_uploads/{uuid}.ext)
            │
            ▼
[ML Inference Engine / Digital Signal Forensics]
            │ (OpenCV / ONNX / Librosa / FFT)
            │
            ├─► 4. Generate Predictions & Explanations
            │
            ▼
[Cleanup Handler (Finally Block & Lifespan)]
            │
            ├─► 5. Delete Temp File (path.unlink())
            ├─► 6. Flag Record: media_deleted = True
            │
            ▼
[PostgreSQL / SQLite Database]
(Only stores SHA-256, Status, Model ID, Risk Level, Signals. NO MEDIA STORED.)
```

### Protection Against Orphaned Files
If an unexpected crash or container termination occurs mid-inference:
- `FileService.cleanup_orphaned_temp_files(max_age_seconds=0)` executes automatically on application startup and graceful shutdown.
- Any orphaned file exceeding its active processing window is permanently unlinked.

---

## 4. User Deletion & Erasure Procedures (GDPR Art. 17)

### Single Analysis Deletion
- **Endpoint**: `DELETE /api/v1/analyze/{analysis_id}`
- **Action**: Sets `deleted_at = timestamp`. Instantly filters the record out of `/analyze/history`, single-record queries, and dashboard metric calculations.

### Complete Account Deletion
- **Endpoint**: `DELETE /api/v1/users/me`
- **Security Check**: Requires password confirmation (`password_confirmation`).
- **Database Cascade**:
  - `users` record deleted.
  - Relational cascade (`cascade="all, delete-orphan"` and foreign key `ondelete="CASCADE"`) wipes:
    - All `media_analysis` records and child `analysis_signals`.
    - All `reports`.
    - All `user_consents`.
    - All active and expired `sessions`.
    - All `user_preferences`.
    - All `api_keys`.
  - `audit_logs` are anonymized (`user_id = NULL`).

### Backup Policy & Retention Limits
- Database backups taken for disaster recovery are retained in encrypted, access-restricted cold storage for a maximum of 30 days.
- When an account deletion is executed in the active production database, records are purged immediately. Data lingering in historical snapshot backups will age out naturally as backup cycles expire.

---

## 5. Third-Party Transfers & Subprocessors

Privacy Eye does **not** sell, rent, or share personal data or uploaded media with third-party data brokers, ad networks, or external cloud AI APIs (e.g. OpenAI, Google Cloud Vision) in the standard self-hosted deployment.
- Inference is conducted locally within the container environment.
- Any future optional cloud model delegation requires explicit opt-in under the unbundled `EXTERNAL_AI_SHARING` consent flag.
