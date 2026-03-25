# /check — Full CI Suite

Run the complete local CI check: ruff lint + format check, pytest (with coverage), pre-commit dry-run, and Rust clippy.
Equivalent to what the GitHub Actions `ci.yml` runs.

## Arguments

$ARGUMENTS
(optional flags: `--fix` to auto-fix ruff issues; `--fast` to skip Rust clippy; `--coverage` to show coverage report; `--pre-commit` to run pre-commit dry-run)

## What This Does

1. **ruff lint** — checks all Python files in `src/` and `tests/` for style and logic errors
2. **ruff format check** — verifies formatting without modifying files
3. **pytest** — runs the full test suite with verbose output and parallel workers
4. **coverage check** — reports coverage per module, fails if below 70%
5. **cargo clippy** — runs Rust linter on `app/src-tauri/` treating warnings as errors
6. **pre-commit dry-run** — verifies hooks would pass (if `--pre-commit` flag passed)

If `--fix` is passed, ruff will automatically fix auto-fixable lint issues and format files.
If `--fast` is passed, skip the Rust clippy step (faster if you haven't changed Rust code).
If `--coverage` is passed, show per-file coverage in the terminal output.

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
Run `uv run pytest tests/ -v --tb=short -n auto` if `tests/` directory exists.
If pytest-xdist not installed, fall back to `uv run pytest tests/ -v --tb=short`.
If it doesn't exist, note that tests haven't been set up yet (Phase 2).
Show a summary of passed/failed/skipped.

**Step 4 — Coverage check:**
Run `uv run pytest tests/ --cov=samplemind --cov-report=term-missing --cov-fail-under=70 -q`.
If `--coverage` flag passed, show full per-file breakdown.
Report whether coverage threshold (70%) was met.
If coverage is below threshold, identify which modules need more tests.

**Step 5 — Rust clippy (unless --fast):**
Run `cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings`.
Report any warnings or errors.

**Step 6 — pre-commit dry-run (if --pre-commit flag):**
Run `uv run pre-commit run --all-files` if `.pre-commit-config.yaml` exists.
Report any hook failures.

**Final summary:** Print a ✓/✗ status for each step and an overall PASS/FAIL result.
If any step fails, suggest the specific fix:
- ruff failure → "run /check --fix to auto-fix ruff issues"
- test failure → "run uv run pytest tests/ -v --tb=long for full traceback"
- coverage failure → "add tests for the modules shown in red"
- clippy failure → "fix Rust warnings listed above"
