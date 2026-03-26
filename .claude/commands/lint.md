# /lint — Lint and Type-Check

Run the full Python quality pipeline: ruff check (lint), ruff format (style), and pyright
(type checking). Reports all errors with file:line references. Optionally auto-fixes issues.

## Arguments

$ARGUMENTS
Optional:
  --fix        Apply auto-fixable ruff changes (safe transforms only)
  --check      Check format without writing (CI mode — exits non-zero if unformatted)
  --types      Run pyright only (skip ruff)
  --style      Run ruff format only (skip lint and types)
  --src <path> Limit to a specific path (default: src/ tests/)

Examples:
  /lint
  /lint --fix
  /lint --check
  /lint --src src/samplemind/analyzer/

---

Parse flags from $ARGUMENTS. Default target is `src/ tests/`.

**Step 1 — Ruff lint:**

If `--types` flag is set, skip to Step 3.

```bash
uv run ruff check src/ tests/ [--fix if --fix flag set]
```

- On success: `✓ ruff check — 0 issues`
- On failure: show each error with file:line, error code, and message
- Common fixes: `uv run ruff check src/ tests/ --fix` applies E, F, I rules automatically

**Step 2 — Ruff format:**

If `--types` flag is set, skip this step.

```bash
uv run ruff format src/ tests/ [--check if --check flag set]
```

- `--check` mode: exits non-zero if any file would be reformatted (use in CI)
- Normal mode: rewrites files in place and reports count of changed files

**Step 3 — Pyright type check:**

If `--style` flag is set, skip this step.

```bash
uv run pyright src/
```

- Reports: errors (blocking), warnings (advisory), information
- Key config lives in `pyproject.toml` `[tool.pyright]` section
- Common issues to watch: missing return types on public functions, unresolved imports,
  incompatible types in SQLModel field definitions

**Step 4 — Summary:**

```
Lint & Type-Check — SampleMind-AI
══════════════════════════════════════════
✓ ruff check    0 issues   (src/ tests/)
✓ ruff format   3 files reformatted
✓ pyright       0 errors, 2 warnings

All checks passed.
```

If any step fails, show the errors grouped by file and suggest targeted fixes.
For pyright errors on generated/migration files, suggest adding `# type: ignore` with a reason.
