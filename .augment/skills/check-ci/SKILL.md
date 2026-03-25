# Skill: check-ci

Run the full local CI suite — ruff lint + format check, pytest with coverage,
and cargo clippy. Mirrors what `.github/workflows/ci.yml` runs. Use before
every commit or PR.

## When to use

Use this skill when the user asks to:
- Run CI locally before pushing
- Check everything is clean (lint + tests + Rust)
- Auto-fix ruff lint/format issues
- Verify coverage thresholds are met

## Steps (run in order)

### Step 1 — Python lint
```bash
uv run ruff check src/ tests/
```
Auto-fix mode: `uv run ruff check --fix src/ tests/`

### Step 2 — Python format check
```bash
uv run ruff format --check src/ tests/
```
Auto-fix mode: `uv run ruff format src/ tests/`

### Step 3 — Python tests
```bash
uv run pytest tests/ -v --tb=short -n auto
```
Fallback (no pytest-xdist): `uv run pytest tests/ -v --tb=short`

### Step 4 — Coverage check (must pass ≥ 60%)
```bash
uv run pytest tests/ --cov=samplemind --cov-report=term-missing --cov-fail-under=60 -q
```

### Step 5 — Rust clippy (skip with `--fast` if Rust unchanged)
```bash
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
```

## Flags

| Flag        | Effect |
|-------------|--------|
| `--fix`     | Auto-fix ruff lint issues and reformat files (steps 1–2) |
| `--fast`    | Skip cargo clippy (faster when no Rust changes) |
| `--coverage`| Show per-file coverage breakdown in terminal output |

## One-liner (full CI locally)

```bash
uv run ruff check src/ tests/ && \
uv run ruff format --check src/ tests/ && \
uv run pytest tests/ --cov=samplemind --cov-fail-under=60 -q -n auto && \
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
```

## Failure → fix mapping

| Failure | Fix |
|---------|-----|
| ruff lint error | `uv run ruff check --fix src/ tests/` |
| ruff format error | `uv run ruff format src/ tests/` |
| test failure | `uv run pytest tests/ -v --tb=long` for full traceback |
| coverage below 60% | Add tests for modules shown in red |
| clippy warning | Fix the Rust warning — never suppress without a comment |

## Coverage targets

| Module | Target |
|--------|--------|
| Overall | ≥ 60% (CI-enforced) |
| `samplemind.analyzer` | ≥ 80% |
| `samplemind.analyzer.classifier` | ≥ 90% |
| `samplemind.cli` | ≥ 70% |

## Related skills

- `run-tests` — run tests only (without lint or clippy)
- `analyze-audio` — understand classifier thresholds

