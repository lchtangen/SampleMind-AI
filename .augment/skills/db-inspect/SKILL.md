# Skill: db-inspect

Inspect the SampleMind SQLite database: schema, record counts, migration state,
and PRAGMA settings.

## When to use

Use this skill when the user asks to:
- Check the current Alembic migration revision
- View the database schema (tables + columns)
- Count samples or users in the database
- Verify SQLite PRAGMA settings (WAL, cache size, etc.)
- Find the path to the database file

## Commands

### DB file path

```bash
uv run python -c "from samplemind.core.config import get_settings; print(get_settings().database_url)"
```

### Migration state

```bash
uv run alembic current    # active revision
uv run alembic history    # all revisions
uv run alembic check      # verify no schema drift (used by CI)
```

### Schema (tables + columns)

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

### Record counts

```bash
uv run python -c "
from samplemind.data.orm import get_engine
from sqlalchemy import text
with get_engine().connect() as c:
    print('samples:', c.execute(text('SELECT COUNT(*) FROM samples')).scalar())
    print('users:  ', c.execute(text('SELECT COUNT(*) FROM users')).scalar())
"
```

### PRAGMA check

```bash
uv run python -c "
from samplemind.data.orm import get_engine
with get_engine().connect() as conn:
    for pragma in ['journal_mode','cache_size','synchronous','temp_store','mmap_size']:
        r = conn.execute(__import__('sqlalchemy').text(f'PRAGMA {pragma}')).fetchone()
        print(f'{pragma:20}: {r[0]}')
"
```

## Expected tables

| Table | Description |
|-------|-------------|
| `samples` | Audio sample library |
| `users` | Auth accounts (Alembic migration 0001) |
| `alembic_version` | Migration tracking |

## Expected PRAGMA values

| PRAGMA | Expected value | Purpose |
|--------|---------------|---------|
| `journal_mode` | WAL | Concurrent reads during writes |
| `cache_size` | -64000 | 64 MB page cache |
| `synchronous` | NORMAL | Safe + fast |
| `temp_store` | MEMORY | In-RAM temp tables |
| `mmap_size` | 268435456 | 256 MB memory-mapped I/O |

## DB paths by OS

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/SampleMind/samplemind.db` |
| Windows | `%LOCALAPPDATA%\SampleMind\samplemind.db` |
| Linux | `~/.local/share/SampleMind/samplemind.db` |

## Key source files

- `src/samplemind/data/orm.py` — engine, session, PRAGMAs
- `migrations/env.py` — Alembic env
- `alembic.ini` — Alembic configuration

## Related skills

- `db-migrate` — generate and apply schema migrations
- `health-check` — verify DB connectivity

