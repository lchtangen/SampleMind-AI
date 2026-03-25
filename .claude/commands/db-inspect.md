# /db-inspect — Inspect the SampleMind Database

Show database schema, record counts, PRAGMA settings, Alembic migration state, and run ad-hoc queries.

## Arguments

$ARGUMENTS
Optional:
  schema       Show all tables and column definitions
  stats        Show record counts per table
  pragma       Show active SQLite PRAGMA settings vs. targets
  alembic      Show Alembic migration history and current revision
  all          Run all checks (default)
  --query "SQL" Run a custom SQL query (read-only)

Examples:
  /db-inspect
  /db-inspect schema
  /db-inspect pragma
  /db-inspect --query "SELECT instrument, COUNT(*) FROM samples GROUP BY instrument"

---

Parse the mode and optional --query from $ARGUMENTS (default: all).

**Step 1 — Database path (always show):**

```bash
uv run python -c "
from samplemind.core.config import get_settings
print('DB path:', get_settings().database_url)
"
```

**Step 2 — Schema (if mode is "schema" or "all"):**

```python
uv run python -c "
from samplemind.data.orm import get_engine
from sqlalchemy import inspect as sa_inspect
insp = sa_inspect(get_engine())
for table in insp.get_table_names():
    print(f'\nTable: {table}')
    for col in insp.get_columns(table):
        nullable = 'NULL' if col.get('nullable', True) else 'NOT NULL'
        default = f\" DEFAULT {col['default']}\" if col.get('default') else ''
        print(f\"  {col['name']:30} {str(col['type']):20} {nullable}{default}\")
"
```

Expected tables: `samples`, `users`, `alembic_version`

**Step 3 — Stats (if mode is "stats" or "all"):**

```python
uv run python -c "
from samplemind.data.orm import get_engine
from sqlalchemy import text
with get_engine().connect() as c:
    print('samples:        ', c.execute(text('SELECT COUNT(*) FROM samples')).scalar())
    print('users:          ', c.execute(text('SELECT COUNT(*) FROM users')).scalar())
    print('with BPM:       ', c.execute(text('SELECT COUNT(*) FROM samples WHERE bpm IS NOT NULL')).scalar())
    print('with key:       ', c.execute(text('SELECT COUNT(*) FROM samples WHERE key IS NOT NULL')).scalar())
    print()
    for row in c.execute(text('SELECT instrument, COUNT(*) as n FROM samples GROUP BY instrument ORDER BY n DESC')):
        print(f'  {row[0] or \"unknown\":12} {row[1]}')
"
```

**Step 4 — PRAGMA check (if mode is "pragma" or "all"):**

```python
uv run python -c "
from samplemind.data.orm import get_engine
from sqlalchemy import text
targets = {
    'journal_mode': 'WAL',
    'cache_size': '-64000',
    'synchronous': 'NORMAL',
    'temp_store': 'MEMORY',
    'mmap_size': '268435456',
}
with get_engine().connect() as c:
    print(f'{'PRAGMA':<20} {'CURRENT':<15} {'TARGET':<15} STATUS')
    for pragma, target in targets.items():
        val = str(c.execute(text(f'PRAGMA {pragma}')).fetchone()[0])
        status = '✓' if val.upper() == target.upper() else '⚠'
        print(f'{pragma:<20} {val:<15} {target:<15} {status}')
"
```

**Step 5 — Alembic state (if mode is "alembic" or "all"):**

```bash
uv run alembic current
uv run alembic history --verbose | head -20
```

If Alembic not configured: show "Alembic not yet set up — Phase 3 work. See docs/en/phase-03-database.md"

**Step 6 — Custom query (if --query flag):**

```python
uv run python -c "
from samplemind.data.orm import get_engine
from sqlalchemy import text
with get_engine().connect() as c:
    for row in c.execute(text('<QUERY>')):
        print(row)
"
```

Only allow SELECT queries. Refuse any DDL/DML for safety.

