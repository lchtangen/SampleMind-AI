# Contributing to SampleMind AI

Welcome, and thank you for considering contributing to SampleMind AI — a local-first,
AI-powered audio sample library manager and DAW companion for FL Studio producers.

This guide will help you get started, stay productive, and collaborate efficiently.

---

## Project Vision

SampleMind AI is a smart sample organizer and analyzer for music producers. It uses
signal processing and AI to:

- Analyze BPM, key, instrument, mood, and energy from every WAV file using librosa
- Organize a library of samples in SQLite (SQLModel + Alembic, WAL mode)
- Auto-tag samples with genre, mood, and custom tags via CLI and web UI
- Search the library by any combination of filters — instrument, BPM range, key, energy
- Authenticate users via JWT + RBAC (viewer / owner / admin roles)
- Export sample packs and integrate with FL Studio filesystem

Quality > quantity. We're building for the future of sound.

---

## Development Setup

### Prerequisites

- **Python 3.13** (managed automatically by `uv`)
- **uv** — Rust-based Python package manager (https://docs.astral.sh/uv/getting-started/installation/)
- **Node.js 20+ and pnpm** — only needed for the Tauri desktop app in `app/`
- **Rust + cargo** — only needed for the Tauri desktop app in `app/`
- **VS Code** with the Python and Pylance extensions

### Install

```bash
# Clone the repository
git clone https://github.com/lchtangen/SampleMind-AI.git
cd SampleMind-AI

# Install all Python dependencies into .venv (uv creates it automatically)
uv sync --dev

# Run the database migrations to create the SQLite tables (users + samples)
uv run alembic upgrade head

# Confirm the CLI works
uv run samplemind --help
```

### Daily Workflow

```bash
# Run all tests (33 tests, all should pass)
uv run pytest tests/ -v

# Run only fast tests — skip the @pytest.mark.slow librosa tests
uv run pytest tests/ -v -m "not slow"

# Run a single test function by node ID
uv run pytest tests/test_audio_analysis.py::test_bpm -v

# Run tests in parallel across all CPU cores
uv run pytest tests/ -n auto

# Lint — ruff replaces flake8, isort, and black; do not install those separately
uv run ruff check src/ tests/

# Auto-fix safe lint issues in place
uv run ruff check src/ tests/ --fix

# Format all Python files
uv run ruff format src/ tests/

# Type-check — pyright is faster than mypy and has first-class Pydantic v2 support
uv run pyright src/

# Verify that Alembic migrations are in sync with the SQLModel metadata
uv run alembic check
```

### Running the App Locally

```bash
# Import a folder of WAV samples and analyze them
uv run samplemind import ~/Music/Samples/

# List all imported samples
uv run samplemind list

# Search by filter combination
uv run samplemind search --query "dark" --energy high --instrument kick

# Tag a sample manually
uv run samplemind tag "kick_128" --genre trap --tags "808,heavy"

# Start the Flask web UI (available at http://localhost:5000)
uv run samplemind serve

# Start the FastAPI server (auth routes — available at http://localhost:8000/docs)
uv run samplemind api
```

### Desktop App (Tauri — optional)

```bash
# Install Node dependencies (one-time)
cd app && pnpm install

# Dev mode — spawns Flask on port 5174 and opens the WebView
pnpm tauri dev

# Production build (macOS — requires Xcode command line tools)
pnpm tauri build --target universal-apple-darwin
```

---

## Code Standards

- **Package manager:** `uv` only. Never use `pip install` or `python -m venv` directly.
- **Linter / formatter:** `ruff` only. Never suggest `black`, `flake8`, `isort`, or `pylint`.
- **Type hints:** Required on all public functions and methods. Run `uv run pyright src/` to verify.
- **Imports:** Use src-layout absolute imports (`from samplemind.analyzer.audio_analysis import analyze_file`). No `sys.path.insert` hacks.
- **stdout / stderr split (critical):** JSON output for machine consumption goes to `stdout` only. Human-readable progress and errors go to `stderr`. Mixing them breaks the Tauri IPC contract silently.
- **Database changes:** Every schema change requires an Alembic migration. Never alter the `samples` or `users` table without a corresponding file in `migrations/versions/`.
- **Audio tests:** Never commit real WAV or AIFF files. Generate synthetic fixtures in `tests/conftest.py` using `numpy` + `soundfile`.
- **Dependencies:** `uv add <package>` to add a runtime dep. `uv add --dev <package>` for dev-only deps. Never edit `pyproject.toml` by hand for dependency changes.

---

## Test Conventions

Shared fixtures live in `tests/conftest.py`. Use them — do not create new `sqlite3` or `flask` setup code:

```python
# Database fixtures — use these for all repository and API tests
# orm_engine    — SQLModel in-memory engine (StaticPool) with users + samples tables
# test_user     — a seeded User row created via UserRepository
# access_token  — valid JWT bearer token string for the test_user

# Synthetic WAV fixtures — safe to use in any test; never commit real audio
# silent_wav    — path to a 1s silence WAV at 22050 Hz mono
# kick_wav      — path to a 0.5s 60 Hz sine wave (high amplitude, low frequency)
# hihat_wav     — path to a 0.1s seeded white noise burst (reproducible)

# Example: new integration test using the in-memory database fixture
def test_upsert_and_retrieve(orm_engine):
    # Monkey-patch the global engine so get_session() uses the in-memory DB
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    from samplemind.core.models.sample import SampleCreate
    from samplemind.data.repositories.sample_repository import SampleRepository

    data = SampleCreate(filename="kick.wav", path="/tmp/kick.wav", bpm=128.0)
    sample = SampleRepository.upsert(data)

    assert sample.id is not None      # auto-assigned by SQLite
    assert sample.bpm == 128.0        # stored as float
    assert SampleRepository.count() == 1
```

**Test markers** — apply these to slow or platform-specific tests:

```python
@pytest.mark.slow    # any test that takes > 1s (real librosa analysis)
@pytest.mark.macos   # requires macOS (AppleScript, AU plugin validation)
@pytest.mark.juce    # requires JUCE plugin built (Phase 9+)
```

---

## Pull Request Process

1. Fork the repo and create a feature branch from `main`
2. Run `uv sync --dev` to install all dependencies
3. Make your changes, following the code standards above
4. Run the full quality gate before opening a PR:

   ```bash
   uv run ruff check src/ tests/ && \
   uv run pyright src/ && \
   uv run pytest tests/ -v && \
   uv run alembic check
   ```

5. Open a pull request — CI runs ruff, pyright, pytest, and alembic check automatically

---

## License

MIT License — see [LICENSE](LICENSE) for details.
