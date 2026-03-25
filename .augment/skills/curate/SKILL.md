---
name: curate
description: AI-powered library curation using LLMs to organize samples and generate smart playlists
---

# Skill: curate

AI-powered library curation using LLMs — organize, analyze gaps, generate smart playlists.

## Commands

```bash
# Library statistics (no LLM needed)
uv run samplemind curate analyze
uv run samplemind curate analyze --json

# AI curation (dry-run by default — shows actions without applying)
uv run samplemind curate "create a dark trap playlist"
uv run samplemind curate "find gaps in my library" --model ollama/llama3.2
uv run samplemind curate "organize by energy and mood" --model anthropic/claude-sonnet-4-5

# Apply actions (--execute flag required)
uv run samplemind curate "create dark trap set" --execute

# Rule-based playlists (no LLM, works offline)
uv run samplemind playlist by-bpm --target 140 --tolerance 5
uv run samplemind playlist energy-arc                  # low → mid → high → low
uv run samplemind playlist by-key "A min" --circle     # circle of fifths
uv run samplemind playlist similar-to --id 42
```

## Key Files

```
src/samplemind/agent/
  library_analyzer.py    # analyze_library() → LibrarySnapshot
  curator.py             # curate(goal) → {actions, insights, questions}
  playlist_generator.py  # rule-based: by_bpm, by_energy_arc, similar_to

src/samplemind/cli/commands/curate_cmd.py
tests/test_ai_curation.py
```

## LLM Providers

| Provider | Env Var | Cost |
|----------|---------|------|
| `anthropic/claude-sonnet-4-5` | `SAMPLEMIND_ANTHROPIC_API_KEY` | ~$0.003/request |
| `openai/gpt-4o` | `SAMPLEMIND_OPENAI_API_KEY` | ~$0.005/request |
| `ollama/llama3.2` | (none — local) | Free |

Auto-select: Claude if `SAMPLEMIND_ANTHROPIC_API_KEY` is set, else Ollama.

## Action Types (from LLM JSON response)

```python
{"type": "create_playlist", "args": {"name": "...", "sample_ids": [1, 42, 87]}}
{"type": "tag_sample",      "args": {"id": 42, "tags": "trap,dark,featured"}}
{"type": "update_mood",     "args": {"id": 42, "mood": "dark"}}  # valid moods only
{"type": "suggest_imports", "args": {"query": "...", "reason": "..."}}
```

## Feature Flag

```python
from samplemind.core.feature_flags import is_enabled
# curate analyze works without flag; LLM features require:
if not is_enabled("ai_curation"):
    raise typer.Exit(1)
```

## Testing

```bash
uv run pytest tests/test_ai_curation.py -v
```

**Rule:** ALL `litellm.completion` calls must be mocked in tests. No API keys in CI.

## Dependencies

```bash
uv add litellm anthropic openai   # cloud LLMs
# Local (free): install Ollama from https://ollama.ai, then:
# ollama pull llama3.2
```

