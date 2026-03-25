# .auggie/ — Augment Auggie CLI Configuration (v2)

Native configuration for Augment Auggie CLI, fully tailored for **SampleMind-AI**.
Dev environment: Windows WSL2. Production target: macOS 12+ Universal Binary.

---

## Directory Structure

```
.auggie/
├── settings.yaml          # Core settings: models, paths, services, auth, IPC, agents index
├── agents.yaml            # 20 agents (phase-02–10 + 11 domain agents) with routing
├── rules.md               # 10-section coding rules: IPC, audio, DB, Rust, tests
├── README.md              # This file
│
├── skills/ (22 skills)
│   ├── analyze_audio.yaml   Audio feature extraction (BPM, key, mood, energy, instrument)
│   ├── batch_import.yaml    Batch import WAV/AIFF with parallel workers
│   ├── build.yaml           Tauri dev/release/universal + sidecar + JUCE plugin
│   ├── check.yaml           Full CI suite (ruff + pytest + coverage + clippy)
│   ├── coverage.yaml        Per-module coverage with targets (analyzer 80%, etc.)
│   ├── db_inspect.yaml      DB schema, stats, PRAGMA check, migration state
│   ├── db_migrate.yaml      Alembic migration generate + apply
│   ├── fingerprint.yaml     SHA-256 audio deduplication
│   ├── health_check.yaml    FastAPI, Flask, sidecar, DB connectivity check
│   ├── import_samples.yaml  Import folder into library with dedup
│   ├── lint.yaml            ruff check + format + cargo clippy
│   ├── list_samples.yaml    List library with key/BPM/energy/mood/genre filters
│   ├── pack.yaml            .smpack sample pack create/import/verify/list
│   ├── run_tests.yaml       pytest + cargo test
│   ├── search.yaml          Search library with text + metadata filters
│   ├── serve_api.yaml       FastAPI server (port 8000, OpenAPI docs, JWT auth)
│   ├── serve_web.yaml       Flask web UI (port 5000, session auth, audio stream)
│   ├── setup_dev.yaml       Run scripts/setup-dev.sh (full env setup)
│   ├── sidecar.yaml         Unix socket sidecar server for JUCE IPC
│   ├── start.yaml           Quick-start services: web/desktop/both/api
│   ├── auth.yaml            User register/login/JWT/RBAC management
│   └── tag.yaml             Manual tagging: genre, mood, energy, custom tags
│
├── environments/
│   ├── dev.yaml             WSL2 dev: paths, tool checks, git config, notes
│   └── prod.yaml            macOS: Universal Binary, signing, FL Studio paths
│
├── workflows/
│   ├── ci-check.yaml        Full CI pipeline — run before every commit
│   ├── new-feature.yaml     Guided feature implementation checklist
│   ├── release.yaml         macOS Universal Binary release pipeline
│   ├── dev-start.yaml       Start all services in order with health checks
│   ├── debug-classifier.yaml Walk through classifier decision tree for a file
│   ├── add-audio-feature.yaml Full stack guide for adding a new audio feature
│   └── onboard-dev.yaml     First-time developer setup from zero
│
├── environments/            See above
├── hooks/
│   └── pre-commit.yaml      Pre-commit: lint, format, fast tests, safety blocks
│
├── tools/
│   ├── vscode.yaml          VSCode task→skill map, shortcuts, extensions guide
│   ├── terminal.yaml        Shell aliases, one-liners, WSL2 tips
│   └── debug.yaml           Debug configs (maps to .vscode/launch.json)
│
└── prompts/
    ├── debug-audio.md       Template: debug wrong audio classification
    ├── code-review.md       Template: PR/code review checklist
    └── api-design.md        Template: design FastAPI endpoints / Flask routes
```

---

## Quick Start

```bash
# 1. Set your Anthropic API key:
export ANTHROPIC_API_KEY=sk-ant-...

# 2. Verify Auggie loads config:
auggie info
auggie agents

# 3. Run a skill:
auggie skill analyze_audio path=samples/kick.wav
auggie skill check
auggie skill import_samples folder=~/Music/Samples/ workers=4

# 4. Run a workflow:
auggie workflow ci-check
auggie workflow new-feature
```

---

## Agent Routing (20 agents)

Routing priority: **1. phase number** → **2. most specific domain agent**

| Task involves… | Agent | Model |
|----------------|-------|-------|
| librosa, BPM, key, classifier, WAV, fingerprinting | `audio-analyzer` | sonnet |
| pytest, tests, coverage, CI, fixtures, conftest | `test-runner` | sonnet |
| Tauri, Rust, Svelte, app/, IPC, pnpm build | `tauri-builder` | sonnet |
| docs/, README, phase docs, ARCHITECTURE | `doc-writer` | haiku |
| FL Studio, JUCE, VST3, AU, AppleScript, sidecar | `fl-studio-agent` | sonnet |
| FastAPI, REST, OpenAPI, /api/docs, JWT endpoints | `api-agent` | sonnet |
| Flask, web/app.py, Jinja2, /api/samples, HTMX | `web-agent` | sonnet |
| JWT, bcrypt, RBAC, UserRole, permissions, OAuth2 | `security-agent` | sonnet |
| setup-dev.sh, scripts/, WSL2, CI/CD, GitHub Actions | `devops-agent` | sonnet |
| ML models, transformers, quantization, embeddings | `ml-agent` | sonnet |
| Phase 2 (audio testing, WAV fixtures) | `phase-02-audio-testing` | sonnet |
| Phase 3 (SQLModel, Alembic, migrations) | `phase-03-database` | sonnet |
| Phase 4 (Typer CLI, Rich, --json flag) | `phase-04-cli` | sonnet |
| Phase 5 (Flask, HTMX, SSE) | `phase-05-web` | sonnet |
| Phase 6 (Tauri desktop, Svelte 5 Runes) | `phase-06-desktop` | sonnet |
| Phase 7 (FL Studio automation) | `phase-07-fl-studio` | sonnet |
| Phase 8 (JUCE plugin, CMake, auval) | `phase-08-vst-plugin` | sonnet |
| Phase 9 (sample packs, .smpack) | `phase-09-sample-packs` | sonnet |
| Phase 10 (production, signing, notarization) | `phase-10-production` | **opus** |

---

## Key Rules (summary — full rules in rules.md)

- **Type hints** on all public Python functions
- **ruff** for lint/format — never black, flake8, pylint, isort
- **uv** for Python deps — never `pip install`; **pnpm** for Node
- **JSON → stdout, text → stderr** (IPC contract — breaking this breaks Tauri)
- **Classifier values**: energy=`low/mid/high` (never `medium`), mood=6 values, instrument=9 values
- **No real audio files** in repo — generate with soundfile + numpy
- **No sys.path.insert** in new code
- `src/main.py` legacy entrypoint must stay functional (Tauri dev mode)

---

## Common Commands

```bash
# ── Setup ─────────────────────────────────────────────────────────────────────
bash scripts/setup-dev.sh                       # first-time full setup
uv sync                                         # re-sync deps after pulling

# ── CLI ───────────────────────────────────────────────────────────────────────
uv run samplemind --help
uv run samplemind import ~/Music/Samples/ --workers 4 --json
uv run samplemind analyze samples/kick.wav --json
uv run samplemind list --json
uv run samplemind search --instrument kick --energy high --json
uv run samplemind tag kick_808 --genre trap --energy high --tags "808,sub,punchy"

# ── Services ──────────────────────────────────────────────────────────────────
uv run samplemind serve                         # Flask at http://localhost:5000
uv run samplemind api --reload                  # FastAPI at http://localhost:8000/api/docs
bash scripts/start.sh web                       # Flask (scripts/start.sh)
bash scripts/start.sh both                      # Flask + Tauri dev

# ── Auth / API (FastAPI) ──────────────────────────────────────────────────────
curl http://localhost:8000/api/v1/health
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"dev@example.com","username":"dev","password":"SecurePass1"}'

# ── Tests ─────────────────────────────────────────────────────────────────────
uv run pytest tests/ -v --tb=short             # all tests
uv run pytest tests/ -m "not slow"             # fast (skip slow)
uv run pytest tests/ -n auto                   # parallel (pytest-xdist)
uv run pytest --cov=samplemind --cov-report=term-missing  # with coverage

# ── Lint / Format ─────────────────────────────────────────────────────────────
uv run ruff check src/ tests/                  # lint
uv run ruff format src/ tests/                 # format
uv run ruff check --fix src/ && uv run ruff format src/   # auto-fix

# ── Tauri Desktop ─────────────────────────────────────────────────────────────
cd app && pnpm install && pnpm tauri dev        # dev mode (HMR)
pnpm tauri build --target universal-apple-darwin  # macOS production

# ── Rust ─────────────────────────────────────────────────────────────────────
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
cargo test --manifest-path app/src-tauri/Cargo.toml

# ── Database ──────────────────────────────────────────────────────────────────
uv run alembic current
uv run alembic revision --autogenerate -m "add_tags_column"
uv run alembic upgrade head

# ── Debug ─────────────────────────────────────────────────────────────────────
# F5 in VSCode → select debug config from .vscode/launch.json
# Or: auggie workflow debug-classifier path=samples/kick.wav
```

## Workflows

| Command | Purpose |
|---------|---------|
| `auggie workflow ci-check` | Full CI suite before committing |
| `auggie workflow dev-start` | Start all services with health checks |
| `auggie workflow new-feature` | Guided checklist for implementing a feature |
| `auggie workflow debug-classifier path=<wav>` | Why was this sample classified wrong? |
| `auggie workflow add-audio-feature` | Add new librosa feature across full stack |
| `auggie workflow onboard-dev` | First-time developer setup |
| `auggie workflow release` | macOS production release pipeline |

---

## Active Environment

Current: **dev** (WSL2) — set in `settings.yaml → active_environment`.
Switch to `prod` when building for macOS release.

See `environments/dev.yaml` and `environments/prod.yaml` for full details.
