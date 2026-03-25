# Skill: setup-dev

Set up the SampleMind-AI development environment from scratch on a new machine.
Works on macOS, Linux/WSL2, and Windows.

## When to use

Use this skill when the user asks to:
- Set up the project for the first time
- Onboard a new developer
- Fix a broken virtual environment
- Reinstall all dependencies
- Verify the development environment is healthy

## Steps (in order)

### 1. Clone and enter project

```bash
git clone git@github.com:lchtangen/SampleMind-AI.git
cd SampleMind-AI
```

### 2. Install Python dependencies (uv)

```bash
uv sync --dev
```

This creates `.venv/` and installs all deps including dev tools.

### 3. Apply database migrations

```bash
uv run alembic upgrade head
```

Required before the first run — creates the SQLite schema.

### 4. Install Node deps for Tauri frontend

```bash
cd app && pnpm install
```

### 5. Verify everything works

```bash
# Python
uv run samplemind --help
uv run pytest tests/ -m "not slow" -q

# Rust
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
cargo test --manifest-path app/src-tauri/Cargo.toml
```

## Prerequisites by platform

### macOS

```bash
xcode-select --install
brew install uv pnpm rustup
rustup-init && rustup target add aarch64-apple-darwin x86_64-apple-darwin
```

### Windows WSL2 (primary dev environment)

```
# Code must live on Linux ext4 filesystem (fast):
/home/ubuntu/dev/projects/SampleMind-AI/
# Never on NTFS (/mnt/c/) — 5-10× slower for git ops

git config core.fsmonitor true   # speed up git on WSL2
```

### Linux / WSL2

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://get.pnpm.io/install.sh | sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Environment variables

```bash
# Required for JWT auth (set in .env or shell profile):
export SAMPLEMIND_SECRET_KEY="your-secret-key-here"

# Optional: override DB path
export SAMPLEMIND_DB_URL="sqlite:///path/to/custom.db"
```

⚠ **Never commit `.env` files.**

## Verify setup

```bash
uv run samplemind version          # print version
uv run samplemind list --json      # should return [] (empty library)
uv run alembic current             # should show HEAD revision
curl http://localhost:8000/api/v1/health   # after: uv run samplemind api
```

## Related skills

- `check-ci` — run full CI suite after setup
- `serve` — start services after setup
- `import-samples` — load your first samples

