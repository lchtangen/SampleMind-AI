# Phase 3 — Database & Data Layer

> Upgrade the raw `sqlite3` layer in `database.py` to **SQLModel** + SQLAlchemy 2.0 with
> Alembic migrations, type-safe models, and a Repository pattern.

---

## Prerequisites

- Phase 1 complete (uv + pyproject.toml)
- `sqlmodel` and `alembic` added to `pyproject.toml`
- Basic SQL knowledge is helpful

---

## Goal State

- `src/samplemind/models.py` with `Sample` SQLModel class
- `src/samplemind/repository.py` with `SampleRepository` class
- Alembic configured for schema migrations
- In-memory SQLite in pytest for isolated tests
- Existing `database.py` can be deleted

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
# filename: src/samplemind/models.py

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Sample(SQLModel, table=True):
    """
    Represents one sample in the library.

    table=True: SQLModel creates a database table for this class.
    Without table=True the class is used only for validation (Pydantic mode).
    """

    # Primary key — auto-incremented by SQLite
    id: Optional[int] = Field(default=None, primary_key=True)

    # File info — path is unique (same file cannot be imported twice)
    filename: str = Field(index=True)                    # Indexed for fast search
    path: str = Field(unique=True)                       # Unique constraint

    # Auto-detected fields (from analyzer)
    bpm: Optional[float] = Field(default=None)           # None = not yet analysed
    key: Optional[str] = Field(default=None)             # "C maj", "F# min", etc.
    mood: Optional[str] = Field(default=None)            # "dark", "chill", etc.
    energy: Optional[str] = Field(default=None)          # "low", "mid", "high"
    instrument: Optional[str] = Field(default=None)      # "kick", "snare", etc.

    # Manually tagged fields (from user)
    genre: Optional[str] = Field(default=None)           # "trap", "lofi", etc.
    tags: Optional[str] = Field(default=None)            # Comma-separated free tags

    # Timestamp — set automatically on insert
    imported_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class SampleCreate(SQLModel):
    """
    Pydantic model for creating a new sample (without id and imported_at).
    Used in API calls and CLI to validate input before saving.
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
    Pydantic model for updating tags (all fields optional).
    Used by the tagger command and web API.
    """
    genre: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[str] = None
    tags: Optional[str] = None
```

---

## 3. Database Connection and Engine

```python
# filename: src/samplemind/data/db.py

from pathlib import Path
from sqlmodel import create_engine, SQLModel, Session
import platformdirs


def _get_db_path() -> Path:
    """
    Find the correct database path based on platform.

    macOS:   ~/Library/Application Support/samplemind/library.db
    Linux:   ~/.local/share/samplemind/library.db
    Windows: C:\\Users\\User\\AppData\\Local\\samplemind\\library.db

    platformdirs handles all of this automatically per XDG standards.
    """
    data_dir = Path(platformdirs.user_data_dir("samplemind", "samplemind"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "library.db"


# Global engine object — created once on import
# connect_args={"check_same_thread": False} allows use from Flask threads
engine = create_engine(
    f"sqlite:///{_get_db_path()}",
    connect_args={"check_same_thread": False},
    echo=False,  # Set to True for SQL debug logging
)


def init_db():
    """
    Create all tables if they don't exist.
    Call this at app startup (Flask and CLI).
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """
    Context manager for database sessions.

    Usage:
        with get_session() as session:
            sample = session.get(Sample, 1)
    """
    return Session(engine)
```

---

## 4. The Repository Pattern

The Repository pattern wraps all database operations in one class. This makes it easy to
substitute the database in tests (e.g. with in-memory SQLite).

```python
# filename: src/samplemind/data/repository.py

from typing import Optional
from sqlmodel import Session, select
from samplemind.models import Sample, SampleCreate, SampleUpdate
from samplemind.data.db import get_session


class SampleRepository:
    """
    All database access for samples goes through this class.
    No SQL strings outside this file.
    """

    def __init__(self, session: Optional[Session] = None):
        # Allow injection of a test session (in-memory SQLite)
        self._session = session

    def _get_session(self) -> Session:
        return self._session or get_session()

    # ── Create / Upsert ──────────────────────────────────────────────────────

    def upsert(self, data: SampleCreate) -> Sample:
        """
        Insert a new sample, or update auto-detected fields if the path already
        exists. Manually tagged fields (genre, tags) are not touched.

        Replaces: database.py::save_sample() with raw INSERT ... ON CONFLICT
        """
        with self._get_session() as session:
            # Check if the path already exists
            existing = session.exec(
                select(Sample).where(Sample.path == data.path)
            ).first()

            if existing:
                # Update only auto-detected fields — preserve manual tags
                existing.bpm = data.bpm
                existing.key = data.key
                existing.mood = data.mood
                existing.energy = data.energy
                existing.instrument = data.instrument
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                # Insert new sample
                sample = Sample.model_validate(data)
                session.add(sample)
                session.commit()
                session.refresh(sample)
                return sample

    # ── Update Tags ───────────────────────────────────────────────────────────

    def tag(self, path: str, update: SampleUpdate) -> Optional[Sample]:
        """
        Update manual tags for a sample.
        Replaces: database.py::tag_sample()
        """
        with self._get_session() as session:
            sample = session.exec(
                select(Sample).where(Sample.path == path)
            ).first()

            if not sample:
                return None

            # Update only fields that are explicitly provided (not None)
            update_data = update.model_dump(exclude_none=True)
            for field, value in update_data.items():
                setattr(sample, field, value)

            session.add(sample)
            session.commit()
            session.refresh(sample)
            return sample

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query: Optional[str] = None,
        bpm_min: Optional[float] = None,
        bpm_max: Optional[float] = None,
        key: Optional[str] = None,
        genre: Optional[str] = None,
        energy: Optional[str] = None,
        instrument: Optional[str] = None,
    ) -> list[Sample]:
        """
        Search with combined filters. All filters are optional.
        Replaces: database.py::search_samples() with raw SQL string building.
        """
        with self._get_session() as session:
            stmt = select(Sample)

            # Full-text search on filename and tags
            if query:
                stmt = stmt.where(
                    Sample.filename.contains(query) | Sample.tags.contains(query)
                )

            # Numeric filters
            if bpm_min is not None:
                stmt = stmt.where(Sample.bpm >= bpm_min)
            if bpm_max is not None:
                stmt = stmt.where(Sample.bpm <= bpm_max)

            # Text filters (LIKE search for flexibility)
            if key:
                stmt = stmt.where(Sample.key.contains(key))
            if genre:
                stmt = stmt.where(Sample.genre.contains(genre))
            if energy:
                stmt = stmt.where(Sample.energy == energy)
            if instrument:
                stmt = stmt.where(Sample.instrument.contains(instrument))

            stmt = stmt.order_by(Sample.imported_at.desc())
            return session.exec(stmt).all()

    def get_by_name(self, name: str) -> Optional[Sample]:
        """Find sample by partial filename match. Replaces: get_sample_by_name()."""
        with self._get_session() as session:
            return session.exec(
                select(Sample).where(Sample.filename.contains(name)).limit(1)
            ).first()

    def count(self) -> int:
        """Number of samples in the library."""
        with self._get_session() as session:
            return len(session.exec(select(Sample)).all())

    def get_all(self) -> list[Sample]:
        """Get all samples — used by export functionality."""
        return self.search()
```

---

## 5. Side by Side — Old vs New

| Operation | Old (`database.py`) | New (`repository.py`) |
|-----------|--------------------|-----------------------|
| Save sample | `conn.execute("INSERT INTO samples ...")` | `repo.upsert(SampleCreate(...))` |
| Update tags | `f"UPDATE samples SET {', '.join(fields)}"` | `repo.tag(path, SampleUpdate(...))` |
| Search | `sql += " AND bpm >= ?"` string building | `stmt = stmt.where(Sample.bpm >= bpm_min)` |
| Find by name | `"SELECT * FROM samples WHERE filename LIKE ?"` | `repo.get_by_name("kick")` |
| Count | `"SELECT COUNT(*) FROM samples"` | `repo.count()` |
| Type safety | None — all `sqlite3.Row` | Full — `sample.bpm: Optional[float]` |
| IDE autocomplete | None | Works with `sample.` in VS Code |

---

## 6. Alembic — Schema Migrations

Alembic tracks schema changes over time, replacing the current `_migrate()` hack that can fail
on complex changes.

### Setup

```bash
# Install Alembic (add to pyproject.toml under dependencies)
$ uv add alembic

# Initialise Alembic in the project
$ uv run alembic init alembic
```

```ini
# filename: alembic.ini (update sqlalchemy.url)
[alembic]
script_location = alembic

# Point to SQLite database (same path as in db.py)
# %(here)s = the directory where alembic.ini resides
sqlalchemy.url = sqlite:///%(here)s/../data/dev.db
```

```python
# filename: alembic/env.py (update target_metadata)

from samplemind.models import Sample      # Import all models
from sqlmodel import SQLModel

# Tell Alembic which tables to track
target_metadata = SQLModel.metadata
```

### First Migration

```bash
# Auto-generate migration file from model definitions
$ uv run alembic revision --autogenerate -m "initial_schema"

# Run the migration (creates the table)
$ uv run alembic upgrade head

# View history
$ uv run alembic history
```

Generated migration file (example):

```python
# filename: alembic/versions/0001_initial_schema.py

"""initial_schema

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        "sample",                              # SQLModel uses classname in lowercase
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("filename", sa.String, nullable=False, index=True),
        sa.Column("path", sa.String, nullable=False, unique=True),
        sa.Column("bpm", sa.Float, nullable=True),
        sa.Column("key", sa.String, nullable=True),
        sa.Column("mood", sa.String, nullable=True),
        sa.Column("energy", sa.String, nullable=True),
        sa.Column("instrument", sa.String, nullable=True),
        sa.Column("genre", sa.String, nullable=True),
        sa.Column("tags", sa.String, nullable=True),
        sa.Column("imported_at", sa.DateTime, nullable=True),
    )

def downgrade():
    op.drop_table("sample")
```

---

## 7. Testing with In-Memory SQLite

```python
# filename: tests/test_repository.py

import pytest
from sqlmodel import create_engine, SQLModel, Session
from samplemind.models import Sample, SampleCreate, SampleUpdate
from samplemind.data.repository import SampleRepository


@pytest.fixture
def in_memory_session():
    """
    Creates an isolated in-memory SQLite database for each test.
    No data leaks between tests.
    """
    # sqlite:// (no file path) = in-memory database
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session  # Provide session to the test


@pytest.fixture
def repo(in_memory_session):
    """SampleRepository connected to in-memory test database."""
    return SampleRepository(session=in_memory_session)


class TestUpsert:
    def test_insert_new_sample(self, repo):
        """Inserting a new sample should succeed and return a Sample object."""
        data = SampleCreate(filename="kick.wav", path="/samples/kick.wav", bpm=128.0)
        sample = repo.upsert(data)

        assert sample.id is not None
        assert sample.filename == "kick.wav"
        assert sample.bpm == 128.0

    def test_upsert_same_path_updates_bpm(self, repo):
        """Re-importing the same path should update BPM, not create a duplicate."""
        repo.upsert(SampleCreate(filename="kick.wav", path="/samples/kick.wav", bpm=128.0))
        repo.upsert(SampleCreate(filename="kick.wav", path="/samples/kick.wav", bpm=140.0))

        # Should still be only one sample
        assert repo.count() == 1
        # BPM should be updated
        sample = repo.get_by_name("kick")
        assert sample.bpm == 140.0


class TestTag:
    def test_tag_updates_genre(self, repo):
        """Tagging should update genre without changing other fields."""
        repo.upsert(SampleCreate(filename="bass.wav", path="/s/bass.wav", mood="dark"))

        sample = repo.get_by_name("bass")
        repo.tag(sample.path, SampleUpdate(genre="trap"))

        updated = repo.get_by_name("bass")
        assert updated.genre == "trap"
        assert updated.mood == "dark"   # Unchanged


class TestSearch:
    def test_search_by_energy(self, repo):
        """Searching by energy filter should return only matching samples."""
        repo.upsert(SampleCreate(filename="kick.wav", path="/s/kick.wav", energy="high"))
        repo.upsert(SampleCreate(filename="pad.wav", path="/s/pad.wav", energy="low"))

        results = repo.search(energy="high")
        assert len(results) == 1
        assert results[0].filename == "kick.wav"

    def test_search_bpm_range(self, repo):
        """BPM range filter should return samples within the range."""
        repo.upsert(SampleCreate(filename="a.wav", path="/s/a.wav", bpm=120.0))
        repo.upsert(SampleCreate(filename="b.wav", path="/s/b.wav", bpm=140.0))
        repo.upsert(SampleCreate(filename="c.wav", path="/s/c.wav", bpm=160.0))

        results = repo.search(bpm_min=130.0, bpm_max=150.0)
        assert len(results) == 1
        assert results[0].filename == "b.wav"
```

---

## Migration Notes

- `src/data/database.py` can be deleted after `repository.py` is implemented and tested
- Existing `~/.samplemind/library.db` can be kept — Alembic can migrate it
- All import paths using `from data.database import ...` update to
  `from samplemind.data.repository import SampleRepository`

---

## Testing Checklist

```bash
# Run repository tests
$ uv run pytest tests/test_repository.py -v

# Confirm Alembic can connect
$ uv run alembic current

# Run all migrations
$ uv run alembic upgrade head

# Check that the table exists
$ python -c "
from samplemind.data.db import engine
from sqlalchemy import inspect
print(inspect(engine).get_table_names())
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

**Error: `ImportError: cannot import name 'Sample'`**
```bash
# Check models.py is in the correct folder:
$ ls src/samplemind/models.py
# and that pyproject.toml points to src/
```

**Error: Losing data on re-import**
```
SampleCreate has no genre/tags fields — upsert() never changes these.
Make sure you use SampleUpdate for manual tagging, not SampleCreate.
```
