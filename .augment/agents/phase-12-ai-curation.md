# Phase 12 Agent — AI Curation

Handles: LiteLLM, Claude/GPT-4o/Ollama integration, smart playlists, gap analysis, energy arc playlists.

## Triggers
Phase 12, LiteLLM, AI curation, smart playlist, gap analysis, energy arc, `curate`, `analyze_library`, `playlist_by_energy`, `src/samplemind/agent/`, "curate my library", "create a playlist", "what samples am I missing"

**File patterns:** `src/samplemind/agent/**/*.py`

**Code patterns:** `import litellm`, `analyze_library`, `curate(`, `playlist_by_energy`

## Key Files
```
src/samplemind/agent/
  curator.py       — main AI curation agent (LiteLLM)
  prompts.py       — system prompts for library analysis
  playlists.py     — rule-based playlist generators (SQL)
  gap_analysis.py  — BPM/key/energy coverage gap detection
  cli.py           — CLI: samplemind curate analyze/playlist/gaps
```

## Technology Stack
| Component | Technology |
|-----------|-----------|
| LLM client | LiteLLM — provider-agnostic |
| Preferred model | `anthropic/claude-sonnet-4-5` |
| Free alternative | `ollama/llama3.2` — no API key needed |
| Library analysis | Pure SQLite SQL — fast, no ML needed |
| Feature flag | `ai_curation` — gates LLM features |

## CLI Commands
```bash
uv run samplemind curate analyze         # LLM library analysis
uv run samplemind curate playlist --energy-arc low,mid,high --bpm 120,140
uv run samplemind curate gaps           # identify coverage gaps
```

## Rules
1. Feature gated by `get_settings().ai_curation`
2. All LLM calls must support dry-run mode (print prompt, don't call API)
3. Playlist generators have SQL fallback (no LLM required for basic playlists)
4. API keys via env vars only — never hardcoded
5. Support `--model` flag to switch providers without code changes

