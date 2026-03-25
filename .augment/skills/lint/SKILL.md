# Skill: lint

Run ruff lint + format check on all Python source and cargo clippy on Rust.
Use this for code style enforcement before committing or pushing.

## When to use

Use this skill when the user asks to:
- Check Python code style (ruff lint)
- Check Python formatting (ruff format)
- Auto-fix lint/format issues
- Run Rust clippy warnings check
- Fix import order, unused imports, or line length errors

## Commands

### Check only (no changes)

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

### Auto-fix everything

```bash
uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/
```

### Rust clippy (must pass with -D warnings)

```bash
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
```

### Check a single file

```bash
uv run ruff check src/samplemind/analyzer/classifier.py
uv run ruff format --check src/samplemind/analyzer/classifier.py
```

## Rules

- **Use `ruff` only** — never `black`, `flake8`, `pylint`, or `isort`
- `cargo clippy` must pass with `-D warnings` — no suppressions without a comment
- Line length: 100 chars (`ruff` enforces via `pyproject.toml`)
- Target: Python 3.13 (`target-version = "py313"` in pyproject.toml)

## Common ruff error codes

| Code | Meaning | Fix |
|------|---------|-----|
| `F401` | Unused import | Remove or `# noqa: F401` if needed |
| `E501` | Line too long (>100) | Break the line |
| `I001` | Import order | `ruff check --fix` |
| `UP006` | Use `list` instead of `List` | `ruff check --fix` |
| `ANN001` | Missing type annotation | Add type hint |

## pyproject.toml ruff config

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "ANN"]
ignore = ["ANN101", "ANN102"]
```

## Related skills

- `check-ci` — full CI suite (lint + tests + clippy together)
- `run-tests` — run tests after fixing lint errors

