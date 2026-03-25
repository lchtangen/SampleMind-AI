"""
samplemind — AI-powered audio sample library manager.

Analyzes WAV/AIFF files with librosa (BPM, key, instrument, mood, energy),
stores metadata in SQLite via SQLModel, and surfaces everything through a CLI,
Flask web UI, Tauri desktop app, and JUCE VST3/AU plugin.

Entry points:
  uv run samplemind --help          CLI (Typer)
  uv run samplemind api             FastAPI auth server
  uv run samplemind serve           Flask web UI

Version history:
  0.2.0 — SQLModel + Alembic ORM, JWT/RBAC auth, Typer CLI (8 commands)
"""

__version__ = "0.2.0"
