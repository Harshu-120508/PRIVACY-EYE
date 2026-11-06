# ==============================================================================
# Privacy Eye — Production FastAPI Backend Dockerfile
# Optimized multi-stage/slim container with OpenCV, FFmpeg, and non-root execution
# ==============================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_ENV=production

WORKDIR /app

# Install essential system libraries for OpenCV, audio DSP, dlib compilation, and health probes
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies: install CPU-only PyTorch wheels first to avoid 2.5GB CUDA bloat
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app

# Create non-privileged runtime user and allocate workspace directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/tmp/uploads /app/models_cache && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Start Uvicorn bound to 0.0.0.0 with dynamic $PORT support for container cloud platforms
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
