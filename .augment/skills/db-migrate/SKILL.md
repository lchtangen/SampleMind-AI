---
name: db-migrate
description: Generate and apply Alembic database migrations for SQLModel schema changes
---

# Skill: db-migrate

Generate and apply Alembic database migrations for SQLModel schema changes.
Requires Phase 3 to be implemented (`alembic.ini` and `migrations/` must exist).

## When to use

Use this skill when the user asks to:
- Add a new column or table to the database
- Apply pending migrations
- Check current migration state
- Roll back a migration
- Verify there is no schema drift

## Commands

### Check current state
```bash
uv run alembic current    # show active revision
uv run alembic history    # show all migrations
uv run alembic check      # verify no drift between models and DB (used by CI)
```

### Generate a new migration
```bash
uv run alembic revision --autogenerate -m "<short_snake_case_description>"
```
Example:
```bash
uv run alembic revision --autogenerate -m "add_tags_column"
```

### Apply migrations
```bash
uv run alembic upgrade head    # apply all pending migrations
```

### Roll back one migration
```bash
uv run alembic downgrade -1
```

## Workflow for adding a new column

1. Edit the SQLModel class in `src/samplemind/core/models/sample.py` or `user.py`
2. Generate the migration:
   ```bash
   uv run alembic revision --autogenerate -m "add_<column>_to_<table>"
   ```
3. Review the generated file in `migrations/versions/` — check `upgrade()` and `downgrade()`
4. Apply:
   ```bash
   uv run alembic upgrade head
   ```
5. Verify:
   ```bash
   uv run alembic current     # should show the new revision as HEAD
   uv run alembic check       # should print nothing (no drift)
   ```

## Common autogenerate issues to check

| Issue | Fix |
|-------|-----|
| NOT NULL column without `server_default` | Add `server_default=""` or make nullable |
| Wrong SQLite column type | Check SQLAlchemy type mapping for SQLite |
| Missing import at top of migration file | Add `from sqlalchemy import ...` |

## DB file location

The database path is set by `get_settings().database_url` using platformdirs:
- **macOS**: `~/Library/Application Support/SampleMind/samplemind.db`
- **Windows**: `%LOCALAPPDATA%\SampleMind\samplemind.db`
- **Linux**: `~/.local/share/SampleMind/samplemind.db`

Check the active path:
```bash
uv run python -c "from samplemind.core.config import get_settings; print(get_settings().database_url)"
```

## Expected tables

| Table | Created by |
|-------|------------|
| `samples` | Alembic initial migration |
| `users` | Alembic migration `0001_...` |
| `alembic_version` | Alembic itself (revision tracking) |

## Inspect the schema

```bash
uv run python -c "
from samplemind.data.orm import get_engine
from sqlalchemy import inspect
insp = inspect(get_engine())
for t in insp.get_table_names():
    print(f'\nTable: {t}')
    for col in insp.get_columns(t):
        print(f'  {col[\"name\"]:30} {col[\"type\"]}')
"
```

## Phase check

If `alembic.ini` or `migrations/env.py` are missing, Alembic is not yet
configured. See `docs/en/phase-03-database.md` for setup instructions.

## Related skills

- `run-tests` — tests use in-memory SQLite (`orm_engine` fixture), no migration needed
- `check-ci` — CI runs `alembic check` to catch drift

