"""
migrations/env.py — Alembic migration environment

Configured to:
- Read the database URL from samplemind.core.config.Settings (the same source
  used at runtime), so migrations always target the right database.
- Use SQLModel's shared metadata so all ORM table definitions are discovered
  automatically — just importing the models is enough.
- Support both online (--sql) and offline (to a SQL file) modes.

Run migrations:
    uv run alembic upgrade head       # apply all pending migrations
    uv run alembic downgrade -1       # roll back one step
    uv run alembic revision --autogenerate -m "add foobar column"
"""

from __future__ import annotations

import logging
from logging.config import fileConfig

from alembic import context
from sqlmodel import SQLModel

# ── Import all ORM models so their tables are included in metadata ─────────────
# Add any new model modules here when they are created.
import samplemind.core.models.user  # noqa: F401  ← registers User table

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

# Configure Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# SQLModel shares metadata with SQLAlchemy — all table definitions live here
target_metadata = SQLModel.metadata


def _get_url() -> str:
    """
    Resolve the database URL at migration time.

    Priority:
    1. SAMPLEMIND_DB_URL environment variable (CI / staging override)
    2. URL from alembic.ini [alembic] section (``sqlalchemy.url``)
    3. URL from samplemind.core.config.Settings (production default)
    """
    import os

    if url := os.getenv("SAMPLEMIND_DB_URL"):
        return url

    if ini_url := config.get_main_option("sqlalchemy.url"):
        # Skip the placeholder entry that starts with "sqlite:///%"
        if not ini_url.startswith("sqlite:///%("):
            return ini_url

    from samplemind.core.config import get_settings

    return get_settings().database_url


# ── Offline mode — emit SQL to a file without a live DB connection ────────────


def run_migrations_offline() -> None:
    """Write migration SQL to stdout without connecting to the database."""
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode — apply migrations to the live database ──────────────────────


def run_migrations_online() -> None:
    """Connect to the database and apply pending migrations."""
    from sqlalchemy import create_engine, pool

    url = _get_url()
    connectable = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=pool.NullPool,  # each migration gets its own connection
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,   # required for SQLite ALTER TABLE support
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

