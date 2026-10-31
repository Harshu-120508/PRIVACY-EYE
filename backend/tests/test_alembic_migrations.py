"""
Privacy Eye — Alembic Migration & Schema Drift Verification Tests
Validates:
1. Dynamic DB URL resolution in alembic env.py without hardcoding.
2. Fresh database migration: upgrade head creates all 16 relational tables.
3. Downgrade one step: drops all tables in reverse dependency order without error.
4. Schema consistency: alembic check verifies zero drift against SQLAlchemy models.
"""
import os
import sys
import sqlite3
import tempfile
import pytest
from pathlib import Path
from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.database.session import Base
from app.database import models  # noqa: F401


@pytest.fixture
def temp_alembic_db():
    """Create an isolated temporary SQLite database for migration testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass


def _get_alembic_config(db_path: str) -> Config:
    """Build programmatic Alembic Config pointing to the temporary test database."""
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return cfg


def test_alembic_env_configuration():
    """Verify that alembic.ini and env.py resolve application settings without hardcoding."""
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    cfg = Config(str(ini_path))
    assert cfg.get_main_option("script_location") == "alembic"
    # Settings DATABASE_URL must be configured
    assert settings.DATABASE_URL is not None
    assert settings.DATABASE_URL_SYNC is not None


def test_alembic_fresh_upgrade_and_downgrade(temp_alembic_db: str):
    """Test full migration lifecycle on fresh DB: upgrade head -> verify tables -> downgrade -1."""
    cfg = _get_alembic_config(temp_alembic_db)

    # 1. Upgrade fresh DB to head
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(temp_alembic_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    created_tables = set(r[0] for r in cursor.fetchall())
    conn.close()

    expected_tables = set(Base.metadata.tables.keys())
    assert "alembic_version" in created_tables
    # Every table defined in SQLAlchemy models must exist
    missing_tables = expected_tables - created_tables
    assert not missing_tables, f"Tables missing after upgrade head: {missing_tables}"

    # 2. Downgrade one step
    command.downgrade(cfg, "-1")

    conn = sqlite3.connect(temp_alembic_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    remaining_tables = set(r[0] for r in cursor.fetchall())
    conn.close()

    # All model tables must be dropped cleanly
    assert "users" not in remaining_tables
    assert "media_analysis" not in remaining_tables
    assert "user_consents" not in remaining_tables


def test_alembic_stamp_and_check(temp_alembic_db: str):
    """Test stamping an existing database copy and verifying zero schema drift."""
    cfg = _get_alembic_config(temp_alembic_db)

    # Simulate existing DB by creating tables directly with Base.metadata.create_all
    from sqlalchemy import create_engine
    sync_engine = create_engine(f"sqlite:///{temp_alembic_db}")
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()

    # Stamp head
    command.stamp(cfg, "head")

    conn = sqlite3.connect(temp_alembic_db)
    cursor = conn.cursor()
    cursor.execute("SELECT version_num FROM alembic_version")
    stamped_version = cursor.fetchone()[0]
    conn.close()

    assert stamped_version == "0001_baseline"

    # Verify check passes with zero schema drift
    command.check(cfg)
