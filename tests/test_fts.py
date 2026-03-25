"""FTS5 full-text search integration tests.

Uses a file-based SQLite DB (not the in-memory orm_engine) because FTS5 virtual
tables are created by Alembic migrations, not by SQLModel.metadata.create_all().
The fts_db fixture creates a temp file DB with both the ORM tables and the FTS5
virtual table + triggers, then redirects both the ORM engine and fts.py's
connection factory to point at the same file.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3

import pytest
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel

from samplemind.core.models.sample import SampleCreate
from samplemind.data.fts import fts_search
from samplemind.data.repositories.sample_repository import SampleRepository

_FTS5_DDL = [
    """
    CREATE VIRTUAL TABLE samples_fts USING fts5(
        filename, tags, genre, mood, instrument,
        content='samples',
        content_rowid='id'
    )
    """,
    """
    CREATE TRIGGER samples_ai AFTER INSERT ON samples BEGIN
        INSERT INTO samples_fts(rowid, filename, tags, genre, mood, instrument)
        VALUES (new.id, new.filename, COALESCE(new.tags, ''),
                COALESCE(new.genre, ''), COALESCE(new.mood, ''),
                COALESCE(new.instrument, ''));
    END
    """,
    """
    CREATE TRIGGER samples_au AFTER UPDATE ON samples BEGIN
        DELETE FROM samples_fts WHERE rowid = old.id;
        INSERT INTO samples_fts(rowid, filename, tags, genre, mood, instrument)
        VALUES (new.id, new.filename, COALESCE(new.tags, ''),
                COALESCE(new.genre, ''), COALESCE(new.mood, ''),
                COALESCE(new.instrument, ''));
    END
    """,
    """
    CREATE TRIGGER samples_ad AFTER DELETE ON samples BEGIN
        DELETE FROM samples_fts WHERE rowid = old.id;
    END
    """,
]


@pytest.fixture()
def fts_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """File-based SQLite with ORM tables + FTS5 virtual table.

    Redirects both the ORM engine and fts.get_fts_connection() to the same
    temp file so SampleRepository.upsert() and fts_search() share state.
    """
    import samplemind.core.models.sample
    import samplemind.core.models.user  # noqa: F401 -- register User table
    import samplemind.data.orm as orm_module

    db_path = tmp_path / "fts_test.db"
    engine = create_engine(f"sqlite:///{db_path}")

    # Create ORM-managed tables (users, samples, ...)
    SQLModel.metadata.create_all(engine)

    # Create FTS5 virtual table and sync triggers (done by Alembic in prod)
    with engine.connect() as conn:
        for ddl in _FTS5_DDL:
            conn.execute(text(ddl))
        conn.commit()

    # Redirect ORM to file-based engine
    orm_module._engine = engine

    # Redirect fts.py's raw sqlite3 connection to the same file
    monkeypatch.setattr(
        "samplemind.data.fts.get_fts_connection",
        lambda: sqlite3.connect(str(db_path)),
    )

    yield engine

    SQLModel.metadata.drop_all(engine)


def test_fts_search_basic(fts_db) -> None:
    SampleRepository.upsert(
        SampleCreate(filename="dark_kick.wav", path="/test/dark_kick.wav", mood="dark", instrument="kick")
    )
    SampleRepository.upsert(
        SampleCreate(filename="bright_hihat.wav", path="/test/bright_hihat.wav", mood="euphoric", instrument="hihat")
    )
    ids = fts_search("dark")
    assert len(ids) == 1
    ids = fts_search("kick")
    assert len(ids) == 1


def test_fts_search_or(fts_db) -> None:
    SampleRepository.upsert(SampleCreate(filename="trap_kick.wav", path="/test/trap.wav", genre="trap"))
    SampleRepository.upsert(SampleCreate(filename="dubstep_bass.wav", path="/test/dubstep.wav", genre="dubstep"))
    ids = fts_search("trap OR dubstep")
    assert len(ids) == 2


def test_repository_search_with_fts(fts_db) -> None:
    SampleRepository.upsert(
        SampleCreate(filename="dark_kick.wav", path="/test/dark_kick.wav", mood="dark", instrument="kick", tags="808,heavy")
    )
    # FTS5 tokenises "dark_kick.wav" as "dark" + "kick" + "wav" (underscore is a separator)
    # and also indexes mood="dark" and instrument="kick", so "dark kick" (implicit AND) matches.
    results = SampleRepository.search(query="dark kick")
    assert len(results) == 1
    assert results[0].filename == "dark_kick.wav"
