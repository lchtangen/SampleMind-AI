# Phase 3 Agent — Database

Handles: SQLModel ORM, Alembic migrations, repository pattern, FTS5 search, backup, multi-library.

## Triggers
- Phase 3, SQLModel, Alembic, ORM, repository, migration, FTS5, database backup, multi-library

## Key Files
- `src/samplemind/data/orm.py`
- `src/samplemind/data/repositories/`
- `src/samplemind/data/fts.py`
- `src/samplemind/data/backup.py`
- `migrations/versions/`

## PRAGMA Settings (apply on every connection open)

```sql
PRAGMA journal_mode=WAL;
PRAGMA cache_size = -64000;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
```

## Rules
1. All schema changes need Alembic migration: `uv run alembic revision --autogenerate`
2. Tests use in-memory SQLite: `create_engine("sqlite://")`
3. FTS5 virtual table `samples_fts` synced via triggers — never query `samples` for text
4. Never hardcode DB paths — use `platformdirs`
5. Energy values in SQL: ONLY `'low'`, `'mid'`, `'high'`

