# Memory: Development Environment (2026)

Critical environment facts for SampleMind-AI development.

---

## Primary Development Machine

**OS:** Windows 11 with WSL2 (Ubuntu 22.04 LTS)
**IDE:** VS Code with Augment Code extension (primary AI tool)
**Shell:** bash in WSL2 terminal

```
# Project root — ALWAYS work here (Linux ext4 = fast):
/home/ubuntu/dev/projects/SampleMind-AI/

# NEVER put code here (NTFS = 5-10x slower):
/mnt/c/...
```

Open VS Code from WSL terminal: `code .`

---

## Python Environment

| Tool | Command | Notes |
|------|---------|-------|
| Package manager | `uv` | NEVER use pip, poetry, or conda |
| Python version | 3.13 | enforced in pyproject.toml |
| Virtual env | auto by `uv` | in `.venv/` |
| Run commands | `uv run <cmd>` | preferred over activating venv |
| Install deps | `uv sync` | reads pyproject.toml |
| Add dep | `uv add <pkg>` | updates pyproject.toml automatically |
| Lint | `uv run ruff check src/` | NEVER flake8/pylint/black/isort |
| Format | `uv run ruff format src/` | |
| Tests | `uv run pytest tests/ -v` | |
| Tests (fast) | `uv run pytest tests/ -m "not slow"` | skips audio ML tests |
| Tests (parallel) | `uv run pytest tests/ -n auto` | pytest-xdist |
| Coverage | `uv run pytest --cov=samplemind --cov-report=term-missing` | min 60% |

---

## Node / Tauri Environment

| Tool | Command | Notes |
|------|---------|-------|
| Package manager | `pnpm` | NEVER use npm in app/ |
| Install | `cd app && pnpm install` | |
| Dev mode | `pnpm tauri dev` | wraps Flask at :5174 |
| Build | `pnpm tauri build` | |
| Universal Binary | `pnpm tauri build --target universal-apple-darwin` | macOS only |

---

## Rust Environment

```bash
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
cargo test --manifest-path app/src-tauri/Cargo.toml
```

**Rule:** `cargo clippy -- -D warnings` MUST pass. Fix all warnings.
**Async commands:** use owned `String`, not `&str` — cannot cross await boundary.

---

## JUCE Plugin (macOS only)

```bash
cd plugin && cmake -B build && cmake --build build
auval -v aufx SmPl SmAI
```

macOS prerequisite: `xcode-select --install`

---

## Service Ports

| Service | Port | Command |
|---------|------|---------|
| Flask web UI | 5000 | `uv run samplemind serve` |
| FastAPI REST | 8000 | `uv run samplemind api` |
| Tauri dev | 5174 | `pnpm tauri dev` |
| Sidecar socket | `/tmp/samplemind.sock` | `uv run python src/samplemind/sidecar/server.py` |

---

## Production Target (macOS)

```bash
# Prerequisites:
xcode-select --install
brew install uv pnpm rustup

# Build:
cd app && pnpm tauri build --target universal-apple-darwin
```

Output: `.app` + `.dmg` Universal Binary (arm64 + x86_64)

---

## AI Tool Config Paths

| Tool | Config Location | What It Reads |
|------|----------------|---------------|
| **Augment Code** | `.augment/` | `rules.md`, `memories/*.md`, `skills/*/SKILL.md` |
| **Claude Code** | `.claude/` + `CLAUDE.md` | agents, commands, settings |
| **GitHub Copilot** | `.github/` | `copilot-instructions.md`, `agents/*.md` |
| **Universal** | `AGENTS.md` (root) | All tools can reference this |

**`.auggie/`** = project automation YAML reference (NOT read by Augment Code extension)

---

## Git Configuration (WSL2 speed)

```bash
git config core.fsmonitor true    # faster status on WSL2
git config core.autocrlf false    # avoid CRLF issues
```

---

## Environment Variables

```bash
# Sentry (optional)
SAMPLEMIND_SENTRY_DSN=https://...

# LLM providers (Phase 12)
SAMPLEMIND_ANTHROPIC_API_KEY=sk-ant-...
SAMPLEMIND_OPENAI_API_KEY=sk-...

# Cloud sync (Phase 13)
SAMPLEMIND_SYNC_ENABLED=true
SAMPLEMIND_SYNC_BUCKET=samplemind-user-xxx
SAMPLEMIND_SYNC_ACCESS_KEY=...
SAMPLEMIND_SYNC_SECRET_KEY=...
SAMPLEMIND_SYNC_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com
SAMPLEMIND_SUPABASE_URL=https://<project>.supabase.co
SAMPLEMIND_SUPABASE_KEY=...

# Stripe marketplace (Phase 15)
SAMPLEMIND_STRIPE_SECRET_KEY=sk_...

# AI generation (Phase 16)
PYTORCH_ENABLE_MPS_FALLBACK=1     # Apple Silicon MPS acceleration
HF_HOME=~/.cache/huggingface      # model cache
```

