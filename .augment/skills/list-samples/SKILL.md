# Skill: list-samples

List all samples in the SampleMind library as a Rich table (terminal) or JSON (machine).

## When to use

Use this skill when the user asks to:
- Show all samples in the library
- Count how many samples have been imported
- Get a quick overview of the library contents
- Export the full library list as JSON for processing

## Commands

### Rich table (human-readable)

```bash
uv run samplemind list
```

### JSON output (machine-readable)

```bash
uv run samplemind list --json
```

### Count samples

```bash
uv run samplemind list --json | python -c "import json,sys; print(len(json.load(sys.stdin)))"
```

### Filter by instrument (via search)

```bash
uv run samplemind search --instrument kick --json
```

## Output fields (JSON)

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
    "tags": "808,sub",
    "sha256": "a3f2..."
  }
]
```

## Rich table columns

`filename` | `bpm` | `key` | `instrument` | `mood` | `energy` | `duration` | `genre`

## Empty library?

If the library is empty, import samples first:

```bash
uv run samplemind import ~/Music/Samples/ --json
```

## Web UI alternative

Browse the library visually in a browser:

```bash
uv run samplemind serve
# Open http://localhost:5000
```

## Key source files

- `src/samplemind/cli/commands/list_cmd.py` — CLI handler
- `src/samplemind/data/repositories/sample_repository.py` — `SampleRepository.search()`

## Related skills

- `search-library` — filter with query, instrument, energy, mood, BPM
- `import-samples` — load audio files into the library
- `tag` — update metadata on listed samples

