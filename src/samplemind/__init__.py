"""
samplemind — AI-powered audio sample library manager.

Analyzes WAV/AIFF files with librosa (BPM, key, instrument, mood, energy),
stores metadata in SQLite via SQLModel, and surfaces everything through a CLI,
Flask web UI, Tauri desktop app, and JUCE VST3/AU plugin.

Entry points:
  uv run samplemind --help          CLI (Typer — 21 commands)
  uv run samplemind api             FastAPI auth server
  uv run samplemind serve           Flask web UI

Version history:
  0.2.0 — SQLModel + Alembic ORM, JWT/RBAC auth, Typer CLI (8 commands)
  0.3.0 — FL Studio integration (filesystem, AppleScript, MIDI, clipboard)
  0.4.0 — Tauri 2 desktop app, Svelte 5 UI, JUCE 8 VST3/AU plugin (sidecar IPC)
  0.5.0 — Semantic search (CLAP embeddings), AI curation (pydantic-ai),
           cloud sync (R2/S3), analytics (Plotly), sample packs (.smpack)
  0.6.0 — AI generation (MockBackend + AudioCraft + Stable Audio),
           marketplace models (Stripe, R2 CDN), Supabase metadata sync (21 cmds)
"""

__version__ = "0.6.0"
