# SampleMind-AI — Augment Code Rules

> **Loaded by the Augment Code VS Code extension on every task.**
> This is the master rules file for the project.
> Agents: `.augment/agents/*.md` · Skills: `.augment/skills/*/SKILL.md` · Guidelines: `.augment-guidelines` (repo root)
> Cross-tool sync: `CLAUDE.md` (Claude Code) · `.github/copilot-instructions.md` (Copilot) · `AGENTS.md` (universal routing)

---

## 0. Project Identity

**SampleMind-AI** — AI-powered audio sample library manager for FL Studio.
Analyzes WAV/AIFF with librosa (BPM, key, instrument, mood, energy), stores in SQLite,
surfaces through CLI, Flask web UI, Tauri desktop app, and JUCE VST3/AU plugin.

Development: Windows WSL2 (`/home/ubuntu/dev/projects/SampleMind-AI/`)
Production target: macOS 12+ Universal Binary

**Current Phase: 11+ (semantic search, AI curation, cloud sync, analytics)**

---

## 1. Code Style

- **Type hints** required on all new public Python functions/methods
- **Lint/format**: `ruff` only — never suggest `black`, `flake8`, `pylint`, `isort`
- **Imports**: `from samplemind.x import y` src-layout style; no `sys.path.insert`
- **Line length**: 100 chars (ruff enforces, `target-version = py313`)
- **Rust**: `cargo clippy -- -D warnings` must pass; no suppressions without a comment

## 2. Audio Analysis — Canonical Patterns

```python
y, sr = librosa.load(path)                              # default sr=22050, soxr_hq
rms = float(np.sqrt(np.mean(y ** 2)))                   # NOT librosa.feature.rms()
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_norm = float(centroid.mean()) / (sr / 2)       # normalized 0–1
zcr = float(librosa.feature.zero_crossing_rate(y).mean())

def fingerprint_file(path: Path) -> str:               # SHA-256 of first 64 KB
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()
```

## 3. Classifier Output Values — Never Deviate

| Field | Valid values | ⚠ Common mistake |
|-------|-------------|-----------------|
| `energy` | `"low"` `"mid"` `"high"` | **Never** `"medium"` |
| `mood` | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` | — |
| `instrument` | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` | — |

## 4. IPC Contract (stdout / stderr split)

- **stdout** → JSON only (machine-readable for Tauri, sidecar, tests)
- **stderr** → human-readable text, Rich progress bars
- All new CLI commands must support `--json` flag that outputs clean JSON to stdout
- **Never** mix human text with JSON on stdout — breaks Tauri IPC silently

## 5. Rust / Tauri Conventions

```rust
// Async commands MUST use owned types:
#[tauri::command]
pub async fn import_folder(path: String) -> Result<String, String> { ... }
// Register in BOTH invoke_handler!() AND capabilities JSON
```

## 6. Database Rules

- **Active runtime**: SQLModel + Alembic (`data/orm.py`, `SampleRepository`, `UserRepository`)
- **Never** use raw sqlite3 or import from `data/database.py` in new code
- Schema changes require an Alembic migration: `uv run alembic revision --autogenerate -m "..."`
- Tests use in-memory SQLite via `orm_engine` fixture (StaticPool — never a file DB in tests)
- WAL + PRAGMAs are applied automatically by `_apply_sqlite_pragmas()` event listener

## 7. Testing Rules

- **Never** commit real audio files — generate with `soundfile` + `numpy` in `conftest.py`
- WAV fixtures use `tmp_path` (pytest) — safe for parallel execution
- Mark slow tests `@pytest.mark.slow`, macOS-only tests `@pytest.mark.macos`
- Coverage minimums: analyzer 80%, classifier 90%, CLI 70%, overall 60% (CI-enforced)
- Use `orm_engine` fixture for DB tests; use `test_user` + `access_token` for auth tests

## 8. Package Management

| Tool | Use for | Never use |
|------|---------|-----------|
| `uv` | All Python deps and execution | `pip install`, `python -m venv` |
| `pnpm` | All Node work in `app/` | `npm`, `yarn` |
| `cargo add` | Rust deps | Manual Cargo.toml edits |

## 9. Workflow Safety Rules

- Read the actual source file before proposing changes
- Prefer minimal, safe edits over broad refactors
- Preserve Tauri/Python IPC contracts at all times
- `src/main.py` (legacy argparse) must stay functional for Tauri dev mode
- Do not push to remote or rebase without explicit user permission

## 10. Never Do

1. Commit real WAV/AIFF/MP3/FLAC files — always use synthetic fixtures
2. Hardcode home directory paths — use `platformdirs`
3. Print JSON to stderr or human text to stdout — breaks IPC silently
4. Use `sys.path.insert` in new code
5. Use `pip`, `npm`, `yarn`, `black`, `flake8`, `pylint`, `isort`
6. Break `src/main.py` without a coordinated Tauri update
7. Suppress `cargo clippy` warnings without a comment
8. Commit `.env` files or credentials
9. Run `git push --force` or `DROP TABLE` without confirmation
10. Add `print()` debug statements to committed code

## 11. Phase Status (2026)

| Phase | Status | Description |
|-------|--------|-------------|
| 1 Foundation | ✅ | uv + pyproject.toml + src layout + structlog + pydantic-settings |
| 2 Audio Analysis | ✅ | librosa, LUFS, stereo, transients, harmonic complexity, 33+ tests |
| 3 Database | ✅ | SQLModel + Alembic + FTS5 + backup + multi-library |
| 4 CLI | ✅ | Typer + Rich + watch mode + export + shell completion |
| 5 Web | ✅ | Flask + HTMX + Socket.IO + WaveSurfer + playlist builder |
| 6 Desktop | 🔧 | Tauri 2 + Svelte 5 + tray + global shortcuts + drag-to-DAW |
| 7 FL Studio | 🔧 | Filesystem + AppleScript + MIDI clock + Windows COM + FL21 API |
| 8 JUCE Plugin | 🔧 | VST3/AU + sidecar IPC + preset manager + MIDI output |
| 9 Sample Packs | 🔧 | .smpack format + registry + versioning + licensing |
| 10 Production | 🔧 | CI/CD + signing + feature flags + update channels + crash reporter |
| 11 Semantic Search | 🚀 | CLAP + FAISS + ChromaDB + text/audio similarity search |
| 12 AI Curation | 🚀 | LiteLLM + Claude/GPT-4o/Ollama + smart playlists + gap analysis |
| 13 Cloud Sync | 🚀 | Cloudflare R2 + Supabase + SHA-256 dedup + multi-device |
| 14 Analytics | 🚀 | Plotly + BPM histogram + key heatmap + growth timeline |
| 15 Marketplace | 🚀 | Stripe Connect + pack publishing + signed CDN URLs |
| 16 AI Generation | 🚀 | AudioCraft MusicGen + Stable Audio Open + BPM-aligned loops |

✅ = complete · 🔧 = in progress · 🚀 = designed, ready to implement

## 12. Key File Locations

| What | Where |
|------|-------|
| Audio analysis | `src/samplemind/analyzer/audio_analysis.py` |
| LUFS loudness | `src/samplemind/analyzer/loudness.py` |
| Stereo field | `src/samplemind/analyzer/stereo.py` |
| Classifiers | `src/samplemind/analyzer/classifier.py` |
| ORM / DB engine | `src/samplemind/data/orm.py` |
| Repositories | `src/samplemind/data/repositories/` |
| FTS5 search | `src/samplemind/data/fts.py` |
| DB backup | `src/samplemind/data/backup.py` |
| Multi-library | `src/samplemind/data/library_manager.py` |
| SQLModel models | `src/samplemind/core/models/` |
| Auth (JWT/RBAC) | `src/samplemind/core/auth/` |
| Feature flags | `src/samplemind/core/feature_flags.py` |
| Logging | `src/samplemind/core/logging.py` |
| Config | `src/samplemind/core/config.py` |
| CLI commands | `src/samplemind/cli/` |
| FastAPI routes | `src/samplemind/api/routes/` |
| Flask web UI | `src/samplemind/web/` |
| Semantic search | `src/samplemind/search/` |
| AI agent | `src/samplemind/agent/` |
| Cloud sync | `src/samplemind/sync/` |
| Analytics | `src/samplemind/analytics/` |
| Marketplace | `src/samplemind/marketplace/` |
| AI generation | `src/samplemind/generation/` |
| Tauri Rust | `app/src-tauri/src/` |
| Svelte frontend | `app/src/` |
| Tests + fixtures | `tests/conftest.py` |
| Migrations | `migrations/versions/` |
| Legacy CLI | `src/main.py` (required by Tauri dev mode) |
| Phase docs | `docs/en/phase-NN-*.md` |

## 13. AI-Tool Directory Map

| Tool | Primary Config | Agents | Skills | Commands |
|------|---------------|--------|--------|----------|
| **Augment Code** (VS Code) | `.augment/rules.md` | `.augment/agents/*.md` | `.augment/skills/*/SKILL.md` | VS Code tasks |
| **Claude Code** | `CLAUDE.md` (root) | `.claude/agents/*.md` | — | `.claude/commands/*.md` |
| **GitHub Copilot** | `.github/copilot-instructions.md` | `.github/agents/*.md` | — | — |
| **All tools (routing)** | `AGENTS.md` (root) | — | — | — |

**Repository Guidelines:** `.augment-guidelines` (repo root) — single canonical file for all repo-level context (replaces `.augment/memories/*.md` and `Augment-Memories.md`).
**Personal Guidelines:** Add via Augment Code `@` menu → User Guidelines (stored per-user, not in repo).
**DO NOT use `.auggie/`** — it is a project automation reference only, not read by any AI extension.

## 14. Semantic Search Embedding Contract (Phase 11)

- All CLAP embeddings: L2-normalized float32, shape (512,)
- Cosine similarity = dot product of unit vectors (range 0.0–1.0)
- Practical "similar" threshold: ≥ 0.75
- Index: `~/.samplemind/vector_index.faiss` + `vector_index_ids.npy`
- Feature flag: `is_enabled("semantic_search")` must gate all search UI

## 15. AI Generation Rules (Phase 16)

- Mock backend ALWAYS available (sine wave, no downloads) — use for all tests
- Real backends (`audiocraft/*`, `stable-audio`): `@pytest.mark.slow` only
- BPM-aligned loops: `duration = 4 bars × 4 beats × (60/BPM)`
- Quality flags: bpm_match (±5 BPM), key_match (exact), clipping (peak > 0.98)
- Auto-import updates BOTH SQLite AND FAISS index
- Generated files: `~/.samplemind/generated/gen_{slug}_{timestamp}.wav`

## 16. Classifier Output Values — Never Deviate

| Field | Valid values | ⚠ Common mistake |
|-------|-------------|-----------------|
| `energy` | `"low"` `"mid"` `"high"` | **Never** `"medium"` |
| `mood` | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` | — |
| `instrument` | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` | — |
| `license` | `"CC0"` `"CC BY 4.0"` `"CC BY-NC 4.0"` `"Royalty-Free"` `"Editorial"` `"Custom"` | — |

