# /export — Export Samples

Copy filtered samples from the SampleMind library to a target directory — FL Studio folder,
external drive, project folder, or any destination. Supports all standard search filters.

## Arguments

$ARGUMENTS
Required:
  --target <dir>        Destination directory (created if it doesn't exist)

Optional filters (at least one recommended):
  --instrument <type>   kick | hihat | snare | bass | loop | pad | lead | sfx | unknown
  --energy <level>      low | mid | high
  --mood <mood>         dark | chill | aggressive | euphoric | melancholic | neutral
  --bpm-min <n>         Minimum BPM (inclusive)
  --bpm-max <n>         Maximum BPM (inclusive)
  --genre <genre>       Filter by user-tagged genre
  --query <text>        Text search across filename, path, tags

Optional behavior:
  --dry-run             Show what would be copied without copying anything
  --flat                Copy all files into target root (no subdirectories)
  --overwrite           Replace existing files at destination (default: skip)
  --json                Output copy report as JSON to stdout

Examples:
  /export --target ~/FL/Kicks --instrument kick
  /export --target ~/Projects/Track1/Samples --energy high --bpm-min 130 --bpm-max 145
  /export --target /tmp/preview --dry-run --instrument bass
  /export --target ~/FL/Samples --json

FL Studio quick-export paths (macOS):
  FL Studio 20: ~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/
  FL Studio 21: ~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/

---

Parse all flags from $ARGUMENTS. `--target` is required — show error and stop if missing.

**Step 1 — Validate target:**

```bash
# Check destination is writable (create if --target doesn't exist)
mkdir -p "$TARGET_DIR" 2>/dev/null || echo "ERROR: cannot create $TARGET_DIR"
```

**Step 2 — Run export command:**

```bash
uv run samplemind export --target "$TARGET_DIR" [all parsed filter flags]
```

If the `export` subcommand is not yet implemented, fall back to a Python script:

```python
uv run python -c "
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository
import shutil, pathlib, json

init_orm()
results = SampleRepository.search(
    query='$QUERY',
    instrument='$INSTRUMENT',
    energy='$ENERGY',
    mood='$MOOD',
)
target = pathlib.Path('$TARGET_DIR')
target.mkdir(parents=True, exist_ok=True)

copied, skipped = 0, 0
for s in results:
    src = pathlib.Path(s.path)
    if not src.exists():
        skipped += 1
        continue
    dst = target / src.name
    if dst.exists() and not OVERWRITE:
        skipped += 1
        continue
    if not DRY_RUN:
        shutil.copy2(src, dst)
    copied += 1

print(json.dumps({'copied': copied, 'skipped': skipped, 'target': str(target)}))
"
```

**Step 3 — Display result:**

If `--json`: print raw JSON to stdout.

Otherwise:

```
Export Complete — SampleMind-AI
══════════════════════════════════════════
Filter:  instrument=kick, energy=high
Target:  ~/FL/Kicks/
──────────────────────────────────────────
Copied:  42 files
Skipped: 3 files (already exist — use --overwrite to replace)
Total:   45 matched
══════════════════════════════════════════
Tip: in FL Studio, press F5 → right-click the target folder → Refresh
```

If `--dry-run`, prepend `DRY RUN — no files were copied` and list the files that would be copied.
