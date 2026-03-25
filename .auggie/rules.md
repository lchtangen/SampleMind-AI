# Auggie CLI — SampleMind-AI Project Rules

> These rules are loaded by Auggie on every task. Follow them unconditionally.

---

## 1. Code Style

- **Type hints** required on all new public Python functions/methods
- **Lint/format**: `ruff` only — never suggest `black`, `flake8`, `pylint`, `isort`
- **Imports**: use `from samplemind.x import y` src-layout style; no `sys.path.insert` hacks
- **Line length**: 100 chars (ruff enforces)
- **Target**: Python 3.13+ syntax (`ruff target-version = py313`)
- **Rust**: `cargo clippy -- -D warnings` must pass; no suppressions without a comment

## 2. Audio Analysis — Exact Patterns

```python
# Canonical load (librosa 0.11, soxr_hq resampler):
y, sr = librosa.load(path)                              # default sr=22050
rms = float(np.sqrt(np.mean(y ** 2)))                   # NOT librosa.feature.rms()
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_norm = float(centroid.mean()) / (sr / 2)       # normalized 0–1
zcr = float(librosa.feature.zero_crossing_rate(y).mean())

# Fingerprinting (first 64 KB SHA-256):
def fingerprint_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()
```

## 3. Classifier Output Values — Never Deviate

| Field | Valid values | ⚠ Common mistake |
|-------|-------------|-----------------|
| `energy` | `"low"` `"mid"` `"high"` | Never use `"medium"` |
| `mood` | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` | — |
| `instrument` | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` | — |

## 4. IPC Contract (stdout / stderr split)

- JSON for machine consumption → **stdout only**
- Human-readable text → **stderr** (or non-JSON display mode)
- All new CLI commands must support `--json` flag that outputs clean JSON to stdout
- Rationale: Rust/Tauri and sidecar flows parse stdout; mixing breaks integration silently

```rust
// Rust — spawn Python and parse stdout:
let output = Command::new("samplemind")
    .args(["import", &path, "--json"])
    .output()
    .map_err(|e| e.to_string())?;
let result: serde_json::Value = serde_json::from_slice(&output.stdout)?;
```

## 5. Rust / Tauri Conventions

```rust
// Async commands MUST use owned types (String, not &str):
#[tauri::command]
pub async fn import_folder(path: String) -> Result<String, String> { ... }

// Register in BOTH invoke_handler AND capabilities JSON
```

- New Tauri commands → add to `invoke_handler!()` + capabilities JSON
- `cargo clippy -- -D warnings` must be clean before any Rust PR

## 6. Database Rules

- **Current runtime**: sqlite3 (`src/samplemind/data/database.py`)
- **Phase 3 target**: SQLModel + Alembic
- Apply these PRAGMAs on connection open:
  ```sql
  PRAGMA journal_mode=WAL;
  PRAGMA cache_size = -64000;
  PRAGMA synchronous = NORMAL;
  PRAGMA temp_store = MEMORY;
  ```
- New schema changes require an Alembic migration file
- Tests use in-memory SQLite: `create_engine("sqlite://")`

## 7. Testing Rules

- Never commit real audio files — always generate with `soundfile` + `numpy`
- WAV fixtures use `tmp_path` (pytest) — safe for parallel execution
- All new audio features require a corresponding pytest fixture + test
- Mark expensive tests with `@pytest.mark.slow`
- Mark macOS-only tests with `@pytest.mark.macos`
- Coverage minimums: analyzer 80%, classifier 90%, CLI 70%, overall 60%

## 8. Package Management

| Tool | Use | Never use |
|------|-----|-----------|
| `uv` | All Python dep/execution work | `pip install`, `python -m venv` |
| `pnpm` | All Node work in `app/` | `npm`, `yarn` |
| `cargo add` | Rust deps | Manual Cargo.toml edits |

## 9. Workflow Rules

- Read the actual source file before proposing changes
- Prefer minimal, safe edits over broad refactors
- Preserve Tauri/Python IPC contracts
- Migration must be incremental and non-breaking
- `src/main.py` (legacy argparse CLI) must remain functional for Tauri dev mode

## 10. Never Do

1. Commit real WAV/AIFF/MP3/FLAC files
2. Hardcode home directory paths — use `platformdirs`
3. Print JSON to stderr or human text to stdout
4. Use `sys.path.insert` in new code
5. Use `pip`, `npm`, `yarn`, `black`, `flake8`, `pylint`, `isort`
6. Break `src/main.py` without a coordinated Tauri update
7. Suppress `cargo clippy` warnings without a comment
8. Commit `.env` files or credentials
9. Run `git push --force` or destructive DB commands without confirmation
10. Add `print()` debug statements to committed code — use `structlog`
