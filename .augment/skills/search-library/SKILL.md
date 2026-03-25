---
name: search-library
description: Search the SampleMind library with free-text queries and metadata filters for BPM, key, energy
---

# Skill: search-library

Search the SampleMind library with free-text queries and/or metadata filters
(instrument, energy, mood, BPM range, key). Returns JSON results.

## When to use

Use this skill when the user asks to:
- Find samples by name, genre, or tag
- Filter by instrument type, energy level, or mood
- Find samples in a BPM or key range
- List all samples in the library

## Commands

Free-text search:
```bash
uv run samplemind search --query "<term>" --json
```

With filters:
```bash
uv run samplemind search --instrument kick --energy high --json
uv run samplemind search --mood dark --bpm-min 120 --bpm-max 160 --json
uv run samplemind search --key "C min" --json
```

List all samples (no filter):
```bash
uv run samplemind list --json
```

## Inputs

| Parameter     | Type   | Required | Valid values / notes |
|---------------|--------|----------|----------------------|
| --query       | string | no       | Free-text match on filename and tags |
| --instrument  | enum   | no       | loop / hihat / kick / snare / bass / pad / lead / sfx / unknown |
| --energy      | enum   | no       | low / **mid** / high — ⚠ **never `medium`** |
| --mood        | enum   | no       | dark / chill / aggressive / euphoric / melancholic / neutral |
| --bpm-min     | int    | no       | Minimum BPM (inclusive) |
| --bpm-max     | int    | no       | Maximum BPM (inclusive) |
| --key         | string | no       | Musical key e.g. `"C min"` or `"G maj"` |
| --json        | flag   | yes      | Always pass for machine-readable output |

## Output (JSON to stdout)

```json
[
  {
    "id": 1,
    "filename": "kick_808.wav",
    "path": "/home/ubuntu/Music/kick_808.wav",
    "bpm": 140.0,
    "key": "C min",
    "instrument": "kick",
    "mood": "dark",
    "energy": "high",
    "duration": 0.48,
    "genre": "trap",
    "tags": "808,sub"
  }
]
```

## Examples

```bash
# Text search
uv run samplemind search --query kick --json

# All hihats
uv run samplemind search --instrument hihat --json

# High-energy dark samples
uv run samplemind search --energy high --mood dark --json

# 808 bass in a BPM range
uv run samplemind search --query 808 --instrument bass --bpm-min 120 --bpm-max 160 --json

# Samples in C minor
uv run samplemind search --key "C min" --json

# List everything
uv run samplemind list --json
```

## No results?

If a search returns nothing, suggest:
1. Removing the `--key` constraint (key detection is approximate)
2. Broadening the energy level (`mid` instead of `high`)
3. Checking that samples were imported: `uv run samplemind list --json`

## Web UI alternative

The Flask web UI offers live search via HTMX at `http://localhost:5000`.
Start it with `uv run samplemind serve`.

## Related skills

- `import-samples` — load samples into the library first
- `analyze-audio` — inspect individual sample features
- `serve` — browse results in the web UI

