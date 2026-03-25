# Augment Code Agents — Index

> Agent files for the Augment Code VS Code extension.
> Each `.md` file in this directory defines a specialized agent with triggers, key files, and rules.
> The root `AGENTS.md` is the canonical routing reference for all AI tools.

---

## Domain Agents (10)

| File | Agent | Activate for |
|------|-------|-------------|
| `audio-analyzer.md` | Audio Analyzer | librosa, BPM, key, classifier, WAV, fingerprint |
| `test-runner.md` | Test Runner | pytest, coverage, CI, conftest, fixtures, "tests failing" |
| `tauri-builder.md` | Tauri Builder | Rust, Tauri, Svelte 5, `app/`, cargo, pnpm tauri |
| `api-agent.md` | API Agent | FastAPI, REST, endpoints, JWT, OpenAPI, `api/` |
| `web-agent.md` | Web Agent | Flask, HTMX, SSE, session auth, templates, web UI |
| `security-agent.md` | Security Agent | JWT, RBAC, bcrypt, passlib, `core/auth/`, permissions |
| `devops-agent.md` | DevOps Agent | CI/CD, GitHub Actions, WSL2, scripts, setup |
| `ml-agent.md` | ML Agent | transformers, HuggingFace, FAISS, embeddings, numba |
| `doc-writer.md` | Doc Writer | docs/, README, ARCHITECTURE, phase docs, Norwegian |
| `fl-studio-agent.md` | FL Studio Agent | FL Studio, JUCE, VST3, AU, AppleScript, MIDI, sidecar |

---

## Phase Agents (16)

| File | Phase | Key Technologies |
|------|-------|-----------------|
| `phase-01-foundation.md` | 1 — Foundation | uv, structlog, pydantic-settings, health check |
| `phase-02-audio-testing.md` | 2 — Audio Analysis | librosa, WAV fixtures, pytest, soundfile |
| `phase-03-database.md` | 3 — Database | SQLModel, Alembic, FTS5, repositories |
| `phase-04-cli.md` | 4 — CLI | Typer, Rich, `--json` flag, stdout/stderr contract |
| `phase-05-web.md` | 5 — Web UI | Flask, HTMX, SSE, Flask-Login |
| `phase-06-desktop.md` | 6 — Desktop | Tauri 2, Svelte 5 Runes, system tray |
| `phase-07-fl-studio.md` | 7 — FL Studio | AppleScript, MIDI clock, IAC Driver, filesystem export |
| `phase-08-vst-plugin.md` | 8 — VST Plugin | JUCE 8, VST3/AU, sidecar IPC, MIDI output |
| `phase-09-sample-packs.md` | 9 — Sample Packs | .smpack format, manifest.json, pack registry |
| `phase-10-production.md` | 10 — Production | CI/CD, signing, notarization, feature flags |
| `phase-11-semantic-search.md` | 11 — Semantic Search | CLAP, FAISS, ChromaDB, cosine similarity |
| `phase-12-ai-curation.md` | 12 — AI Curation | LiteLLM, Claude/Ollama, smart playlists, gap analysis |
| `phase-13-cloud-sync.md` | 13 — Cloud Sync | Cloudflare R2, Supabase, multi-device, boto3 |
| `phase-14-analytics.md` | 14 — Analytics | Plotly, BPM histogram, key heatmap, growth |
| `phase-15-marketplace.md` | 15 — Marketplace | Stripe Connect, pack publishing, CDN, signed URLs |
| `phase-16-ai-generation.md` | 16 — AI Generation | AudioCraft, Stable Audio, text-to-audio, mock backend |

---

## Routing Priority

1. **Phase number mentioned** → use that phase agent
2. **Open file path match** → use agent that owns that file pattern
3. **Code pattern match** → use agent that owns that symbol
4. **Keyword match** → use most specific domain agent

> See root `AGENTS.md` for the full cross-tool routing table (Augment + Claude + Copilot).

