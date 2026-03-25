# Phase 12 Agent — AI Curation

Handles: LiteLLM, library analysis, smart playlists, gap analysis, energy arc, circle of fifths.

## Triggers
- Phase 12, AI curation, LiteLLM, library analysis, smart playlist, gap analysis, energy arc, circle of fifths, curate

## Key Files
- `src/samplemind/agent/library_analyzer.py`
- `src/samplemind/agent/curator.py`
- `src/samplemind/agent/playlist_generator.py`
- `src/samplemind/cli/commands/curate_cmd.py`

## LLM Providers

| Model | Requires |
|-------|---------|
| `anthropic/claude-sonnet-4-5` | `SAMPLEMIND_ANTHROPIC_API_KEY` |
| `openai/gpt-4o` | `SAMPLEMIND_OPENAI_API_KEY` |
| `ollama/llama3.2` | Ollama installed locally (free) |

## LLM Response Schema

```json
{
  "reasoning": "...",
  "suggested_actions": [
    {"type": "create_playlist", "args": {...}, "description": "..."}
  ],
  "questions": [],
  "insights": "..."
}
```

## Rules
1. dry_run=True by default — NEVER apply actions without `--execute`
2. LLM must only reference sample IDs that exist in the library snapshot
3. Mock `litellm.completion` in ALL tests — no API keys in CI
4. Feature flag `ai_curation` required for LLM features
5. `curate analyze` works WITHOUT the feature flag (just SQL stats)
6. Temperature 0.3 for consistent structured JSON output
7. `response_format={"type": "json_object"}` prevents non-JSON responses

