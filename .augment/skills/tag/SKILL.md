# Skill: tag

Manually tag a sample in the library with genre, mood, energy, and free-form tags.
Tagged fields (`genre`, `tags`) are **never overwritten** on re-import.

## When to use

Use this skill when the user asks to:
- Set a genre on a sample (trap, lofi, house, dnb, techno, etc.)
- Override the auto-detected mood, energy, or instrument
- Add free-form tags (comma-separated)
- Re-tag a misclassified sample

## Command

```bash
uv run samplemind tag "<name>" [--genre <genre>] [--mood <mood>] [--energy <energy>] [--tags <tags>]
```

`<name>` is a case-insensitive partial match on filename.

## Inputs

| Parameter | Type | Valid values | Notes |
|-----------|------|-------------|-------|
| name | string | any | Partial filename match |
| --genre | string | free-form | e.g. `trap`, `lofi`, `house`, `dnb` |
| --mood | enum | `dark` `chill` `aggressive` `euphoric` `melancholic` `neutral` | |
| --energy | enum | `low` `mid` `high` | ⚠ **never `medium`** |
| --tags | string | comma-separated | e.g. `"punchy,808,sub"` |
| --json | flag | — | Output JSON to stdout |

## Examples

```bash
# Set genre and energy
uv run samplemind tag kick_808 --genre trap --energy high

# Override mood and add tags
uv run samplemind tag break_loop --mood aggressive --tags "break,loop,drum"

# Full tag with JSON output
uv run samplemind tag pad_c_minor --mood melancholic --genre lofi --json
```

## Field overwrite rules

| Field | Auto-detected | Manually tagged | Re-import behaviour |
|-------|-------------|-----------------|---------------------|
| `bpm`, `key`, `instrument` | ✅ yes | — | **Overwritten** on re-import |
| `mood`, `energy` | ✅ yes | ✅ can override | **Overwritten** unless manually set |
| `genre`, `tags` | ✅ no | ✅ yes | **Never overwritten** |

## Key source files

- `src/samplemind/cli/commands/tag_cmd.py` — CLI handler
- `src/samplemind/data/repositories/sample_repository.py` — `SampleRepository.tag()`
- `src/samplemind/core/models/sample.py` — `SampleUpdate` model

## Related skills

- `list-samples` — find the exact sample filename first
- `search-library` — filter samples to identify what needs tagging
- `analyze-audio` — check current classifier output before overriding

