# /db-migrate — Create Database Migration

Generate a new Alembic migration for a SQLModel schema change.

## Arguments

$ARGUMENTS
Required: migration description (short, snake_case)
Examples:
  /db-migrate add_tags_column
  /db-migrate add_genre_to_samples
  /db-migrate create_initial_schema

---

Create a new Alembic database migration. Migration description: $ARGUMENTS

**Step 1 — Check Phase 3 is implemented:**
Look for `alembic/` directory and `alembic.ini` at repo root.
If missing: explain that Alembic migrations are Phase 3 work, reference
`docs/en/phase-03-database.md`, and offer to scaffold the Alembic setup first.

**Step 2 — Check current migration state:**
```bash
uv run alembic current    # show current DB revision
uv run alembic history    # show migration history
```

**Step 3 — Generate the migration:**
```bash
uv run alembic revision --autogenerate -m "<description from $ARGUMENTS>"
```

This compares the current `Sample` SQLModel class (in `src/samplemind/models.py`)
against the live database schema and generates a migration file.

**Step 4 — Review the generated file:**
Read the new migration file in `alembic/versions/`.
Show the `upgrade()` and `downgrade()` functions.
Check for common Alembic autogenerate issues:
- Missing `server_default` for NOT NULL columns
- Incorrect column type mapping (SQLite limitations)
- Missing imports at the top of the migration file

**Step 5 — Apply or discard:**
Ask the user: apply the migration now?
If yes:
```bash
uv run alembic upgrade head
```
If no: show the file path so they can review and edit it first.

**Step 6 — Verify:**
```bash
uv run alembic current    # should show the new revision as HEAD
```
