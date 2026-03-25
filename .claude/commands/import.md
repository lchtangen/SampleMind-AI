# /import — Import Samples to Library

Import a folder of audio samples into the SampleMind library database.

## Arguments

$ARGUMENTS
Required: path to a folder containing WAV/AIFF files
Optional flags:
  --recursive    scan subdirectories too
  --dry-run      show what would be imported without actually doing it
Example: /import ~/Music/Samples/Kicks/
Example: /import ~/Downloads/sample-pack/ --recursive

---

Import audio samples from the folder in: $ARGUMENTS

**Step 1 — Validate the folder:**
Check that the specified path exists and is a directory. If not, tell the user.
Count how many audio files (*.wav, *.aiff, *.mp3) are in the folder (and subdirs if --recursive).

**Step 2 — Run the import:**
Choose the appropriate command based on project state:

*Phase 4+ (Typer CLI with uv):*
```bash
uv run samplemind import "<path>" [--recursive] [--json]
```

*Current state (argparse CLI):*
```bash
python src/main.py import "<path>"
```

Show a progress indicator while importing. If the import supports `--json` output, parse it
and display a Rich-style summary table.

**Step 3 — Show results:**
After import completes, show:
- Number of files imported successfully
- Number skipped (already in library)
- Number with errors (and what the errors were)
- Total library size after import

**Step 4 — Offer next steps:**
Suggest:
- `/search kick` to find specific samples
- `/analyze <path>` to check a specific file's analysis
- Open the web UI (`python src/web/app.py`) to browse visually

**If no CLI is set up yet:**
Run the analysis directly via Python and show what would be imported.
Suggest following `docs/en/phase-01-foundation.md` to set up the proper CLI first.
