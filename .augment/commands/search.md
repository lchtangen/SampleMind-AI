# /search — Search the Sample Library

Search the SampleMind library with text query and/or metadata filters.

## Arguments

$ARGUMENTS
Usage: /search [query] [--instrument TYPE] [--energy LEVEL] [--mood MOOD] [--bpm-min N] [--bpm-max N] [--key KEY]

Examples:
  /search kick                          — text search for "kick"
  /search --instrument hihat            — all hihats
  /search --energy high --mood dark     — high-energy dark samples
  /search 808 --instrument bass --bpm-min 120 --bpm-max 160
  /search --key "C min"                 — samples in C minor

Valid values:
  --instrument: kick, snare, hihat, bass, pad, unknown
  --energy:     low, medium, high
  --mood:       dark, neutral, bright

---

Search the SampleMind library using the query and filters in: $ARGUMENTS

**Step 1 — Parse the arguments:**
Extract:
- Text query (first positional argument, if any)
- `--instrument`, `--energy`, `--mood`, `--bpm-min`, `--bpm-max`, `--key` filters

**Step 2 — Run the search:**

*Phase 4+ (Typer CLI):*
```bash
uv run samplemind search [--query "..."] [--instrument ...] [--energy ...] [--json]
```

*Current state (argparse):*
```bash
python src/main.py search [--query "..."] [--energy ...] [--instrument ...]
```

*Direct DB query (if CLI not available):*
```python
import sys; sys.path.insert(0, "src")
from data.database import search_samples
results = search_samples(query="...", energy="...", instrument="...")
for r in results: print(r)
```

**Step 3 — Display results:**
Show results in a table:

| # | Filename | BPM | Key | Instrument | Mood | Energy | Duration |
|---|----------|-----|-----|-----------|------|--------|----------|

If no results: suggest loosening filters (e.g., remove --key constraint, broaden energy range).

**Step 4 — Offer actions on results:**
For the top result, offer:
- `/analyze <path>` to see full feature breakdown
- Copy path to clipboard (show the path)
- Export to FL Studio (`uv run samplemind export --fl-studio`)
