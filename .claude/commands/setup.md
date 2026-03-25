# /setup — Run Dev Environment Setup

Run `scripts/setup-dev.sh` with guided output. Handles first-time setup or repair of a broken environment.

## Arguments

$ARGUMENTS
Optional:
  --check-only     Verify tools are installed without installing anything
  --python-only    Only run the Python/uv setup steps
  --node           Also set up Node.js + pnpm + Tauri toolchain
  --full           Full setup including optional Rust/Node tools

Examples:
  /setup
  /setup --check-only
  /setup --full

---

Parse flags from $ARGUMENTS.

**Step 1 — WSL2 safety check:**

```bash
pwd
```

If the path contains `/mnt/c/`, stop immediately and show:
```
❌ STOP: Your project is on an NTFS filesystem (/mnt/c/).
This is 5-10× slower than WSL2's native ext4 filesystem.

Move your project:
  cp -r /mnt/c/path/to/SampleMind-AI ~/dev/projects/
  cd ~/dev/projects/SampleMind-AI

Then re-run /setup from the new location.
```

**Step 2 — If --check-only:**

Verify each tool without installing:
```bash
uv --version && echo "✓ uv"
python3 --version && echo "✓ python3"
node --version 2>/dev/null && echo "✓ node" || echo "⚠ node (optional)"
pnpm --version 2>/dev/null && echo "✓ pnpm" || echo "⚠ pnpm (optional)"
cargo --version 2>/dev/null && echo "✓ cargo" || echo "⚠ cargo (optional)"
```

Show summary and exit.

**Step 3 — Run setup script:**

```bash
bash scripts/setup-dev.sh
```

The script performs these steps automatically:
1. Platform detection (WSL2 / macOS / Linux)
2. Install uv (if missing)
3. `uv sync --extra dev` — Python 3.13 + all dev dependencies
4. Verify core imports: samplemind, librosa, soundfile, typer, fastapi, flask
5. `uv run ruff check src/` — lint check
6. `uv run pytest tests/ -x --tb=short -q` — test run
7. `git config core.fsmonitor=true` + `core.untrackedcache=true` (WSL2 performance)
8. `uv run pre-commit install` — hook setup
9. Check node, pnpm, cargo (optional Tauri toolchain)

**Step 4 — Post-setup validation:**

After the script completes:
```bash
uv run samplemind --help
uv run samplemind list --json
```

If validation fails, show the specific import error and suggest:
```bash
uv sync --extra dev     # re-sync deps
uv run python -c "import samplemind"   # verify package install
```

**Step 5 — Show next steps:**

```
✅ Dev environment ready!

Quick start:
  uv run samplemind serve          → Flask at http://localhost:5000
  uv run samplemind api --reload   → FastAPI at http://localhost:8000/api/docs
  uv run pytest tests/ -v          → Run tests
  /serve                           → Start services via Claude
  /check                           → Run full CI suite

Optional (Tauri desktop):
  cd app && pnpm install && pnpm tauri dev

Import samples:
  uv run samplemind import ~/Music/Samples/ --workers 4 --json
```

Note: If `scripts/setup-dev.sh` is not found, it likely needs to be created. Show the manual setup steps:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --extra dev
git config core.fsmonitor true
uv run pre-commit install
```

