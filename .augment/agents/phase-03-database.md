# Phase 3 Agent — Database & Migrations

Handles: SQLModel ORM, Alembic versioning, repository pattern, schema evolution.

## Triggers
Phase 3, SQLModel, Alembic, `alembic revision`, `alembic upgrade`, `SampleRepository`, `UserRepository`, `orm.py`, `get_engine()`, `init_orm`, `migrations/versions/`, "add a column", "change DB schema", "run migration"

**File patterns:** `src/samplemind/data/**/*.py`, `src/samplemind/core/models/sample.py`, `src/samplemind/core/models/user.py`, `migrations/**/*.py`, `alembic.ini`

**Code patterns:** `from sqlmodel import`, `SQLModel`, `Field(`, `create_engine(`, `init_orm()`, `get_engine()`, `alembic`, `op.add_column`, `SampleRepository`, `UserRepository`

## Key Files
- `src/samplemind/data/orm.py` — engine, session, PRAGMA config
- `src/samplemind/data/repositories/sample_repository.py`
- `src/samplemind/data/repositories/user_repository.py`
- `src/samplemind/core/models/sample.py` — SampleCreate, SampleUpdate, SamplePublic
- `src/samplemind/core/models/user.py` — User, UserCreate, UserPublic
- `migrations/versions/` — Alembic migration files

## Using SampleRepository
```python
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.data.orm import init_orm

init_orm()  # idempotent — safe to call multiple times
sample = SampleRepository.upsert(SampleCreate(filename="kick.wav", path="/abs/path", bpm=128.0))
results = SampleRepository.search(query="dark", energy="high", instrument="kick")
SampleRepository.tag("/abs/path", SampleUpdate(genre="trap", tags="808,heavy"))
```

## SQLite PRAGMA Settings (auto-applied via event listener in orm.py)
```python
PRAGMA journal_mode=WAL        # concurrent readers during writes
PRAGMA cache_size=-64000       # 64 MB page cache
PRAGMA synchronous=NORMAL      # safe + fast
PRAGMA temp_store=MEMORY
PRAGMA mmap_size=268435456     # 256 MB memory-mapped I/O
```

## Alembic Migration Workflow
```bash
uv run alembic revision --autogenerate -m "add_genre_column"
# Review migration file in migrations/versions/
uv run alembic upgrade head
uv run alembic check            # verify no drift (CI runs this)
```

## Rules
1. Never use raw sqlite3 in new code — use `SampleRepository` or `UserRepository`
2. Never import from `data/database.py` in new code (legacy — kept for reference only)
3. Schema changes require an Alembic migration file
4. DB file location from `get_settings().database_url` — never hardcode paths
5. Tests use `orm_engine` fixture (in-memory `StaticPool`) — never write to a file DB in tests

