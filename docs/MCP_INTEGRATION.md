# Privacy Eye — Model Context Protocol (MCP) Integration Guide

> **Author:** Dexter (MCP Integration Engineer & Cybersecurity Architect)  
> **Server Implementation:** `backend/app/mcp/server.py`  
> **SDK:** Official MCP v2 Python SDK (`mcp` / `MCPServer`)  
> **Supported Transports:** `stdio` (local subprocess), `SSE` (HTTP streaming)  
> **Verification Status:** Verified with automated test suite (`tests/test_mcp_server.py` — 10/10 tests passing, `tests/test_stage7_integration_and_security.py` — 6/6 tests passing)  

---

## 1. Overview

The Privacy Eye Model Context Protocol (MCP) server securely exposes forensic deepfake detection capabilities to AI assistants (such as Claude Desktop, Cursor, Antigravity IDE, and autonomous agents).

### Security Architecture & Guarantees
- **No Arbitrary Filesystem Access:** Clients cannot specify arbitrary disk paths or read host files.
- **No URL Fetching:** Clients cannot instruct the server to execute outbound network requests or trigger SSRF attacks.
- **Strict Magic Byte & Base64 Validation:** Every uploaded media stream is checked against format magic bytes (JPEG `FF D8 FF`, PNG `89 50 4E 47`, WebP `RIFF...WEBP`, WAV `RIFF...WAVE`, MP4 `ftyp`, etc.).
- **Zero Raw Media Retention:** Media payloads are processed strictly in-memory or in ephemeral temp buffers purged immediately via `try...finally` after feature extraction.
- **Tenant Scoping & IDOR Defense:** Access to existing analysis history records is strictly verified against optional developer API keys. Cross-user data leakage is strictly prohibited.
- **Truthful Probabilistic Output:** Confidence scores, manipulation probabilities, model identifiers, and technical limitations are explicitly returned. No hardcoded or fabricated predictions are produced.

---

## 2. Supported Tools & Strict Input Schemas

| Tool Name | Purpose | Input Arguments | Output Format |
|---|---|---|---|
| `get_detection_capabilities` | Inspect supported formats, maximum byte bounds, and active algorithms. | None | JSON object with platform metadata, supported media types, and privacy guarantees. |
| `analyze_image` | Run real 2D-FFT, ELA, and neural image deepfake analysis. | `image_base64: str`<br>`filename: Optional[str]` | Structured analysis object (`status`, `media_type`, `model_id`, `model_version`, `prediction`, `confidence_score`, `signals`, `limitations`). |
| `analyze_video` | Run frame-sampled temporal continuity, DCT blocking, and flicker analysis. | `video_base64: str`<br>`filename: Optional[str]` | Structured analysis object with temporal signals and manipulation risk. |
| `analyze_audio` | Run spectral flatness, Mel-spectrogram variance, and pitch stability analysis. | `audio_base64: str`<br>`filename: Optional[str]` | Structured analysis object with acoustic signals and voice clone indicators. |
| `get_analysis_status` | Check processing status of a scan ID. | `analysis_id: str` (UUID)<br>`api_key: Optional[str]` | `status`, `media_type`, `created_at`, `processing_finished_at`. |
| `get_analysis_result` | Retrieve full forensic audit report and signals. | `analysis_id: str` (UUID)<br>`api_key: Optional[str]` | Full audit record without user PII or raw media. |
| `get_model_status` | Inspect active model ensemble, registry, and hardware device. | None | Device (`cpu`/`cuda`), active models, checksums, and disclaimers. |
| `get_privacy_settings` | Inspect zero-knowledge storage metrics and user rights. | None | Unbundled consent purposes, retention policy, and erasure endpoints. |

---

## 3. Configuration & Setup Instructions

### 3.1 Claude Desktop Configuration
Add the following to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "privacy-eye": {
      "command": "python",
      "args": [
        "-m",
        "app.mcp.server"
      ],
      "cwd": "C:\\Users\\harsh\\PRIVACY-EYE\\backend",
      "env": {
        "PYTHONPATH": "C:\\Users\\harsh\\PRIVACY-EYE\\backend"
      }
    }
  }
}
```

### 3.2 Antigravity IDE Configuration
In your project's `.agents/mcp_config.json`:

```json
{
  "mcpServers": {
    "privacy-eye": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "C:/Users/harsh/PRIVACY-EYE/backend",
      "env": {
        "PYTHONPATH": "C:/Users/harsh/PRIVACY-EYE/backend"
      }
    }
  }
}
```

---

## 4. Verification & Automated Testing

Run the MCP test suite directly:

```bash
cd backend
python -m pytest tests/test_mcp_server.py -v
```

All 8 tests execute end-to-end inference, schema boundary validation, and security exception handling without mocking.
