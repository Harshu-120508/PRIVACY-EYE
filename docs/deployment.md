# Privacy Eye — Deployment & Operations Guide

This guide details the deployment steps, environment configuration, containerization, and production operational practices for Privacy Eye.

---

## 1. Environment Configuration

### 1.1 Backend Configuration (`backend/.env`)

Create `backend/.env` with the following variables:

```ini
# Application Metadata
APP_NAME=Privacy Eye API
APP_ENV=production                  # development | staging | production
APP_VERSION=1.0.0
DEBUG=False

# Host & Ports
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
# Production (PostgreSQL):
DATABASE_URL=postgresql+asyncpg://privacy_user:SuperSecretPassword123@localhost:5432/privacy_eye
# Local Development (SQLite):
# DATABASE_URL=sqlite+aiosqlite:///./privacyeye.db

# Cryptography & JWT Security
SECRET_KEY=generate-a-64-char-random-hex-string-for-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS & Network Boundaries
CORS_ORIGINS=https://privacyeye.yourdomain.com,https://your-app.vercel.app
ALLOWED_HOSTS=privacyeye.yourdomain.com,localhost,127.0.0.1

# Security & Upload Throttling
RATE_LIMIT_PER_MINUTE=60
MAX_IMAGE_MB=20
MAX_VIDEO_MB=50
MAX_AUDIO_MB=25

# Storage
TEMP_UPLOAD_DIR=/tmp/privacy_eye_uploads
MODEL_STORAGE_PATH=./weights
```

### 1.2 Frontend Configuration (`frontend/.env.local`)

```ini
NEXT_PUBLIC_API_URL=https://api.privacyeye.yourdomain.com/api/v1
NEXT_PUBLIC_APP_NAME=Privacy Eye
NEXT_PUBLIC_APP_ENV=production
```

---

## 2. Local Development Setup

### Backend (FastAPI + Uvicorn)
```bash
# In backend/ directory:
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
pip install mcp>=2.0.0

# Start server with live reload:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend (Next.js 14)
```bash
# In frontend/ directory:
npm install
npm run dev
# Accessible at http://localhost:3000
```

---

## 3. Production Docker Deployment

### 3.1 Docker Compose Setup

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: privacyeye-db
    environment:
      POSTGRES_USER: privacy_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: privacy_eye
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U privacy_user -d privacy_eye"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: privacyeye-backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql+asyncpg://privacy_user:${DB_PASSWORD}@db:5432/privacy_eye
      - SECRET_KEY=${SECRET_KEY}
      - APP_ENV=production
      - CORS_ORIGINS=${CORS_ORIGINS}
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: privacyeye-frontend
    restart: unless-stopped
    depends_on:
      - backend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000/api/v1
    ports:
      - "3000:3000"

volumes:
  pgdata:
```

---

## 4. Health & Readiness Probes

Privacy Eye provides standard endpoints for orchestrators (Kubernetes, AWS ECS, Railway):

- **Liveness Probe**: `GET /health` or `GET /api/v1/health`
  - Returns `200 OK` with JSON `{"status": "healthy", "version": "1.0.0"}` if the process is responsive.
- **Readiness Probe**: `GET /ready` or `GET /api/v1/ready`
  - Validates active database connectivity (`SELECT 1`) and ML inference engine state.
  - Returns `status: "ready"` or `status: "degraded"` with individual component states:
    ```json
    {
      "status": "ready",
      "api": "READY",
      "database": "READY",
      "models": "DEGRADED_FORENSICS"
    }
    ```

---

## 5. Model Context Protocol (MCP) Server Run

To launch the standalone MCP server transport for AI assistants:

```bash
cd backend
python -m app.mcp.server
```

Clients connecting via Stdio or SSE can invoke all 8 approved forensic analysis tools.
