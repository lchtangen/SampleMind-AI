# Skill: pack

Create, import, verify, or list `.smpack` sample pack files.
`.smpack` is a ZIP archive containing `manifest.json` and audio files.

> **Phase 9 feature** — check that `src/samplemind/packs/` exists before running.
> If missing, see `docs/en/phase-09-sample-packs.md`.

## When to use

Use this skill when the user asks to:
- Package a filtered subset of samples into a `.smpack` file
- Import a received `.smpack` pack into the library
- Verify the integrity of a `.smpack` file
- List the contents of a `.smpack` file

## Commands

### Create a pack

```bash
uv run samplemind pack create "<name>" <slug> [--instrument <inst>] [--energy <e>] [--mood <m>]
```

Example:
```bash
uv run samplemind pack create "Trap Kicks Vol 1" trap-kicks-v1 --instrument kick --energy high
```

### Import a pack

```bash
uv run samplemind pack import ~/Downloads/trap-pack.smpack
```

### Verify a pack

```bash
uv run samplemind pack verify my-pack.smpack
```

### List pack contents

```bash
uv run samplemind pack list my-pack.smpack
```

## .smpack Format

ZIP archive with:
- `manifest.json` — metadata (name, slug, version, author, description, sample list)
- `samples/` — WAV files with relative paths

## Inputs for `create`

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| name | string | yes | Display name e.g. "Trap Kicks Vol 1" |
| slug | string | yes | URL-safe e.g. `trap-kicks-v1` |
| --instrument | enum | no | loop/hihat/kick/snare/bass/pad/lead/sfx/unknown |
| --energy | enum | no | low/mid/high |
| --mood | enum | no | dark/chill/aggressive/euphoric/melancholic/neutral |
| --author | string | no | Creator name |

## Outputs

| Command | Key outputs |
|---------|-------------|
| create | `pack_path`, `count`, `size_mb`, `sha256` |
| import | `imported`, `skipped` (duplicates), `errors` |
| verify | `status` (PASS/FAIL), `issues` list |
| list | `manifest` metadata, `samples` table |

## Phase check

```bash
ls src/samplemind/packs/ 2>/dev/null || echo "Phase 9 not implemented yet"
```

## Key source files (Phase 9)

- `src/samplemind/packs/manifest.py` — manifest model
- `src/samplemind/packs/builder.py` — pack creation
- `src/samplemind/packs/importer.py` — pack import
- `src/samplemind/cli/commands/pack_cmd.py` — CLI handler

## Related skills

- `search-library` — find samples to include in the pack
- `tag` — ensure samples are tagged before packing
- `import-samples` — import packs after download

