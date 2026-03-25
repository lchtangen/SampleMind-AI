# Prompt: Code Review Checklist

Use this prompt when reviewing a PR or asking Auggie to review code changes.

---

## How to invoke

Ask Auggie: `"Review the changes in <file> / this PR"`
Or: `"Does this follow SampleMind coding standards?"`

---

## Prompt template (for Auggie)

```
Please review the following changes for SampleMind-AI coding standards:

<paste diff or describe changes>

Check for:

## Python
- [ ] Type hints on all new public functions/methods
- [ ] src-layout imports (from samplemind.x import y) — no sys.path.insert
- [ ] ruff-compatible style (will pass: uv run ruff check src/ tests/)
- [ ] Line length ≤ 100 chars
- [ ] No print() debug statements — use structlog
- [ ] No real audio files committed

## IPC Contract
- [ ] JSON output → stdout only
- [ ] Human-readable output → stderr only
- [ ] New CLI commands support --json flag
- [ ] No mixed stdout/stderr in JSON mode (breaks Tauri IPC)

## Audio / Classifier
- [ ] energy values are exactly "low", "mid", or "high" (never "medium")
- [ ] mood values are in: dark, chill, aggressive, euphoric, melancholic, neutral
- [ ] instrument values are in: loop, hihat, kick, snare, bass, pad, lead, sfx, unknown
- [ ] New audio features use canonical pattern (not librosa.feature.rms() directly)

## Database
- [ ] Schema changes have an Alembic migration
- [ ] Tests use in-memory SQLite (create_engine("sqlite://"))
- [ ] SampleRepository used — no raw SQL strings outside repositories/

## Rust / Tauri
- [ ] Async commands use owned types (String not &str)
- [ ] New commands registered in invoke_handler AND capabilities JSON
- [ ] cargo clippy passes with -D warnings

## Tests
- [ ] New functionality has a test
- [ ] WAV fixtures use soundfile + numpy (no real audio)
- [ ] Expensive tests marked @pytest.mark.slow
- [ ] macOS-only tests marked @pytest.mark.macos

## Dependencies
- [ ] New Python deps added with: uv add <pkg>
- [ ] New Node deps added with: pnpm add <pkg> (in app/)
- [ ] New Rust deps added with: cargo add <crate>
- [ ] No manual edits to pyproject.toml deps section, package.json, Cargo.toml

## Never (instant reject)
- [ ] pip install in docs or scripts
- [ ] black / flake8 / pylint / isort suggested
- [ ] npm in app/ directory
- [ ] sys.path.insert in new code
- [ ] .env file committed
- [ ] Real audio file committed
- [ ] SAMPLEMIND_SECRET_KEY hardcoded

Flag any violations and suggest the exact fix.
```

---

## CI gates that must pass

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run pytest tests/ -m "not slow" --tb=short
uv run pytest tests/ --cov=samplemind --cov-fail-under=60
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
```

