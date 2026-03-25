# /check — Full CI Suite

Run the complete local CI check: ruff lint + format check, pytest, and Rust clippy.
Equivalent to what the GitHub Actions `ci.yml` runs.

## Arguments

$ARGUMENTS
(optional: `--fix` to auto-fix ruff issues; `--fast` to skip Rust clippy)

## What This Does

1. **ruff lint** — checks all Python files in `src/` and `tests/` for style and logic errors
2. **ruff format check** — verifies formatting without modifying files
3. **pytest** — runs the full test suite with verbose output
4. **cargo clippy** — runs Rust linter on `app/src-tauri/` treating warnings as errors

If `--fix` is passed, ruff will automatically fix auto-fixable lint issues and format files.
If `--fast` is passed, skip the Rust clippy step (faster if you haven't changed Rust code).

---

Run the full CI suite for this SampleMind-AI project. Check the arguments in $ARGUMENTS for any flags.

**Step 1 — Python lint (ruff):**
Run `uv run ruff check src/ tests/` if tests/ exists, otherwise `uv run ruff check src/`.
If `--fix` was passed, run with `--fix` flag.
Report any lint errors clearly.

**Step 2 — Python format check (ruff format):**
Run `uv run ruff format --check src/` (add `tests/` if it exists).
If `--fix` was passed, run `uv run ruff format src/` instead (no --check).
Report any formatting issues.

**Step 3 — Python tests (pytest):**
Run `uv run pytest tests/ -v --tb=short` if `tests/` directory exists.
If it doesn't exist, note that tests haven't been set up yet (Phase 2) and suggest running `uv run pytest --co` to see what's discovered.
Show a summary of passed/failed/skipped.

**Step 4 — Rust clippy (unless --fast):**
Run `cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings`.
Report any warnings or errors.

**Final summary:** Print a ✓/✗ status for each step and an overall PASS/FAIL result.
If any step fails, suggest the specific fix (e.g., "run /check --fix to auto-fix ruff issues").
