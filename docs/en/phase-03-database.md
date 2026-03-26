# Phase 3 — Database & Data Layer

**Status: ✅ Complete** — SQLModel + Alembic live, WAL mode auto-applied | Phase 3 of 16

> Upgrade the raw `sqlite3` layer in `database.py` to **SQLModel** + SQLAlchemy 2.0 with
> Alembic migrations, type-safe models, and a Repository pattern.

---

## Prerequisites

- Phase 1 complete (uv + pyproject.toml)
- `sqlmodel` and `alembic` added to `pyproject.toml`
- Basic SQL knowledge is helpful

---

## Goal State

- `src/samplemind/core/models/sample.py` with `Sample`, `SampleCreate`, `SampleUpdate`, `SamplePublic` SQLModel classes
- `src/samplemind/data/repositories/sample_repository.py` with `SampleRepository` (static-method pattern)
- `src/samplemind/data/orm.py` with `get_engine()`, `init_orm()`, `get_session()` context manager, WAL PRAGMAs
- `migrations/versions/0002_create_samples_table.py` — Alembic migration for the `samples` table
- In-memory SQLite via the `orm_engine` conftest fixture for isolated tests
- `data/database.py` superseded — no longer imported by any CLI command or web route

---

## 1. Why SQLModel?

SQLModel is built on top of SQLAlchemy 2.0 and Pydantic. It lets you define database models
and validation models in a single class:

```
Raw sqlite3 (old)              SQLModel (new)
─────────────────────          ────────────────────────────────
No types — everything str/None Types: Optional[float], str, ...
SQL strings manually           select(Sample).where(...)
No validation                  Pydantic validates automatically
_migrate() hack                Alembic autogenerates migrations
row["bpm"] (sqlite3.Row)       sample.bpm (attribute)
```

Inheritance chain:
```
SQLModel
  ├── inherits from SQLAlchemy (database operations)
  └── inherits from Pydantic (validation and serialisation)
```

---

## 2. The Sample Model

```python
# filename: src/samplemind/core/models/sample.py
#
# This module is imported by:
#   data/orm.py — for SQLModel.metadata.create_all()
#   data/repositories/sample_repository.py — for upsert/search/tag
#   cli/commands/import_.py — for SampleCreate
#   cli/commands/library.py — for Sample (type annotations)
#   cli/commands/tag.py — for SampleUpdate
#   web/app.py — for SampleCreate and SampleUpdate

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    """Return the current UTC time. Used as default_factory to avoid the
    deprecated datetime.utcnow() (removed in Python 3.14)."""
    return datetime.now(UTC)


# ── ORM table ──────────────────────────────────────────────────────────────────


class Sample(SQLModel, table=True):
    """
    Represents one audio sample in the library.

    table=True: SQLModel creates a 'samples' database table for this class.
    Without table=True the class would be Pydantic-only (no DB table).

    Note: __tablename__ = "samples" (explicit plural) avoids SQLModel's default
    which would use the lowercase class name "sample" (singular).
    """

    __tablename__ = "samples"  # explicit plural — matches Alembic migration

    # Primary key — auto-incremented by SQLite
    id: Optional[int] = Field(default=None, primary_key=True)

    # File identity — path is unique (same file cannot be imported twice)
    filename: str = Field(index=True)   # indexed for fast LIKE search
    path: str = Field(unique=True)      # UNIQUE constraint prevents duplicate imports

    # Auto-detected fields (from the librosa analysis pipeline)
    # These are overwritten on every re-import — the analyzer decides their values.
    bpm: Optional[float] = Field(default=None)        # beats per minute
    key: Optional[str] = Field(default=None)          # e.g. "C maj", "F# min"
    mood: Optional[str] = Field(default=None)         # dark/chill/aggressive/euphoric/melancholic/neutral
    energy: Optional[str] = Field(default=None)       # low/mid/high
    instrument: Optional[str] = Field(default=None)   # kick/snare/hihat/bass/pad/lead/loop/sfx/unknown

    # Manually tagged fields (from user input)
    # These are NEVER overwritten on re-import — SampleRepository.upsert() skips them.
    genre: Optional[str] = Field(default=None)        # e.g. "trap", "lofi", "house"
    tags: Optional[str] = Field(default=None)         # comma-separated free-form tags

    # Timestamp — set once on first insert; never updated on re-import
    imported_at: Optional[datetime] = Field(default_factory=_now)


# ── Pydantic request schemas ───────────────────────────────────────────────────


class SampleCreate(SQLModel):
    """
    Schema for creating or upserting a sample during import.

    Only auto-detected fields are included — manually tagged fields (genre, tags)
    are intentionally absent so upsert() cannot accidentally overwrite them.
    Used by: cli/commands/import_.py, web/app.py (drag-and-drop import)
    """
    filename: str
    path: str
    bpm: Optional[float] = None
    key: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[str] = None
    instrument: Optional[str] = None


class SampleUpdate(SQLModel):
    """
    Schema for updating manual user tags on an existing sample.
    All fields are optional — only non-None fields are written by repo.tag().
    Used by: cli/commands/tag.py, web/app.py (POST /api/tag)
    """
    genre: Optional[str] = None
    mood: Optional[str] = None    # user can override the analyzer's mood
    energy: Optional[str] = None  # user can override the analyzer's energy
    tags: Optional[str] = None    # comma-separated free-form tags


class SamplePublic(SQLModel):
    """
    Safe public representation of a sample for API responses and JSON output.
    Derived from an ORM instance via model_config from_attributes=True.
    Used by: api/routes/*.py, cli --json output serialization
    """
    id: Optional[int] = None
    filename: str
    path: str
    bpm: Optional[float] = None
    key: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[str] = None
    instrument: Optional[str] = None
    genre: Optional[str] = None
    tags: Optional[str] = None
    imported_at: Optional[datetime] = None

    model_config = {"from_attributes": True}  # allows SamplePublic.model_validate(orm_instance)
```

---

## 3. Database Connection and Engine

```python
# filename: src/samplemind/data/orm.py
#
# This module is the single source of truth for the SQLAlchemy engine.
# All repositories (SampleRepository, UserRepository) call get_session()
# from here — nothing else in the codebase creates its own engine.

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

# Module-level engine — lazily created on first call to get_engine().
# Tests can replace this with: import samplemind.data.orm as m; m._engine = test_engine
_engine: Engine | None = None


def _apply_sqlite_pragmas(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
    """
    Apply performance and reliability PRAGMAs to every new SQLite connection.

    Registered as a SQLAlchemy 'connect' event listener so it runs automatically
    on every new connection — the caller never has to remember to set these.

    WAL mode:        concurrent reads during writes (CLI + web can run simultaneously)
    cache_size:      64 MB page cache (negative value = kilobytes)
    synchronous:     NORMAL — crash-safe without the overhead of FULL
    temp_store:      in-RAM temp tables and indexes (faster sorts and joins)
    mmap_size:       256 MB memory-mapped I/O (faster sequential reads on SSDs)
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA cache_size=-64000")    # negative = kilobytes → 64 MB
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")  # 256 MB
    cursor.close()


def get_engine() -> Engine:
    """
    Return the shared SQLAlchemy engine, creating it lazily on first call.

    The database URL comes from Settings.database_url which uses platformdirs:
      macOS:   ~/Library/Application Support/SampleMind/samplemind.db
      Linux:   ~/.local/share/SampleMind/samplemind.db
      Windows: %LOCALAPPDATA%\\SampleMind\\samplemind.db

    Tests override _engine directly:
        import samplemind.data.orm as orm_module
        orm_module._engine = in_memory_engine
    """
    global _engine  # noqa: PLW0603
    if _engine is None:
        from samplemind.core.config import get_settings

        db_url = get_settings().database_url
        _engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},  # needed for Flask threads
            echo=False,   # set to True temporarily to log all SQL for debugging
        )
        # Register PRAGMA handler — fires on every new connection, not just the first
        event.listen(_engine, "connect", _apply_sqlite_pragmas)
    return _engine


def init_orm() -> None:
    """
    Create all SQLModel tables if they do not already exist.

    Both model modules must be imported before create_all() so SQLModel.metadata
    knows about every table. This is safe to call multiple times — create_all is
    idempotent (it skips tables that already exist).

    Call this once at startup in every entry point:
        CLI commands:  call init_orm() before the first repository operation
        Flask:         call in the before_request hook
        FastAPI:       call in the lifespan context manager
    """
    # Import models to register their table definitions in SQLModel.metadata
    import samplemind.core.models.user    # noqa: F401 — registers User table
    import samplemind.core.models.sample  # noqa: F401 — registers Sample table

    engine = get_engine()
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Yield a SQLModel session that auto-commits on success and rolls back on error.

    expire_on_commit=False: keeps ORM attributes populated after commit so callers
    can safely access fields (e.g. sample.id) on the returned object without
    opening another session. Without this, accessing any field after commit raises
    DetachedInstanceError.

    Usage (in repositories — callers should not need get_session directly):
        with get_session() as session:
            session.add(sample)
        # sample.id is accessible here because of expire_on_commit=False
    """
    with Session(get_engine(), expire_on_commit=False) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
```

---

## 4. The Repository Pattern

The Repository pattern wraps all database operations in one class. This makes it easy to
substitute the database in tests (e.g. with in-memory SQLite).

```python
# filename: src/samplemind/data/repositories/sample_repository.py
#
# All database access for samples goes through this class.
# No raw SQL strings anywhere in this file — everything uses SQLModel's
# type-safe select() API.
#
# Design: static methods (not instance methods) so callers never need to
# construct or inject a SampleRepository instance. Each method opens and
# closes its own session via the get_session() context manager in orm.py.
# Tests redirect the engine by monkey-patching orm._engine before calling.

from __future__ import annotations

from typing import Optional

from sqlmodel import func, select

from samplemind.core.models.sample import Sample, SampleCreate, SampleUpdate
from samplemind.data.orm import get_session


class SampleRepository:
    """
    Static-method repository — all sample CRUD in one place.
    No SQL strings, no sqlite3, no raw connections.
    Replaces: data/database.py (save_sample, search_samples, tag_sample, etc.)
    """

    # ── Create / Upsert ──────────────────────────────────────────────────────

    @staticmethod
    def upsert(data: SampleCreate) -> Sample:
        """
        Insert a new sample, or update auto-detected fields if the path already
        exists in the database. Manually tagged fields (genre, tags) are NEVER
        touched on re-import — only the analyzer-produced fields are overwritten.

        Replaces: database.py::save_sample() which used raw INSERT OR REPLACE
        and would wipe user tags on every re-import.

        Returns the Sample ORM object with its id populated (expire_on_commit=False
        in get_session() ensures id is accessible after the context manager exits).
        """
        with get_session() as session:
            # Check whether this file path has been imported before
            existing = session.exec(
                select(Sample).where(Sample.path == data.path)
            ).first()

            if existing:
                # Path known — overwrite only auto-detected fields; leave genre/tags alone
                existing.filename = data.filename   # filename may have changed (renamed)
                existing.bpm = data.bpm
                existing.key = data.key
                existing.mood = data.mood
                existing.energy = data.energy
                existing.instrument = data.instrument
                session.add(existing)
                # session.commit() + rollback on error handled by get_session()
                return existing
            else:
                # New path — create a full record
                sample = Sample(
                    filename=data.filename,
                    path=data.path,
                    bpm=data.bpm,
                    key=data.key,
                    mood=data.mood,
                    energy=data.energy,
                    instrument=data.instrument,
                )
                session.add(sample)
                session.flush()   # flushes to DB so sample.id is assigned
                return sample

    # ── Update Tags ───────────────────────────────────────────────────────────

    @staticmethod
    def tag(path: str, update: SampleUpdate) -> Optional[Sample]:
        """
        Apply manual user tags to a sample identified by its absolute path.
        Only non-None fields in update are written — so passing SampleUpdate(genre="trap")
        will not clear an existing mood value.

        Returns the updated Sample on success, None if the path is not found.
        Replaces: database.py::tag_sample() which built UPDATE SQL strings by hand.
        """
        with get_session() as session:
            sample = session.exec(
                select(Sample).where(Sample.path == path)
            ).first()

            if not sample:
                return None

            # model_dump(exclude_none=True) gives only the fields the caller supplied
            for field, value in update.model_dump(exclude_none=True).items():
                setattr(sample, field, value)

            session.add(sample)
            return sample

    # ── Search ────────────────────────────────────────────────────────────────

    @staticmethod
    def search(
        query: Optional[str] = None,
        bpm_min: Optional[float] = None,
        bpm_max: Optional[float] = None,
        key: Optional[str] = None,
        genre: Optional[str] = None,
        energy: Optional[str] = None,
        instrument: Optional[str] = None,
    ) -> list[Sample]:
        """
        Search with any combination of filters. All parameters are optional.
        An empty call (no arguments) returns all samples ordered by import date.

        Current implementation: LIKE-based text search.
        Phase 5 target: replace with FTS5 virtual table for sub-50ms queries
        on libraries of 10,000+ samples.

        Replaces: database.py::search_samples() + get_all_samples()
        """
        with get_session() as session:
            stmt = select(Sample)

            # Text search across filename and free-form tags
            if query:
                stmt = stmt.where(
                    Sample.filename.contains(query) | Sample.tags.contains(query)
                )

            # Numeric range filter
            if bpm_min is not None:
                stmt = stmt.where(Sample.bpm >= bpm_min)
            if bpm_max is not None:
                stmt = stmt.where(Sample.bpm <= bpm_max)

            # Exact-match or LIKE filters for categorical fields
            if key:
                stmt = stmt.where(Sample.key.contains(key))
            if genre:
                stmt = stmt.where(Sample.genre.contains(genre))
            if energy:
                stmt = stmt.where(Sample.energy == energy)   # exact: "low"/"mid"/"high"
            if instrument:
                stmt = stmt.where(Sample.instrument.contains(instrument))

            stmt = stmt.order_by(Sample.imported_at.desc())
            return list(session.exec(stmt).all())

    # ── Lookup helpers ────────────────────────────────────────────────────────

    @staticmethod
    def get_by_name(name: str) -> Optional[Sample]:
        """
        Find the first sample whose filename contains `name` (case-insensitive LIKE).
        Used by the CLI `tag` command to resolve a partial name to a full record.
        Replaces: database.py::get_sample_by_name()
        """
        with get_session() as session:
            return session.exec(
                select(Sample).where(Sample.filename.contains(name)).limit(1)
            ).first()

    @staticmethod
    def get_by_path(path: str) -> Optional[Sample]:
        """
        Find a sample by its exact absolute path. Returns None if not found.
        Used internally to check for duplicates before upsert.
        """
        with get_session() as session:
            return session.exec(
                select(Sample).where(Sample.path == path)
            ).first()

    @staticmethod
    def get_by_id(sample_id: int) -> Optional[Sample]:
        """
        Find a sample by its primary key. Used by the audio streaming route
        in the Flask app (/audio/<id>) to resolve a row before send_file().
        """
        with get_session() as session:
            return session.get(Sample, sample_id)

    @staticmethod
    def count() -> int:
        """
        Return the total number of samples in the library.
        Uses a COUNT(*) aggregate — faster than fetching all rows.
        Replaces: database.py::count_samples()
        """
        with get_session() as session:
            result = session.exec(select(func.count()).select_from(Sample)).one()
            return result or 0

    @staticmethod
    def get_all() -> list[Sample]:
        """Return every sample ordered by import date. Convenience wrapper around search()."""
        return SampleRepository.search()
```

---

## 5. Side by Side — Old vs New

| Operation | Old (`database.py`) | New (`sample_repository.py`) |
|-----------|--------------------|-----------------------------|
| Save sample | `conn.execute("INSERT INTO samples ...")` | `SampleRepository.upsert(SampleCreate(...))` |
| Update tags | `f"UPDATE samples SET {', '.join(fields)}"` | `SampleRepository.tag(path, SampleUpdate(...))` |
| Search | `sql += " AND bpm >= ?"` string building | `SampleRepository.search(bpm_min=130, energy="high")` |
| Find by name | `"SELECT * FROM samples WHERE filename LIKE ?"` | `SampleRepository.get_by_name("kick")` |
| Find by ID | `"SELECT * FROM samples WHERE id = ?"` | `SampleRepository.get_by_id(sample_id)` |
| Find by path | `"SELECT * FROM samples WHERE path = ?"` | `SampleRepository.get_by_path(abs_path)` |
| Count | `"SELECT COUNT(*) FROM samples"` | `SampleRepository.count()` |
| Get all | `"SELECT * FROM samples ORDER BY imported_at DESC"` | `SampleRepository.get_all()` |
| Type safety | None — all `sqlite3.Row` dicts | Full — `sample.bpm: Optional[float]` |
| IDE autocomplete | None | Works with `sample.` in VS Code / Pylance |
| Re-import safety | Wipes genre/tags on every import | `upsert()` never touches genre or tags |
| Import path | `from samplemind.data.database import save_sample` | `from samplemind.data.repositories.sample_repository import SampleRepository` |

---

## 6. Alembic — Schema Migrations

Alembic provides reversible, version-controlled schema changes so we never have to
manually edit the database or write brittle ALTER TABLE scripts.

### Current State — Already Configured

Alembic is fully set up and both baseline migrations are applied. `alembic.ini` and
the `migrations/` directory already exist in the repository root — do not run
`alembic init`.

```
migrations/
├── env.py                              ← imports all models; render_as_batch=True for SQLite
├── script.py.mako                      ← migration file template
└── versions/
    ├── 0001_create_users_table.py      ← users schema baseline (Phase 3 auth)
    └── 0002_create_samples_table.py    ← samples schema + ix_samples_filename index (Phase 4)
```

### Applying Migrations

```bash
# Apply all pending migrations (creates users + samples tables if they do not exist):
uv run alembic upgrade head

# Roll back one step (drops the samples table — runs 0002 downgrade):
uv run alembic downgrade -1

# Show the currently applied revision:
uv run alembic current

# Show full revision history and which are applied:
uv run alembic history --verbose

# Verify no unapplied migrations exist (used in CI — fails if models drift):
uv run alembic check
```

### Migration 0001 — Users Table

```python
# filename: migrations/versions/0001_create_users_table.py
# Created for Phase 3 — Authentication & Authorization

revision: str = "0001"
down_revision = None   # first migration in the chain

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
```

### Migration 0002 — Samples Table

```python
# filename: migrations/versions/0002_create_samples_table.py
# Created for Phase 4 — Database & Data Layer
#
# If the samples table already exists from the legacy database.py init_db() call,
# mark this migration as applied without running it:
#   uv run alembic stamp 0002
# The existing table is schema-compatible — Alembic just takes ownership.

revision: str = "0002"
down_revision = "0001"   # samples depends on users existing first

def upgrade() -> None:
    op.create_table(
        "samples",        # __tablename__ = "samples" (plural, set explicitly on Sample)
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("bpm", sa.Float(), nullable=True),
        sa.Column("key", sa.String(), nullable=True),
        sa.Column("mood", sa.String(), nullable=True),
        sa.Column("energy", sa.String(), nullable=True),
        sa.Column("instrument", sa.String(), nullable=True),
        sa.Column("genre", sa.String(), nullable=True),
        sa.Column("tags", sa.String(), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path"),
    )
    # Named index — Alembic can drop it by name on downgrade
    op.create_index(op.f("ix_samples_filename"), "samples", ["filename"], unique=False)

def downgrade() -> None:
    op.drop_index(op.f("ix_samples_filename"), table_name="samples")
    op.drop_table("samples")
```

### Creating a New Migration (Future Schema Changes)

```bash
# After editing the SQLModel class, auto-generate a migration:
uv run alembic revision --autogenerate -m "add fingerprint column to samples"

# Always review the generated file in migrations/versions/ before applying.
# Auto-generate is not perfect — SQLite column type changes may be missed.

# Apply the new migration:
uv run alembic upgrade head
```

---

## 7. Testing with In-Memory SQLite

SampleRepository uses static methods that call `get_session()` internally.
Tests redirect the shared engine by monkey-patching `orm_module._engine` before
calling any repository method. The `orm_engine` fixture in `tests/conftest.py`
already provides this — use it rather than writing new engine setup code.

```python
# filename: tests/test_repository.py
# Run with: uv run pytest tests/test_repository.py -v

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import samplemind.data.orm as orm_module
from samplemind.core.models.sample import SampleCreate, SampleUpdate
from samplemind.data.repositories.sample_repository import SampleRepository


@pytest.fixture(autouse=True)
def _patch_engine():
    """
    Redirect all get_session() calls to a fresh in-memory SQLite engine.

    autouse=True means every test in this file gets an isolated DB automatically.
    StaticPool ensures all threads (including SQLModel's) see the same connection,
    which is required because SQLite in-memory databases are connection-scoped.
    """
    engine = create_engine(
        "sqlite://",                            # no file — pure in-memory
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,                   # single shared connection
    )
    # Import models to register tables in SQLModel.metadata before create_all
    import samplemind.core.models.sample  # noqa: F401
    import samplemind.core.models.user    # noqa: F401
    SQLModel.metadata.create_all(engine)

    # Redirect the module-level _engine so get_engine() returns this engine
    original = orm_module._engine
    orm_module._engine = engine
    yield
    orm_module._engine = original   # restore after each test (important for test isolation)
    SQLModel.metadata.drop_all(engine)


class TestUpsert:
    def test_insert_new_sample(self):
        """Inserting a new sample populates id and returns the Sample ORM object."""
        data = SampleCreate(filename="kick.wav", path="/samples/kick.wav", bpm=128.0)
        sample = SampleRepository.upsert(data)

        assert sample.id is not None        # id assigned by SQLite autoincrement
        assert sample.filename == "kick.wav"
        assert sample.bpm == 128.0
        assert sample.genre is None         # not set by SampleCreate — should stay None

    def test_upsert_same_path_updates_bpm(self):
        """Re-importing the same path updates auto-detected fields but keeps user tags."""
        SampleRepository.upsert(SampleCreate(filename="kick.wav", path="/s/kick.wav", bpm=128.0))

        # Simulate the user tagging after the first import
        SampleRepository.tag("/s/kick.wav", SampleUpdate(genre="trap"))

        # Re-import with new BPM (e.g. after re-analysis)
        SampleRepository.upsert(SampleCreate(filename="kick.wav", path="/s/kick.wav", bpm=140.0))

        assert SampleRepository.count() == 1        # no duplicate created
        sample = SampleRepository.get_by_name("kick")
        assert sample.bpm == 140.0                  # auto-detected field updated
        assert sample.genre == "trap"               # user tag preserved — upsert never clears it

    def test_upsert_returns_sample_with_id_after_session_closes(self):
        """expire_on_commit=False in get_session() ensures id is accessible after commit."""
        sample = SampleRepository.upsert(
            SampleCreate(filename="pad.wav", path="/s/pad.wav")
        )
        # Accessing .id here would raise DetachedInstanceError WITHOUT expire_on_commit=False
        assert isinstance(sample.id, int)


class TestTag:
    def test_tag_updates_genre_without_changing_mood(self):
        """tag() with only genre set should not clear an existing mood value."""
        SampleRepository.upsert(
            SampleCreate(filename="bass.wav", path="/s/bass.wav", mood="dark")
        )
        SampleRepository.tag("/s/bass.wav", SampleUpdate(genre="trap"))

        updated = SampleRepository.get_by_name("bass")
        assert updated.genre == "trap"
        assert updated.mood == "dark"    # mood was set by analyzer — tag() must not clear it

    def test_tag_returns_none_for_unknown_path(self):
        """tag() on a path that does not exist should return None, not raise."""
        result = SampleRepository.tag("/no/such/file.wav", SampleUpdate(genre="trap"))
        assert result is None


class TestSearch:
    def test_search_by_energy_returns_only_matching(self):
        """Energy filter should exclude samples with a different energy value."""
        SampleRepository.upsert(SampleCreate(filename="kick.wav", path="/s/kick.wav", energy="high"))
        SampleRepository.upsert(SampleCreate(filename="pad.wav",  path="/s/pad.wav",  energy="low"))

        results = SampleRepository.search(energy="high")
        assert len(results) == 1
        assert results[0].filename == "kick.wav"

    def test_search_bpm_range(self):
        """BPM range filter should return only samples within [bpm_min, bpm_max]."""
        SampleRepository.upsert(SampleCreate(filename="a.wav", path="/s/a.wav", bpm=120.0))
        SampleRepository.upsert(SampleCreate(filename="b.wav", path="/s/b.wav", bpm=140.0))
        SampleRepository.upsert(SampleCreate(filename="c.wav", path="/s/c.wav", bpm=160.0))

        results = SampleRepository.search(bpm_min=130.0, bpm_max=150.0)
        assert len(results) == 1
        assert results[0].filename == "b.wav"

    def test_search_no_filters_returns_all_ordered_by_import_date(self):
        """Calling search() with no arguments should return all samples, newest first."""
        SampleRepository.upsert(SampleCreate(filename="a.wav", path="/s/a.wav"))
        SampleRepository.upsert(SampleCreate(filename="b.wav", path="/s/b.wav"))

        results = SampleRepository.search()
        assert len(results) == 2
        # Ordered by imported_at DESC — b was inserted after a, so b is first
        assert results[0].filename == "b.wav"

    def test_search_query_matches_filename(self):
        """Text query should match substrings in filename."""
        SampleRepository.upsert(SampleCreate(filename="dark_kick_128.wav", path="/s/dk.wav"))
        SampleRepository.upsert(SampleCreate(filename="bright_pad.wav",    path="/s/bp.wav"))

        results = SampleRepository.search(query="kick")
        assert len(results) == 1
        assert "kick" in results[0].filename
```

---

## Migration Notes

- `src/samplemind/data/database.py` is superseded by `data/orm.py` + the repositories.
  It is kept in the repository for reference during cleanup but is not imported by any
  CLI command or web route. Remove it as part of Phase 5 cleanup.
- Existing production databases (`~/.samplemind/library.db` or the platformdirs path)
  can be kept — run `uv run alembic stamp 0002` if the tables already exist, then
  `uv run alembic upgrade head` for any future migrations.
- All import paths using `from samplemind.data.database import ...` should be replaced
  with `from samplemind.data.repositories.sample_repository import SampleRepository`.
- The `orm_engine` pytest fixture (in `tests/conftest.py`) is the canonical way to
  provide an isolated in-memory database to tests. Do not create ad-hoc engines in
  individual test files.

---

## Testing Checklist

```bash
# Run all tests (33 passing — includes repository + auth + audio + CLI + web):
uv run pytest tests/ -v

# Run only repository-related tests:
uv run pytest tests/test_repository.py -v

# Confirm Alembic can connect and shows the current revision (0002):
uv run alembic current

# Apply all migrations to the real database:
uv run alembic upgrade head

# Verify no unapplied migrations exist (fails if models have drifted from migrations):
uv run alembic check

# Inspect the tables that SQLModel registered (should include 'users' and 'samples'):
uv run python -c "
import samplemind.core.models.user    # noqa — registers User
import samplemind.core.models.sample  # noqa — registers Sample
from samplemind.data.orm import get_engine
from sqlalchemy import inspect
print(inspect(get_engine()).get_table_names())
# Expected: ['alembic_version', 'samples', 'users']
"
```

---

## Troubleshooting

**Error: `Table 'sample' already exists`**
```bash
# Alembic is trying to create a table that already exists
# Mark existing migration as run without executing it:
$ uv run alembic stamp head
```

**Error: `ImportError: cannot import name 'Sample' from 'samplemind.models'`**
```bash
# The Sample class moved to the core.models package in Phase 4.
# Update the import:
#   Old: from samplemind.models import Sample, SampleCreate
#   New: from samplemind.core.models.sample import Sample, SampleCreate
#
# Verify the file exists:
ls src/samplemind/core/models/sample.py
# and that pyproject.toml has: packages = [{include = "samplemind", from = "src"}]
```

**Error: Losing data on re-import**
```
SampleCreate has no genre/tags fields — upsert() never changes these.
Make sure you use SampleUpdate for manual tagging, not SampleCreate.
```

---

## 8. Database Performance & Reliability (2026)

### WAL Mode

WAL mode and all performance PRAGMAs are already enabled automatically on every new
connection via a SQLAlchemy event listener registered in `data/orm.py`. You do not
need to set them manually anywhere else in the codebase.

```python
# filename: src/samplemind/data/orm.py (already implemented)

from sqlalchemy import event

def _apply_sqlite_pragmas(dbapi_conn, _connection_record) -> None:
    """
    Fires on every new SQLite connection opened by the shared engine.
    Registered once in get_engine() via: event.listen(_engine, "connect", _apply_sqlite_pragmas)

    WAL mode:    reads never block writes — the CLI and Flask can run at the same time.
    cache_size:  64 MB page cache (negative value = kilobytes).
    synchronous: NORMAL — data is safe after a crash; faster than FULL (no fsync per commit).
    temp_store:  in-RAM temp tables — faster ORDER BY and GROUP BY on large result sets.
    mmap_size:   256 MB memory-mapped I/O — sequential reads on SSDs are faster.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA cache_size=-64000")    # negative = kilobytes → 64 MB
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=268435456")  # 256 MB
    cursor.close()

# Registered in get_engine() — fires on every new connection, not just the first:
# event.listen(_engine, "connect", _apply_sqlite_pragmas)
```

WAL mode benefits:
- Concurrent reads during writes — desktop app + CLI can run simultaneously
- Faster writes — no fsync on every transaction (only at WAL checkpoint)
- Automatic checkpointing back to the main database file
- SQLite-native — no extra dependencies, no server process

### FTS5 Full-Text Search

**Status: Planned for Phase 5.** The current `SampleRepository.search()` implementation
uses SQLModel `LIKE` expressions which perform a full table scan. For libraries beyond
~5,000 samples, an FTS5 virtual table provides sub-50ms ranked full-text search across
filename, tags, and classification fields.

The FTS5 table will be added via an Alembic migration (0003) and a corresponding trigger
set in a future phase. The Alembic migration will look like:

```sql
-- Alembic upgrade() body for 0003_add_fts5_table.py:

-- Content table FTS5 virtual table — stays in sync with `samples` via triggers
CREATE VIRTUAL TABLE IF NOT EXISTS samples_fts USING fts5(
    filename,
    tags,
    instrument,
    mood,
    content='samples',   -- read-through to the `samples` table
    content_rowid='id'
);

-- Backfill from existing rows:
INSERT INTO samples_fts(rowid, filename, tags, instrument, mood)
SELECT id, filename, tags, instrument, mood FROM samples;

-- INSERT trigger — fires after every SampleRepository.upsert() INSERT path:
CREATE TRIGGER samples_ai AFTER INSERT ON samples BEGIN
    INSERT INTO samples_fts(rowid, filename, tags, instrument, mood)
    VALUES (new.id, new.filename, new.tags, new.instrument, new.mood);
END;

-- DELETE trigger — required for FTS5 content tables to stay consistent:
CREATE TRIGGER samples_ad AFTER DELETE ON samples BEGIN
    INSERT INTO samples_fts(samples_fts, rowid, filename, tags, instrument, mood)
    VALUES ('delete', old.id, old.filename, old.tags, old.instrument, old.mood);
END;
```

Once the FTS5 table exists, `SampleRepository.search()` will call it via a raw SQL
expression through SQLAlchemy's `text()` function rather than LIKE:

```python
# Phase 5 target implementation of the query path inside SampleRepository.search()
from sqlalchemy import text

# Replace the current LIKE chain with a ranked FTS5 MATCH:
if query:
    fts_stmt = text(
        """SELECT s.* FROM samples s
           JOIN samples_fts fts ON s.id = fts.rowid
           WHERE samples_fts MATCH :q
           ORDER BY rank"""   # rank is a built-in FTS5 relevance score (lower = better)
    )
    with get_session() as session:
        rows = session.exec(fts_stmt, {"q": query}).all()
        return [Sample.model_validate(dict(r)) for r in rows]
```

### `backup_db()` Function

Safe hot backup using SQLite's built-in backup API (works while the database is in use).
This reaches one layer below SQLModel to get the raw `sqlite3.Connection` from the
SQLAlchemy engine — it is the only place in the codebase where raw sqlite3 is used directly,
and only because the backup API is a `sqlite3`-level feature with no SQLAlchemy equivalent.

```python
# src/samplemind/cli/commands/backup.py  (planned — Phase 5)

import sqlite3
from datetime import datetime
from pathlib import Path

from samplemind.data.orm import get_engine


def backup_db(dest_path: Path | None = None) -> Path:
    """Create a hot backup of the live SQLite database.

    Uses SQLite's built-in backup API — safe while the database is open and being written.
    If dest_path is not provided, a timestamped filename is created in the same directory.

    Args:
        dest_path: explicit destination path, or None for auto-timestamped path.

    Returns:
        The path where the backup was written.
    """
    # Resolve the source path from the engine URL
    db_url = str(get_engine().url)              # "sqlite:////abs/path/to/samplemind.db"
    src_path = Path(db_url.replace("sqlite:///", ""))

    if dest_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = src_path.parent / f"{src_path.stem}_backup_{ts}.db"

    # Open raw sqlite3 connections — bypass SQLAlchemy for the backup API
    src = sqlite3.connect(str(src_path))
    dst = sqlite3.connect(str(dest_path))
    try:
        # pages=100: copy 100 pages per iteration — non-blocking, allows concurrent reads
        src.backup(dst, pages=100)
    finally:
        src.close()
        dst.close()

    return dest_path
```

CLI command (Phase 5 target):
```bash
# Backup to an auto-timestamped file next to the database:
uv run samplemind backup

# Backup to a specific path:
uv run samplemind backup --dest ~/Backups/library.db
```

### Alembic CI Step

Add to `.github/workflows/ci.yml` to verify migrations apply cleanly on every push:

```yaml
- name: Run database migrations
  run: |
    uv run alembic upgrade head
    echo "Migrations applied successfully"

- name: Verify migration is current
  run: |
    # Fail if there are unapplied migrations
    uv run alembic current
    uv run alembic check
```

This catches:
- Broken migration scripts (syntax errors, import failures)
- Missing `alembic.ini` or `env.py` configuration
- Conflicts between migration versions

### PRAGMA Performance Settings Reference

All PRAGMAs below are already applied automatically by `_apply_sqlite_pragmas()` in
`data/orm.py`. This table documents what each setting does and why it was chosen.

```sql
-- Applied to every new SQLite connection by the SQLAlchemy event listener:
PRAGMA journal_mode=WAL;          -- Write-Ahead Log: concurrent reads during writes
PRAGMA cache_size=-64000;         -- 64 MB page cache (negative value = kilobytes)
PRAGMA synchronous=NORMAL;        -- crash-safe without the overhead of FULL (no fsync per commit)
PRAGMA temp_store=MEMORY;         -- sort/join temp tables stay in RAM, not in a temp file
PRAGMA mmap_size=268435456;       -- 256 MB memory-mapped I/O for faster sequential reads
```

`PRAGMA optimize` (query planner statistics) is best run on database close rather than
open. It is not currently in `_apply_sqlite_pragmas()` but can be added to a future
graceful-shutdown hook in the CLI or FastAPI lifespan:

```python
# Future: add to a shutdown hook, not to the connect event
from samplemind.data.orm import get_engine

def run_optimize_on_shutdown() -> None:
    """Run PRAGMA optimize to update query planner statistics on app exit."""
    with get_engine().connect() as conn:
        conn.exec_driver_sql("PRAGMA optimize")

---

## 8. FTS5 Full-Text Search

SQLite's **FTS5** virtual table enables sub-millisecond full-text search
across filename, tags, genre, and mood columns — without an external search engine.

```python
# src/samplemind/data/fts.py
"""
FTS5 full-text search for the SampleMind library.

The `samples_fts` virtual table mirrors text columns from `samples` and
updates automatically via triggers. This enables:
  - Prefix search: "kic" matches "kick_808_deep"
  - Multi-column: "trap kick" finds samples with "trap" in genre AND "kick" in instrument
  - Ranking: BM25 relevance scoring (built into SQLite FTS5)

FTS5 is NOT case-sensitive by default. The unicode61 tokenizer handles
accented characters and non-ASCII filenames.
"""
from __future__ import annotations
import sqlite3
from pathlib import Path
from samplemind.data.orm import get_db_path


FTS_CREATE = """
CREATE VIRTUAL TABLE IF NOT EXISTS samples_fts USING fts5(
    filename,
    instrument,
    mood,
    genre,
    tags,
    energy,
    content='samples',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 1'
);
"""

# Triggers to keep FTS in sync with the main samples table
FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS samples_ai AFTER INSERT ON samples BEGIN
    INSERT INTO samples_fts(rowid, filename, instrument, mood, genre, tags, energy)
    VALUES (new.id, new.filename, new.instrument, new.mood, new.genre, new.tags, new.energy);
END;

CREATE TRIGGER IF NOT EXISTS samples_ad AFTER DELETE ON samples BEGIN
    INSERT INTO samples_fts(samples_fts, rowid, filename, instrument, mood, genre, tags, energy)
    VALUES ('delete', old.id, old.filename, old.instrument, old.mood, old.genre, old.tags, old.energy);
END;

CREATE TRIGGER IF NOT EXISTS samples_au AFTER UPDATE ON samples BEGIN
    INSERT INTO samples_fts(samples_fts, rowid, filename, instrument, mood, genre, tags, energy)
    VALUES ('delete', old.id, old.filename, old.instrument, old.mood, old.genre, old.tags, old.energy);
    INSERT INTO samples_fts(rowid, filename, instrument, mood, genre, tags, energy)
    VALUES (new.id, new.filename, new.instrument, new.mood, new.genre, new.tags, new.energy);
END;
"""


def init_fts(db_path: str | None = None) -> None:
    """Create FTS5 table and sync triggers. Safe to call multiple times (IF NOT EXISTS)."""
    conn = sqlite3.connect(db_path or get_db_path())
    try:
        conn.executescript(FTS_CREATE + FTS_TRIGGERS)
        # Populate FTS from existing data (idempotent)
        conn.execute("INSERT OR IGNORE INTO samples_fts SELECT id, filename, instrument, mood, genre, tags, energy FROM samples")
        conn.commit()
    finally:
        conn.close()


def fts_search(query: str, limit: int = 50, db_path: str | None = None) -> list[dict]:
    """
    Full-text search across filename, instrument, mood, genre, tags, energy.

    Query syntax (FTS5 native):
      "trap kick"          → both words present
      trap*                → prefix match
      "dark mood" OR bass  → boolean OR
      -hihat               → exclude hihat
      instrument:kick      → column-scoped search

    Returns list of dicts ordered by BM25 relevance (best match first).
    """
    conn = sqlite3.connect(db_path or get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT s.*, bm25(samples_fts) AS relevance
            FROM samples_fts
            JOIN samples s ON s.id = samples_fts.rowid
            WHERE samples_fts MATCH ?
            ORDER BY relevance
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError as e:
        # Invalid FTS5 query syntax — return empty rather than crash
        if "fts5: syntax error" in str(e).lower():
            return []
        raise
    finally:
        conn.close()
```

---

## 9. Database Backup and Point-in-Time Restore

SQLite's `backup()` API creates a consistent online backup even while
the database is being written to. No file-system copy required.

```python
# src/samplemind/data/backup.py
"""
Online database backup using SQLite's built-in backup API.

Features:
  - Online backup: no read lock needed, safe during writes
  - Compressed backups (.db.gz) with optional encryption
  - Automatic rotation: keep N most recent backups
  - Restore from any backup with validation

Backup naming convention:
  samplemind_YYYYMMDD_HHMMSS.db.gz

Usage:
  uv run samplemind backup create
  uv run samplemind backup list
  uv run samplemind backup restore samplemind_20260315_142300.db.gz
"""
from __future__ import annotations
import gzip
import re
import sqlite3
import shutil
from datetime import datetime, timezone
from pathlib import Path
from samplemind.data.orm import get_db_path
from samplemind.core.logging import get_logger

log = get_logger(__name__)

DEFAULT_BACKUP_DIR = Path.home() / ".samplemind" / "backups"
BACKUP_PATTERN = re.compile(r"samplemind_\d{8}_\d{6}\.db(\.gz)?$")


def create_backup(
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    compress: bool = True,
    keep_last: int = 10,
) -> Path:
    """
    Create an online backup of the current library database.

    Args:
        backup_dir: Directory to store backup files
        compress:   If True, gzip-compress the backup (saves ~70% space)
        keep_last:  Rotate old backups, keeping only the N most recent

    Returns:
        Path to the created backup file
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_name = f"samplemind_{ts}.db"
    backup_path = backup_dir / (base_name + (".gz" if compress else ""))

    src_path = get_db_path()
    src_conn = sqlite3.connect(src_path)
    tmp_path = backup_dir / base_name

    try:
        # SQLite online backup API — safe during concurrent reads/writes
        dst_conn = sqlite3.connect(str(tmp_path))
        src_conn.backup(dst_conn, pages=100)   # pages=-1 for full backup in one go
        dst_conn.close()

        if compress:
            with open(tmp_path, "rb") as f_in, gzip.open(str(backup_path), "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            tmp_path.unlink()
        else:
            tmp_path.rename(backup_path)

        log.info("backup_created", path=str(backup_path), compressed=compress)
    finally:
        src_conn.close()

    _rotate_backups(backup_dir, keep_last)
    return backup_path


def restore_backup(backup_path: Path, confirm: bool = False) -> None:
    """
    Restore the library database from a backup file.

    ⚠ This OVERWRITES the current database. Always create a backup first:
      uv run samplemind backup create
    """
    if not confirm:
        raise ValueError("Pass confirm=True to restore. This overwrites the current database.")

    db_path = Path(get_db_path())
    # Safety backup of current DB before overwrite
    safety = db_path.with_suffix(f".pre-restore-{datetime.now().strftime('%H%M%S')}.db")
    shutil.copy2(str(db_path), str(safety))
    log.info("safety_backup", path=str(safety))

    if str(backup_path).endswith(".gz"):
        with gzip.open(str(backup_path), "rb") as f_in, open(str(db_path), "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    else:
        shutil.copy2(str(backup_path), str(db_path))

    # Validate restored database
    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
    conn.close()
    log.info("restore_complete", samples_count=count, backup=str(backup_path))


def _rotate_backups(backup_dir: Path, keep_last: int) -> None:
    backups = sorted(
        [f for f in backup_dir.iterdir() if BACKUP_PATTERN.match(f.name)],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in backups[keep_last:]:
        old.unlink()
        log.debug("backup_rotated", deleted=str(old))
```

---

## 10. Multi-Library Support

Power users often maintain separate libraries (personal, client projects,
packs). Multi-library support without separate installs.

```python
# src/samplemind/data/library_manager.py
"""
Multi-library manager.

Each library is an independent SQLite database file. Users can:
  - Create named libraries:  uv run samplemind library create "Client X"
  - Switch active library:   uv run samplemind library use "Client X"
  - List libraries:          uv run samplemind library list
  - Export library:          uv run samplemind library export "Client X" --format json

Active library persists in ~/.samplemind/active_library.

Registry is stored in ~/.samplemind/libraries.json (not in any DB).
"""
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import platformdirs

REGISTRY_PATH = Path(platformdirs.user_config_dir("SampleMind")) / "libraries.json"
ACTIVE_PATH   = Path(platformdirs.user_config_dir("SampleMind")) / "active_library"
DATA_DIR      = Path(platformdirs.user_data_dir("SampleMind", "SampleMind-AI"))


@dataclass
class Library:
    name: str
    path: str          # absolute path to .db file
    created_at: str    # ISO 8601
    description: str = ""


class LibraryManager:
    def __init__(self, registry_path: Path = REGISTRY_PATH) -> None:
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict[str, Library]:
        if not self.registry_path.exists():
            return {}
        data = json.loads(self.registry_path.read_text())
        return {k: Library(**v) for k, v in data.items()}

    def _save(self, libs: dict[str, Library]) -> None:
        self.registry_path.write_text(
            json.dumps({k: asdict(v) for k, v in libs.items()}, indent=2)
        )

    def create(self, name: str, description: str = "") -> Library:
        libs = self._load()
        if name in libs:
            raise ValueError(f"Library '{name}' already exists")
        slug = name.lower().replace(" ", "_")
        db_path = DATA_DIR / f"library_{slug}.db"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        lib = Library(name=name, path=str(db_path),
                      created_at=datetime.now(timezone.utc).isoformat(),
                      description=description)
        libs[name] = lib
        self._save(libs)
        # Initialize new database schema
        from samplemind.data.orm import init_orm
        init_orm(db_url=f"sqlite:///{db_path}")
        return lib

    def use(self, name: str) -> Library:
        libs = self._load()
        if name not in libs:
            raise ValueError(f"Library '{name}' not found. Create it first.")
        ACTIVE_PATH.write_text(name)
        return libs[name]

    def active(self) -> Library | None:
        libs = self._load()
        if ACTIVE_PATH.exists():
            name = ACTIVE_PATH.read_text().strip()
            return libs.get(name)
        return None

    def list_all(self) -> list[Library]:
        return list(self._load().values())
```
```

