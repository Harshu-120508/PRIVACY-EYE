"""
Supabase client integration for Privacy Eye.
Provides client singleton for database operations, storage, and authentication.
"""

from typing import Optional
from supabase import create_client, Client
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

_supabase_client: Optional[Client] = None


def get_supabase() -> Optional[Client]:
    """Returns singleton Supabase client or None if credentials are not configured."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY

    if not url or not key:
        logger.warning("Supabase credentials not configured in settings")
        return None

    try:
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized successfully", url=url)
        return _supabase_client
    except Exception as e:
        logger.error("Failed to initialize Supabase client", error=str(e))
        return None

