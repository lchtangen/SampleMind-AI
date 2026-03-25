# /tag — Tag a Sample

Manually tag a sample in the library with genre, mood, energy, or custom tags.
Tagged fields are preserved on re-import (never overwritten by auto-analysis).

## Arguments

$ARGUMENTS
Required: sample name (partial filename match, case-insensitive)
Optional:
  --genre <genre>      Music genre (trap, lofi, house, dnb, techno, etc.)
  --mood <mood>        dark | chill | aggressive | euphoric | melancholic | neutral
  --energy <energy>    low | mid | high  ⚠ NEVER "medium"
  --tags <tags>        Comma-separated custom tags (e.g. "punchy,808,sub")

Examples:
  /tag kick_808 --genre trap --energy high
  /tag "break loop" --mood aggressive --tags "break,drum,loop"
  /tag pad_c_min --mood melancholic --genre lofi
  /tag hihat_closed --energy low --genre house

---

Parse the sample name and flags from $ARGUMENTS.

**Step 1 — Validate values:**

- energy must be exactly `"low"`, `"mid"`, or `"high"` — NEVER `"medium"`
- mood must be one of: `dark` `chill` `aggressive` `euphoric` `melancholic` `neutral`
- genre is free-form text
- tags is a comma-separated string (no spaces around commas)

If an invalid value is passed, show the valid options and stop.

**Step 2 — Run the tag command:**

```bash
uv run samplemind tag "<name>" [--genre "<genre>"] [--mood "<mood>"] [--energy "<energy>"] [--tags "<tags>"]
```

**Step 3 — Confirm the update:**

Show the updated sample fields:
```
✓ Tagged: <filename>
  genre:  <genre>    (user-tagged — preserved on re-import)
  mood:   <mood>
  energy: <energy>
  tags:   <tags>
```

**Step 4 — Explain what was changed:**

Auto-detected fields (may be overwritten on re-import):
- bpm, key, instrument — set by librosa analysis

Manually tagged fields (NEVER overwritten on re-import):
- genre, tags — always preserved
- mood, energy — can be manually overridden, will be preserved if set

**Step 5 — Suggest related actions:**

- Search by the new tag: `/search --genre <genre>`
- Bulk tag by filter: "Tag all kick samples as trap: /tag [loop through results]"
- Via web UI: Open http://localhost:5000 → click sample → edit tags

