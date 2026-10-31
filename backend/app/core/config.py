from typing import Optional, List, Dict, Any
"""
Privacy Eye — Application Configuration
Uses pydantic-settings for typed, validated environment variable loading.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me-in-production-must-be-32-chars"
    CSRF_SECRET_KEY: Optional[str] = None
    APP_VERSION: str = "1.0.0-mvp"
    APP_DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./privacyeye.db"
    DATABASE_URL_SYNC: str = "sqlite:///./privacyeye.db"
    AUTO_CREATE_TABLES: bool = False  # Schema managed via Alembic migrations

    # JWT
    JWT_SECRET_KEY: str = "change-me-jwt-secret-32-chars-min"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Gemini AI Agent
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # File Limits
    MAX_IMAGE_SIZE_MB: int = 20
    MAX_VIDEO_SIZE_MB: int = 500
    MAX_AUDIO_SIZE_MB: int = 50
    TEMP_UPLOAD_DIR: str = "./tmp/uploads"
    TEMP_RETENTION_MINUTES: int = 30

    # CORS & Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_UPLOADS_PER_HOUR: int = 20

    # ML & Model Storage (Hugging Face Hub)
    ML_MODELS_DIR: str = "app/ml/weights"
    ML_DEVICE: str = "cpu"
    MODEL_REPOSITORY: str = "privacy-eye/privacy-eye-models"
    MODEL_REVISION: str = "main"
    MODEL_CACHE_DIR: str = "./models_cache"
    HF_TOKEN: str = ""
    AUTO_DOWNLOAD_MODELS: bool = True

    @property
    def max_image_bytes(self) -> int:
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024

    @property
    def max_video_bytes(self) -> int:
        return self.MAX_VIDEO_SIZE_MB * 1024 * 1024

    @property
    def max_audio_bytes(self) -> int:
        return self.MAX_AUDIO_SIZE_MB * 1024 * 1024

    def ensure_temp_dir(self) -> None:
        os.makedirs(self.TEMP_UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.MODEL_CACHE_DIR, exist_ok=True)


settings = Settings()
settings.ensure_temp_dir()
