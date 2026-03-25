# /list — List Library Samples

List all samples in the library with optional filters. Shows a formatted table or JSON.

## Arguments

$ARGUMENTS
Optional filters:
  --key <key>          Musical key, e.g. "C min", "G maj", "F# min"
  --bpm-min <n>        Minimum BPM (inclusive)
  --bpm-max <n>        Maximum BPM (inclusive)
  --instrument <type>  loop|hihat|kick|snare|bass|pad|lead|sfx|unknown
  --energy <level>     low|mid|high  ⚠ NEVER "medium"
  --mood <mood>        dark|chill|aggressive|euphoric|melancholic|neutral
  --genre <genre>      Free-form genre filter (trap, lofi, house, etc.)
  --json               Output raw JSON to stdout

Examples:
  /list
  /list --instrument kick --energy high
  /list --key "C min" --mood dark
  /list --bpm-min 120 --bpm-max 140 --genre trap
  /list --json

---

Parse filters from $ARGUMENTS.

**Step 1 — Build and run the command:**

```bash
uv run samplemind list [--key "..."] [--bpm-min N] [--bpm-max N] \
  [--instrument X] [--energy X] [--mood X] [--genre X] --json
```

**Step 2 — Display results:**

If --json flag: output raw JSON directly.

Otherwise display a formatted table:

```
┌─────┬──────────────────────────┬──────┬────────┬────────────┬──────────┬──────────┐
│ ID  │ Filename                 │  BPM │ Key    │ Instrument │ Energy   │ Mood     │
├─────┼──────────────────────────┼──────┼────────┼────────────┼──────────┼──────────┤
│  1  │ kick_808_hard.wav        │ 140  │ C min  │ kick       │ high     │ dark     │
│  2  │ hihat_closed_trap.wav    │ 140  │ —      │ hihat      │ low      │ neutral  │
└─────┴──────────────────────────┴──────┴────────┴────────────┴──────────┴──────────┘
Total: 2 samples
```

**Step 3 — Show stats summary:**

After the table:
- Total samples matching filters
- BPM range in results
- Instrument breakdown (counts per type)
- Energy distribution (low/mid/high counts)

**Step 4 — Suggest next actions:**

If 0 results:
- "No samples match these filters. Try broader criteria."
- Suggest: `/import ~/Music/Samples/` to add samples

If results found:
- `/analyze <filename>` — analyze a specific file
- `/tag <name> --genre trap` — tag samples from results
- `/search <query>` — text search across results
- Open web UI: `http://localhost:5000` for interactive filtering

**Step 5 — Schema reference:**

Sample fields: id, filename, path, bpm, key, mood, energy, instrument, genre, tags, imported_at
Classifier valid values:
- energy: "low" | "mid" | "high" (NEVER "medium")
- mood: "dark" | "chill" | "aggressive" | "euphoric" | "melancholic" | "neutral"
- instrument: "loop" | "hihat" | "kick" | "snare" | "bass" | "pad" | "lead" | "sfx" | "unknown"

