"""
data/orm.py — SQLModel engine and session factory

A single SQLite engine is shared across the whole process.
Call ``init_orm()`` once at startup (FastAPI lifespan or ``samplemind api``).

The SQLite database is the *same file* used by the legacy sqlite3 layer
(``~/.samplemind/library.db`` or the platformdirs path).  Both layers can
coexist because SQLite allows concurrent readers and SQLModel manages the
``users`` and ``samples`` tables independently of the legacy ``sqlite3`` layer.

WAL mode + performance PRAGMAs are applied on every new connection via a
SQLAlchemy ``connect`` event listener.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

_engine = None


def _apply_sqlite_pragmas(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
    """Apply performance and reliability PRAGMAs to every new SQLite connection.

    WAL mode:        concurrent reads during writes (CLI + app can run simultaneously)
    cache_size:      64 MB page cache
    synchronous:     NORMAL — safe + fast (not FULL which is slow)
    temp_store:      in-RAM temp tables/indexes
    mmap_size:       256 MB memory-mapped I/O
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA cache_size=-64000")  # negative = kilobytes → 64 MB
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")  # 256 MB
    cursor.close()


def get_engine() -> Engine:
    """Return the shared SQLAlchemy engine, creating it on first call."""
    global _engine
    if _engine is None:
        from samplemind.core.config import get_settings

        db_url = get_settings().database_url
        _engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        # Register PRAGMA handler for every new connection
        event.listen(_engine, "connect", _apply_sqlite_pragmas)
    return _engine


def init_orm() -> None:
    """
    Create all SQLModel tables (``users``, ``samples``, etc.) if they don't exist.

    Imports all models so SQLModel.metadata knows about every table before
    calling ``create_all``.  Safe to call multiple times — idempotent.
    """
    # Import models to register them in SQLModel.metadata before create_all
    import samplemind.core.models.sample
    import samplemind.core.models.user  # noqa: F401

    engine = get_engine()
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session]:
    """
    Yield a SQLModel session, committing on success or rolling back on error.

    ``expire_on_commit=False`` keeps object attributes populated after the
    session is committed and closed, so callers can safely access fields on
    the returned ORM instances without an active session.
    """
    with Session(get_engine(), expire_on_commit=False) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
