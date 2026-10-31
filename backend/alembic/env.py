"""Alembic env.py — async migration support."""
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
import sqlalchemy as sa
from alembic import context
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.database.session import Base
from app.database import models  # noqa: F401 — register all models

config = context.config

# Dynamically set sync URL from application settings (if not already set via CLI or programmatic config)
configured_url = config.get_main_option("sqlalchemy.url")
if not configured_url or configured_url == "sqlite:///./privacyeye.db":
    sync_url = settings.DATABASE_URL_SYNC
    if sync_url:
        config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def compare_type_handler(context, inspected_column, metadata_column, inspected_type, metadata_type):
    """Custom type comparison for SQLite to avoid false positives on Enum vs VARCHAR."""
    if context.dialect.name == "sqlite":
        if isinstance(metadata_type, sa.Enum) and isinstance(inspected_type, (sa.String, sa.VARCHAR)):
            return False
    return None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode with compare_type and batch mode for SQLite."""
    url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL_SYNC
    is_sqlite = bool(url and ("sqlite" in url))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=compare_type_handler,
        render_as_batch=is_sqlite,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations in 'online' mode with compare_type and batch mode for SQLite."""
    is_sqlite = connection.dialect.name == "sqlite"
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=compare_type_handler,
        render_as_batch=is_sqlite,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run online migrations using async engine derived dynamically from configured URL."""
    from sqlalchemy.ext.asyncio import create_async_engine
    raw_url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL_SYNC
    if "sqlite://" in raw_url and "aiosqlite" not in raw_url:
        async_url = raw_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif "postgresql://" in raw_url and "asyncpg" not in raw_url:
        async_url = raw_url.replace("postgresql://", "postgresql+asyncpg://")
    else:
        async_url = raw_url

    engine = create_async_engine(async_url, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    """Dispatch online migration run."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
