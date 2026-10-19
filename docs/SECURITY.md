# Privacy Eye — Security Architecture & Threat Model

This document outlines the security controls, defensive countermeasures, cryptography standards, and vulnerability mitigations implemented in Privacy Eye.

---

## 1. Authentication & Session Security

### Argon2id Password Hashing
- **Algorithm**: Argon2id (memory-hard, resistant to GPU/ASIC brute-force attacks).
- **Parameters**:
  - Memory cost: 65,536 KiB (64 MB)
  - Time cost (iterations): 3
  - Parallelism: 4 threads
- **Enforcement**: Plaintext passwords are never logged, stored, or transmitted without TLS.

### JWT & Session Token Lifecycle
- **Access Tokens**: Short-lived (15 minutes default) JSON Web Tokens (JWT) signed with `HMAC-SHA256`. Carries subject `sub` (User ID), email, role, and expiration timestamp.
- **Refresh Tokens**: High-entropy cryptographically secure random bytes (`secrets.token_urlsafe(64)`).
- **Storage**: Only the SHA-256 hash of refresh tokens is stored in the `sessions` table. A database leak cannot reveal valid refresh tokens.
- **Rotation**: Refresh tokens are rotated on each exchange; older tokens are revoked immediately.
- **Revocation**: Logging out or changing passwords invalidates all active sessions across devices.

---

## 2. Authorization & Insecure Direct Object Reference (IDOR) Mitigation

- **Strict Resource Scoping**: Every database lookup for analyses, reports, API keys, or consents strictly couples the requested resource ID with `current_user.id`:
  ```python
  select(MediaAnalysis).where(
      MediaAnalysis.id == analysis_id,
      MediaAnalysis.user_id == current_user.id,
      MediaAnalysis.deleted_at.is_(None)
  )
  ```
- **Role-Based Access Control (RBAC)**: Endpoints reserved for administrative oversight (dataset management, model registry activation) check `current_user.role == UserRole.ADMIN`. Regular users receive `403 FORBIDDEN`.

---

## 3. Defense Against Web Vulnerabilities (OWASP Top 10)

| Vulnerability | Attack Vector | Countermeasure in Privacy Eye |
| :--- | :--- | :--- |
| **SQL Injection (SQLi)** | Malicious SQL inputs in queries | SQLAlchemy 2.0 ORM with asynchronous parameterized queries. No raw SQL concatenation. |
| **Cross-Site Scripting (XSS)** | Malicious scripts in user-provided names/signals | Next.js / React automatic HTML entity escaping on all rendered data. Strict CSP headers in production. |
| **Cross-Site Request Forgery (CSRF)** | Unauthorized browser state mutation | Custom `CSRFMiddleware` enforcing standard header validation and SameSite cookie policies. |
| **Path Traversal / Local File Inclusion** | Uploaded filenames containing `../../` | Uploaded files are renamed using secure UUIDs (`uuid.uuid4().hex + suffix`). Original filenames are stored as sanitized string metadata only. |
| **Server-Side Request Forgery (SSRF)** | Exploiting media fetch URLs | Privacy Eye does not accept arbitrary external URLs for media fetching. All media is provided via direct file upload or base64 stream. |
| **Denial of Service (DoS / Resource Exhaustion)** | Oversized payloads or rapid-fire scanning | Strict file size caps (20MB image, 50MB video, 25MB audio). IP-based and user-based rate limiting via `RateLimitMiddleware`. |

---

## 4. Media Upload Sanitization & Ephemeral Handling

1. **MIME & Magic Byte Verification**:
   - Content-Type header alone is not trusted. File headers are validated against signature bytes (e.g. `\xFF\xD8\xFF` for JPEG, `\x89PNG` for PNG, `ftyp` box for MP4).
2. **Ephemeral Disk Footprint**:
   - Files are stored temporarily in a restricted directory (`/tmp/privacy_eye_uploads`).
   - Permissions are restricted to the service user (`0700`).
   - Files are unlinked immediately after inference completes.
3. **Memory Safety**:
   - Frame sampling in video is capped (max 10-15 frames sampled evenly) to prevent out-of-memory crashes on large video files.

---

## 5. Model Context Protocol (MCP) Security Controls

The embedded MCP server (`app.mcp.server`) provides AI agents access to Privacy Eye. It enforces security boundaries:

1. **No Shell or Filesystem Access**: MCP tools only accept in-memory base64 strings or validated UUIDs. No tools expose local filesystem paths or command execution.
2. **Payload Size Limits**: Strict byte checks before processing (Image: 20MB, Video: 50MB, Audio: 25MB).
3. **No Key Leakage**: Sensitive environment variables, internal tokens, and database passwords are redacted from tool outputs.
4. **Tool Isolation**: Operations run within isolated helper routines with independent error recovery.

---

## 6. Audit Logging & Secrets Management

- **Audit Trail**: Key security lifecycle events (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `PASSWORD_CHANGED`, `CONSENT_GRANTED`, `CONSENT_WITHDRAWN`, `DELETE_ANALYSIS`, `ACCOUNT_DELETED`) are logged to the `audit_logs` table with timestamp, action, and anonymized context.
- **Sensitive Data Redaction**: Passwords, raw bearer tokens, and media payloads are filtered out before logs are formatted.
- **Environment Configuration**: Secrets are loaded strictly via `pydantic-settings` from environment variables, never hardcoded in source control.
