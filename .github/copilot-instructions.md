# GitHub Copilot — SampleMind-AI Complete Project Instructions

SampleMind-AI is an AI-powered audio sample library manager for music producers using FL Studio.
Stack: Python backend (librosa + FastAPI + Flask + Typer), Tauri 2 desktop (Rust + Svelte 5),
JUCE 8 VST3/AU plugin, SQLite database. All surfaces share the same DB.

Primary production target: macOS 12+ Universal Binary (arm64 + x86_64)
Development environment: Windows WSL2 Ubuntu 24.04 (Linux ext4 — NOT /mnt/c/)
Documentation: docs/en/phase-01-foundation.md through docs/en/phase-16-ai-sample-generation.md
Architecture: ARCHITECTURE.md | Agent routing: AGENTS.md (root)

**AI Tool Config:**
- Augment Code (VS Code): `.augment/rules.md`, `.augment/memories/`, `.augment/skills/*/SKILL.md`
- Claude Code: `CLAUDE.md` (root), `.claude/agents/*.md`, `.claude/commands/*.md`
- GitHub Copilot: `.github/copilot-instructions.md` (this file), `.github/agents/*.md`

---

## Migration State (March 2026)

Both legacy and new code paths coexist — respect both:

| Component | Legacy path | New path |
|-----------|-------------|----------|
| CLI entrypoint | `src/main.py` (argparse) | `src/samplemind/cli/app.py` (Typer) |
| Audio analysis | `src/analyzer/` | `src/samplemind/analyzer/` |
| Database | `src/data/database.py` (sqlite3) | `src/samplemind/data/` (SQLModel) |
| Web UI | `src/web/app.py` (Flask) | `src/samplemind/web/app.py` (Flask) |
| REST API | — | `src/samplemind/api/main.py` (FastAPI) |

**Critical:** `src/main.py` must remain functional — Tauri dev mode spawns it directly.
Never break this entrypoint without updating `app/src-tauri/src/main.rs` in the same change.

---

## Core Engineering Rules

1. **Read the actual source file** before proposing changes — never guess structure.
2. **Respect migration state** — keep compatibility unless a hard cutover is explicitly requested.
3. **Prefer minimal, safe edits** over broad refactors.
4. **Preserve Tauri/Python IPC contracts** — JSON to stdout, text to stderr, always.
5. **Prefer updating existing files** over introducing new architecture layers.
6. **Type hints** required on all new public Python functions/methods.
7. **Never suggest** `pip install`, `black`, `flake8`, `pylint`, `isort`, `npm` in `app/`.

---

## Services Map

| Service | Port | Start command | Health check |
|---------|------|---------------|--------------|
| Flask web UI | 5000 (5174 Tauri dev) | `uv run samplemind serve` | `GET /api/status` |
| FastAPI REST | 8000 | `uv run samplemind api --reload` | `GET /api/v1/health` |
| Tauri Vite HMR | 1420 | auto (pnpm tauri dev) | — |
| Sidecar socket | /tmp/samplemind.sock | `uv run python src/samplemind/sidecar/server.py &` | ping via nc |

### FastAPI Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/health` | GET | none | `{"status":"ok","version":"x.y.z"}` |
| `/api/v1/auth/register` | POST | none | Create account → UserPublic |
| `/api/v1/auth/login` | POST | none | OAuth2PasswordRequestForm → TokenResponse |
| `/api/v1/auth/refresh` | POST | none | `{refresh_token}` → new access_token |
| `/api/v1/auth/me` | GET | Bearer | Current user profile |
| `/api/v1/auth/me` | PUT | Bearer | Update username |
| `/api/v1/auth/change-password` | POST | Bearer | Change password |
| `/api/docs` | GET | none | OpenAPI interactive UI |

### Flask Routes

| Route | Auth | Description |
|-------|------|-------------|
| `/` | session | Library view |
| `/login`, `/register`, `/logout` | none/session | Auth pages |
| `/api/samples` | session | JSON sample list (HTMX live search) |
| `/api/tag` | session | Update tags |
| `/api/import` | session | Trigger folder import |
| `/api/status` | none | Health + stats |
| `/audio/<id>` | session | Stream WAV for browser playback |

---

## Python Standards

**Package manager:** `uv` only — never `pip install` or `python -m venv`.
**Lint/format:** `ruff` only — never `black`, `flake8`, `pylint`, `isort`.
**Node:** `pnpm` only in `app/` — never `npm` or `yarn`.

```bash
# All Python work:
uv sync                            # install deps
uv run samplemind --help           # CLI
uv run pytest tests/ -v --tb=short
uv run pytest tests/ -n auto       # parallel (pytest-xdist)
uv run pytest --cov=samplemind --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run ruff check --fix src/       # auto-fix

# Generate a secure secret key:
python -c "import secrets; print(secrets.token_hex(32))"
```

**Imports** — use src-layout for all new code:
```python
from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.core.config import get_settings
from samplemind.core.auth import get_current_active_user
from samplemind.data.repositories.sample_repository import SampleRepository
```

Never use `sys.path.insert` in new code.

---

## Auth System (JWT + RBAC)

### JWT Configuration
- Algorithm: **HS256** (python-jose)
- Access token expires: **30 minutes**
- Refresh token expires: **7 days**
- Secret: `SAMPLEMIND_SECRET_KEY` env var — **default is insecure, always override in production**

### RBAC Roles & Permissions

| Role | Permissions |
|------|-------------|
| `viewer` | audio:read, search:basic |
| `member` | + audio:write/delete/analyze/batch, search:advanced, pack:*, api:key_create |
| `owner` | member + api:key_revoke (default for new accounts) |
| `admin` | all permissions |

### Auth Flow
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@example.com","username":"user","password":"SecurePass1"}'

# Login → get tokens
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d 'username=user&password=SecurePass1'
# Returns: {"access_token":"<jwt>","refresh_token":"<token>","token_type":"bearer","expires_in":1800}

# Use token
curl -H 'Authorization: Bearer <access_token>' http://localhost:8000/api/v1/auth/me

# Refresh
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' -d '{"refresh_token":"<token>"}'
```

### Password Rules
Minimum 8 characters, 1 uppercase, 1 lowercase, 1 digit.

### Protect a FastAPI Endpoint
```python
from samplemind.core.auth import get_current_active_user
from samplemind.core.auth.rbac import Permission, RBACService, UserRole
from samplemind.core.models.user import User

@router.get("/protected")
async def protected(current_user: User = Depends(get_current_active_user)):
    RBACService.require_permission(UserRole(current_user.role), Permission.AUDIO_READ)
    # ...
```

---

## IPC Contract (stdout/stderr split)

**This is critical — breaking it silently breaks Tauri and sidecar integrations.**

- **JSON output** → `stdout` only (machine-readable)
- **Human text** → `stderr` only (or Rich console that writes to stderr)
- All new CLI commands **must** support `--json` flag
- Never mix print() debug output with JSON stdout

```python
# CORRECT:
import sys, json
print(json.dumps(result), file=sys.stdout)          # JSON to stdout
print(f"Processed {n} files", file=sys.stderr)     # text to stderr

# WRONG — breaks Tauri IPC:
print(f"Processing {path}...")   # this pollutes JSON stdout
print(json.dumps(result))
```

```rust
// Rust: spawn CLI and parse stdout only
let output = Command::new("samplemind")
    .args(["list", "--json"])
    .output().map_err(|e| e.to_string())?;
let result: serde_json::Value = serde_json::from_slice(&output.stdout)?;
```

**Current CLI commands:**
```bash
uv run samplemind import <folder> [--workers N] [--json]
uv run samplemind analyze <folder|file> [--json]
uv run samplemind list [--key KEY] [--bpm-min N] [--json]
uv run samplemind search [query] [--instrument X] [--energy X] [--json]
uv run samplemind tag <name> [--genre X] [--mood X] [--energy X] [--tags X]
uv run samplemind serve [--port N]
uv run samplemind api [--host X] [--port N] [--reload]
uv run samplemind version
```

---

## Audio Analysis — Canonical Patterns (librosa 0.11)

```python
# src/samplemind/analyzer/audio_analysis.py — canonical pattern:
y, sr = librosa.load(path)                              # default sr=22050, soxr_hq resampling
rms = float(np.sqrt(np.mean(y ** 2)))                   # ← NEVER librosa.feature.rms()
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_norm = float(centroid.mean()) / (sr / 2)       # normalized 0–1
zcr = float(librosa.feature.zero_crossing_rate(y).mean())
flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
rolloff_norm = float(rolloff.mean()) / (sr / 2)

# Fingerprinting — SHA-256 of first 64 KB:
def fingerprint_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()

# Batch import — parallel workers:
from concurrent.futures import ProcessPoolExecutor
def analyze_batch(paths: list[Path], workers: int = 0) -> list[dict]:
    workers = workers or os.cpu_count()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(analyze_file, paths))
```

**Classifier output values — EXACT strings stored in DB — never deviate:**

| Field | Valid values | ⚠ Never use |
|-------|-------------|-------------|
| `energy` | `"low"` `"mid"` `"high"` | `"medium"` |
| `mood` | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` | — |
| `instrument` | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` | — |

**Classifier thresholds (src/samplemind/analyzer/classifier.py):**
- Energy: `rms<0.015→low`, `rms<0.06→mid`, else `high`
- Instrument (priority order): loop→hihat→kick→snare→bass→pad→lead→sfx→unknown
- Mood (priority order): aggressive→dark→melancholic→chill→euphoric→neutral

---

## Database Rules

**Current runtime:** sqlite3 in `src/samplemind/data/database.py` and SQLModel ORM in `src/samplemind/data/orm.py`.
**Default path:** `~/.samplemind/library.db` (dev) | `~/Library/Application Support/SampleMind/samplemind.db` (macOS prod)
**Phase 3 target:** Full SQLModel + Alembic migration path.

```sql
-- Apply on every connection open:
PRAGMA journal_mode=WAL;        -- concurrent reads during writes
PRAGMA cache_size = -64000;     -- 64 MB page cache
PRAGMA synchronous = NORMAL;    -- safe + fast
PRAGMA temp_store = MEMORY;     -- in-RAM temp tables
PRAGMA mmap_size = 268435456;   -- 256 MB memory-mapped I/O
```

**Alembic commands:**
```bash
uv run alembic current                              # show active revision
uv run alembic history --verbose                    # full history
uv run alembic revision --autogenerate -m "desc"    # generate migration
uv run alembic upgrade head                         # apply all migrations
uv run alembic downgrade -1                         # roll back one
```

**Test DB:** always use in-memory SQLite — never a file path in tests:
```python
engine = create_engine("sqlite://")   # in-memory, no file
SQLModel.metadata.create_all(engine)
```

**Expected tables:** `samples`, `users`, `alembic_version`

---

## Web and Desktop Rules

**Flask:**
- Keep API responses stable — additive changes only, no breaking response shape changes
- Use `flask-cors`: `CORS(app, origins=["tauri://localhost", "http://localhost:5174"])`
- Session auth (Flask) and JWT auth (FastAPI) coexist — different ports, different mechanisms
- Audio streaming: use `send_file(path, mimetype="audio/wav", conditional=True)` for range requests
- HTMX endpoints: check `HX-Request` header and return partial HTML or JSON accordingly

**Tauri/Rust:**
```rust
// ✅ CORRECT — owned types, can cross await boundary:
#[tauri::command]
pub async fn import_folder(path: String) -> Result<String, String> { ... }

// ❌ WRONG — &str cannot cross await boundary:
pub async fn import_folder(path: &str) -> Result<String, String> { ... }
```
- Return `Result<T, String>` and map errors with `.map_err(|e| e.to_string())`
- Register new commands in BOTH `invoke_handler!()` AND capabilities JSON
- `cargo clippy -- -D warnings` must be clean — fix all warnings

**Svelte 5 frontend:**
```svelte
<!-- Use Runes (not legacy stores): -->
let query = $state('');
let results = $derived.by(() => filter(samples, query));
$effect(() => { fetchResults(query); });
```

**Package managers:**
- `app/`: always `pnpm` — never `npm` or `yarn`
- Python: always `uv` — never `pip`
- Rust: `cargo add` for new deps — never edit Cargo.toml manually

---

## Testing and Quality

```bash
uv run pytest tests/ -v --tb=short          # all tests
uv run pytest tests/ -m "not slow"          # fast only
uv run pytest tests/ -n auto                # parallel (pytest-xdist)
uv run pytest --cov=samplemind --cov-report=term-missing --cov-fail-under=60
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
cargo test --manifest-path app/src-tauri/Cargo.toml
```

**Coverage targets:** overall ≥60% | analyzer ≥80% | classifier ≥90% | CLI ≥70%

**Test markers:**
```python
@pytest.mark.slow    # >1 second (audio analysis) — skipped in fast CI
@pytest.mark.macos   # requires macOS (AppleScript, AU validation)
@pytest.mark.juce    # requires JUCE plugin built
```

**WAV fixtures — always synthetic, never real audio files:**
```python
# tests/conftest.py
@pytest.fixture
def kick_wav(tmp_path: Path) -> Path:
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)
    path = tmp_path / "kick.wav"
    sf.write(str(path), samples, 22050)
    return path

@pytest.fixture
def hihat_wav(tmp_path: Path) -> Path:
    samples = np.random.uniform(-0.3, 0.3, 2205).astype(np.float32)  # 0.1s white noise
    path = tmp_path / "hihat.wav"
    sf.write(str(path), samples, 22050)
    return path
```

**CI matrix (.github/workflows/python-lint.yml):**
- Python 3.13 ubuntu-latest: ruff + pytest + coverage
- Python 3.13 windows-latest: fast tests only (not slow, not macos)
- Python 3.13 macos-14: fast tests (not slow)
- Rust ubuntu-latest: clippy + cargo test

---

## Tooling, Environment & VSCode

**WSL2:** Always work on ext4 (`/home/ubuntu/`) — never `/mnt/c/` (5-10× slower).
```bash
git config core.fsmonitor true       # speed up git on WSL2
git config core.untrackedcache true
code .                               # open VSCode from WSL terminal
```

**VSCode integration:**
- Python interpreter: `${workspaceFolder}/.venv/bin/python` (set via `Python: Select Interpreter`)
- Format on save: ruff (auto-configured in `.vscode/settings.json`)
- Debug configs (F5): `.vscode/launch.json` — Flask, FastAPI, pytest all, pytest file
- Run tasks (Ctrl+Shift+B): `.vscode/tasks.json` — CI check, lint, tests, serve
- Recommended extensions: `.vscode/extensions.json`
  - `charliermarsh.ruff` (lint+format), `ms-python.python`, `rust-lang.rust-analyzer`
  - `svelte.svelte-vscode`, `tauri-apps.tauri-vscode`

**Terminal shortcuts** (add to `~/.bashrc`):
```bash
alias pt="uv run pytest tests/ -v --tb=short"
alias ptf="uv run pytest tests/ -m 'not slow'"
alias rl="uv run ruff check src/ tests/"
alias rfix="uv run ruff check --fix src/ && uv run ruff format src/"
alias cc="cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings"
alias smserve="uv run samplemind serve"
alias smapi="uv run samplemind api --reload"
```

**File paths:** use `platformdirs` for config/data — never hardcode `~` or home directory.

---

## Agent Routing Reference (24 agents)

| Task involves... | Agent |
|-----------------|-------|
| librosa, BPM, key, classifier, WAV, fingerprinting | `audio-analyzer` |
| pytest, tests, coverage, CI, fixtures, conftest | `test-runner` |
| Tauri, Rust, Svelte, app/, IPC, pnpm build | `tauri-builder` |
| docs/, README, phase docs, ARCHITECTURE | `doc-writer` |
| FL Studio, JUCE, VST3, AU, AppleScript, sidecar | `fl-studio-agent` |
| FastAPI, REST, OpenAPI, /api/v1/, JWT endpoints | `api-agent` |
| Flask, web/app.py, Jinja2, HTMX, audio streaming | `web-agent` |
| JWT, bcrypt, RBAC, UserRole, Permission, OAuth2 | `security-agent` |
| scripts/, WSL2, CI/CD, setup-dev.sh, GitHub Actions | `devops-agent` |
| ML models, transformers, quantization, embeddings | `ml-agent` |
| Phase 2 (audio testing, WAV fixtures) | `phase-02-audio-testing` |
| Phase 3 (SQLModel, Alembic) | `phase-03-database` |
| Phase 4 (Typer CLI, Rich, --json) | `phase-04-cli` |
| Phase 5 (Flask API, HTMX, SSE) | `web-agent` |
| Phase 6 (Tauri desktop, Svelte 5) | `phase-06-desktop` |
| Phase 7 (FL Studio automation) | `fl-studio-agent` |
| Phase 8 (JUCE plugin, CMake, auval) | `phase-08-vst-plugin` |
| Phase 9 (sample packs, .smpack) | `phase-09-sample-packs` |
| Phase 10 (production, signing, notarization) | `phase-10-production` |

---

## Never Suggest

1. `pip install` — use `uv add <pkg>` or `uv sync`
2. `python -m venv` — uv manages the venv
3. `black`, `flake8`, `pylint`, `isort` — use `ruff` only
4. `npm` in `app/` — use `pnpm`
5. `sys.path.insert` hacks in new code
6. Committing real audio files (WAV, AIFF, MP3, FLAC)
7. Breaking `src/main.py` without updating `app/src-tauri/src/main.rs`
8. Hardcoded home directory paths — use `platformdirs`
9. Raw TCP sockets for sidecar IPC — use Unix domain socket (`/tmp/samplemind.sock`)
10. `git push --force` or destructive DB operations without explicit confirmation
11. Committing `.env` files or API keys
12. Hardcoding `SAMPLEMIND_SECRET_KEY` — always use env var
13. `print()` for debug in committed code — use `structlog`
14. Suppressing `cargo clippy` warnings without a comment explaining why

---

## FL Studio Context

Integration mechanisms (macOS-first, Windows secondary):
1. **Filesystem export** — copy WAVs to FL Studio Samples folder
2. **Clipboard paths** — `pbcopy` (macOS), `clip.exe` (Windows)
3. **AppleScript** — focus FL Studio, open sample browser (F8)
4. **Windows COM** — `win32com.client` automation
5. **Virtual MIDI** — IAC Driver (macOS), CC messages for BPM/key metadata
6. **JUCE VST3/AU plugin** — live sample browser inside FL Studio

```
# macOS paths:
~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/
~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/
~/Library/Audio/Plug-Ins/Components/SampleMind.component
~/Library/Audio/Plug-Ins/VST3/SampleMind.vst3

# Windows paths:
C:\Users\<name>\Documents\Image-Line\FL Studio 21\Data\Patches\Samples\SampleMind\
```

**Required macOS entitlements** (Tauri app + JUCE plugin):
- `com.apple.security.automation.apple-events`
- `com.apple.security.cs.allow-unsigned-executable-memory` (Python sidecar)
- `com.apple.security.files.user-selected.read-write`
- `com.apple.security.assets.music.read-write`

---

## Security Rules

1. No network access required — SampleMind is fully local
2. Never store credentials or API keys in the database or config files
3. `SAMPLEMIND_SECRET_KEY` must always be set from env — default is insecure
4. Sidecar binary: verify SHA-256 at startup before execution
5. Code signing: Apple Developer ID (macOS), Azure Trusted Signing (Windows)
6. No telemetry without explicit opt-in (`SAMPLEMIND_SENTRY_DSN` env var)
7. Audio files never copied without explicit user action
8. Python logging always to stderr — never stdout (IPC contract)
9. Never log user file paths at INFO+ level (privacy)
10. `.env` files must never be committed — reference `.env.example` only

---

## Required Environment Variables

```bash
# Core (required in production):
SAMPLEMIND_SECRET_KEY=<32+ random chars>    # JWT signing — CHANGE THIS
FLASK_SECRET_KEY=<32+ random chars>         # Flask session encryption
ANTHROPIC_API_KEY=sk-ant-...               # Auggie CLI + AI features

# Generate secrets:
python -c "import secrets; print(secrets.token_hex(32))"

# Optional:
SAMPLEMIND_DB_PATH=~/.samplemind/library.db
SAMPLEMIND_LOG_LEVEL=info                   # debug|info|warning|error
SAMPLEMIND_WORKERS=0                        # 0 = auto (cpu_count)
SAMPLEMIND_SENTRY_DSN=                      # opt-in error tracking

# OAuth providers (optional):
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# macOS production signing:
APPLE_SIGNING_IDENTITY=
APPLE_TEAM_ID=
APPLE_ID=
APPLE_PASSWORD=                             # app-specific password
```

---

## Common Commands Reference

```bash
# Setup:
bash scripts/setup-dev.sh              # first-time full setup

# Services:
uv run samplemind serve                # Flask at localhost:5000
uv run samplemind api --reload         # FastAPI at localhost:8000/api/docs
bash scripts/start.sh both             # Flask + Tauri dev

# CLI:
uv run samplemind import ~/Music/ --workers 4 --json
uv run samplemind list --instrument kick --energy high --json
uv run samplemind search --mood dark --json
uv run samplemind tag kick_808 --genre trap --energy high

# Tests:
uv run pytest tests/ -v --tb=short
uv run pytest tests/ -m "not slow" -n auto
uv run pytest --cov=samplemind --cov-report=term-missing

# Lint:
uv run ruff check src/ tests/
uv run ruff check --fix src/ && uv run ruff format src/
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings

# DB:
uv run alembic current
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head

# Desktop:
cd app && pnpm tauri dev
cd app && pnpm tauri build --target universal-apple-darwin
```

---

## Phase 11–16 Quick Reference

### Phase 11 — Semantic Search
```bash
uv run samplemind semantic "dark trap kick" --top 20
uv run samplemind semantic --audio ref.wav --top 10 --json
uv run samplemind index rebuild --workers 4
```
- CLAP 2023 model: 512-dim embeddings, L2-normalized
- FAISS IndexFlatIP: cosine similarity search < 5ms for 100k samples
- Feature flag: `semantic_search` (enable via `~/.samplemind/flags.json`)
- Key files: `src/samplemind/search/embeddings.py`, `vector_index.py`

### Phase 12 — AI Curation
```bash
uv run samplemind curate analyze               # no LLM needed
uv run samplemind curate "create dark set"     # dry-run (default)
uv run samplemind curate "organize" --execute  # apply actions
```
- Providers: `anthropic/claude-sonnet-4-5`, `openai/gpt-4o`, `ollama/llama3.2`
- Feature flag: `ai_curation`
- All LLM calls mocked in tests — no API keys in CI
- Key files: `src/samplemind/agent/curator.py`, `library_analyzer.py`

### Phase 13 — Cloud Sync
```bash
uv run samplemind sync push       # upload metadata + new files to R2
uv run samplemind sync pull       # merge from other devices
uv run samplemind sync status     # show config
```
- File storage: Cloudflare R2 (S3-compatible), SHA-256 deduplication
- Metadata: Supabase PostgreSQL, last-write-wins conflicts
- Feature flag: `cloud_sync`
- Key files: `src/samplemind/sync/file_sync.py`, `metadata_sync.py`

### Phase 14 — Analytics Dashboard
```bash
uv run samplemind analytics               # terminal summary
uv run samplemind analytics --json        # all chart data
# Flask: http://localhost:5000/analytics  # interactive Plotly dashboard
```
- Charts: BPM histogram, key heatmap (12×2), growth timeline, instrument×energy
- All aggregations: pure SQL, < 20ms for 500k samples
- Dark theme: `plot_bgcolor: "#1e1e2e"`
- Key files: `src/samplemind/analytics/engine.py`, `charts.py`

### Phase 15 — Marketplace
```bash
uv run samplemind marketplace search "dark trap"
uv run samplemind marketplace install dark-trap-vol-1
uv run samplemind marketplace publish my-pack.smpack --price 9.99
```
- Payments: Stripe Connect (80% creator / 20% platform)
- Validation: energy must be `low`/`mid`/`high` — never `medium`
- Downloads: signed R2 URLs (24h expiry)
- Feature flag: `pack_marketplace`

### Phase 16 — AI Sample Generation
```bash
uv run samplemind generate "dark trap kick" --bpm 140 --import
uv run samplemind generate "ambient pad A minor" --model stable-audio
uv run samplemind generate "test" --model mock --json   # no downloads
```
- Models: `audiocraft/musicgen-small/medium/large`, `stable-audio`, `mock` (tests)
- BPM loops: `duration = 4 × 4 × (60/BPM)` seconds
- Quality flags: `bpm_match`, `key_match`, `instrument_match`, `clipping`
- Apple Silicon: `PYTORCH_ENABLE_MPS_FALLBACK=1` for ~5x speedup
- Key files: `src/samplemind/generation/pipeline.py`, `backends/`

---

## Agent Routing Table

For feature-specific changes, use the appropriate `.github/agents/*.md` file:

| If task involves… | Use agent |
|-------------------|-----------|
| pyproject.toml, uv, structlog, pydantic-settings | `phase-01-foundation.md` |
| librosa, classifiers, WAV fixtures, LUFS, stereo | `phase-02-audio-testing.md` |
| SQLModel, Alembic, FTS5, DB backup | `phase-03-database.md` |
| Typer, Rich, CLI commands, watch mode, export | `phase-04-cli.md` |
| Flask, FastAPI, HTMX, Socket.IO, WaveSurfer | `web-agent.md` |
| Tauri, Rust, Svelte 5 Runes, system tray | `phase-06-desktop.md` |
| FL Studio, AppleScript, MIDI clock, IAC Driver | `fl-studio-agent.md` |
| JUCE, VST3, AU, sidecar socket, preset manager | `phase-08-vst-plugin.md` |
| .smpack format, pack registry, licensing | `phase-09-sample-packs.md` |
| CI/CD, signing, feature flags, crash reporter | `phase-10-production.md` |
| CLAP, FAISS, vector index, cosine similarity | `phase-11-semantic-search.md` |
| LiteLLM, library curation, smart playlists | `phase-12-ai-curation.md` |
| Cloudflare R2, Supabase, multi-device sync | `phase-13-cloud-sync.md` |
| Plotly, analytics, BPM histogram, key heatmap | `phase-14-analytics.md` |
| Stripe, marketplace, pack publishing | `phase-15-marketplace.md` |
| AudioCraft, Stable Audio, text-to-audio | `phase-16-ai-generation.md` |
| audio analysis, fingerprinting, batch import | `audio-analyzer.md` |
| Tauri, Rust, Svelte, app/, build, CI | `tauri-builder.md` |
| docs/en/, docs/no/, ARCHITECTURE.md | `doc-writer.md` |
| pytest, cargo test, CI, coverage, conftest | `test-runner.md` |
