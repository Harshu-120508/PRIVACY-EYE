"""
Privacy Eye — FastAPI Backend Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.logging import configure_logging
from app.database.session import engine
from app.database import models  # noqa: F401 — ensure models are registered
from app.api.v1 import router as api_v1_router
from app.core.middleware import RateLimitMiddleware, RequestIDMiddleware, CSRFMiddleware

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup & shutdown."""
    logger.info("Privacy Eye API starting", version=settings.APP_VERSION, env=settings.APP_ENV)
    # Database schema is managed via Alembic migrations.
    # Base.metadata.create_all is gated behind explicit dev-only AUTO_CREATE_TABLES flag.
    if getattr(settings, "AUTO_CREATE_TABLES", False) and settings.APP_ENV == "development":
        from app.database.session import Base, engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized via create_all (dev-only fallback)")
    # Model registry integrity & startup provenance check
    from app.services.model_manager import model_manager
    model_manager.validate_registry_at_startup()

    # Warm up ML models on startup
    from app.services.ml_service import ml_service
    from app.services.file_service import file_service
    file_service.cleanup_orphaned_temp_files(max_age_seconds=0)
    await ml_service.warmup()
    yield
    file_service.cleanup_orphaned_temp_files(max_age_seconds=0)
    logger.info("Privacy Eye API shutting down")


app = FastAPI(
    title="Privacy Eye API",
    description=(
        "AI-powered digital authenticity and deepfake detection platform. "
        "Results are probabilistic indicators — not definitive conclusions."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(RequestIDMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(RateLimitMiddleware, calls=settings.RATE_LIMIT_PER_MINUTE, period=60)

cors_origins = settings.CORS_ORIGINS
if isinstance(cors_origins, str):
    cors_origins = [o.strip() for o in cors_origins.split(",") if o.strip()]

# In production, allow configured origins plus dynamic Vercel preview/production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if ("*" not in cors_origins) else ["*"],
    allow_origin_regex=r"^https?://.*" if ("*" in cors_origins or settings.APP_ENV != "production") else r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allowed_hosts = settings.ALLOWED_HOSTS
if isinstance(allowed_hosts, str):
    allowed_hosts = [h.strip() for h in allowed_hosts.split(",") if h.strip()]

# In production, restrict wildcard hosts to known deployment domains if unconfigured
if settings.APP_ENV == "production" and (allowed_hosts == ["*"] or not allowed_hosts):
    logger.warning("Wildcard ALLOWED_HOSTS detected in production; restricting to platform domains")
    allowed_hosts = ["*.railway.app", "*.up.railway.app", "*.vercel.app", "localhost", "127.0.0.1"]

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts,
)

# ── Routes ──────────────────────────────────────────────────────────────────
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {"service": "Privacy Eye API", "status": "operational", "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@app.get("/ready", tags=["Health"])
@app.get("/api/v1/ready", tags=["Health"])
async def ready():
    from sqlalchemy import text
    from app.services.model_manager import model_manager

    # 1. Database readiness check
    db_status = "INITIALIZING"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_status = "READY"
    except Exception as e:
        logger.warning("Readiness probe: database connection degraded", error=str(e))
        db_status = "DEGRADED"

    # 2. ML Engine readiness
    ml_status = model_manager.get_model_status()
    engine_ready = ml_status.get("ml_engine_status", "DEGRADED_FORENSICS")

    overall_status = "ready" if (db_status == "READY" and engine_ready in ("READY", "DEGRADED_FORENSICS")) else "degraded"

    return {
        "status": overall_status,
        "api": "READY",
        "database": db_status,
        "models": engine_ready,
        "details": {
            "device": ml_status.get("device", "cpu"),
            "repository": ml_status.get("repository"),
            "models_count": ml_status.get("models_count", 0),
        },
    }

