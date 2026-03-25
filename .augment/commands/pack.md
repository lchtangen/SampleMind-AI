# /pack — Manage Sample Packs (.smpack)

Create, import, verify, or list .smpack sample pack files.

## Arguments

$ARGUMENTS
Actions:
  create <name> <slug>        — export filtered library as .smpack
  import <path>               — import .smpack into library
  verify <path>               — validate .smpack without importing
  list <path>                 — show contents of .smpack

Options for create:
  --instrument TYPE   filter by instrument (kick/snare/hihat/bass/pad)
  --energy LEVEL      filter by energy (low/medium/high)
  --mood MOOD         filter by mood (dark/neutral/bright)
  --author NAME       pack author name
  --desc TEXT         pack description

Examples:
  /pack create "Trap Kicks" trap-kicks-v1 --instrument kick --energy high
  /pack import ~/Downloads/trap-pack.smpack
  /pack verify my-pack.smpack
  /pack list my-pack.smpack

---

Manage .smpack sample packs. Parse the action and arguments from: $ARGUMENTS

**Step 1 — Determine action:**
Parse the first word of $ARGUMENTS as the action (create/import/verify/list).

**Step 2 — Check Phase 9 is implemented:**
Look for `src/samplemind/packs/` directory.
If it doesn't exist: explain that .smpack support is Phase 9, reference
`docs/en/phase-09-sample-packs.md`, and offer to implement it.

**Step 3 — Run the appropriate command:**

```bash
# create
uv run samplemind pack create "<name>" "<slug>" [--instrument ...] [--energy ...] [--author ...]

# import
uv run samplemind pack import "<path>" [--dest ~/Music/SampleMind/imported/]

# verify
uv run samplemind pack verify "<path>"

# list (table view)
uv run samplemind pack list "<path>"
```

**Step 4 — Display results:**

For **create**: show pack path, sample count, file size, SHA-256 of output file.

For **import**: show imported/skipped/error counts; list any errors with filenames.

For **verify**: show PASS/FAIL; list any issues found (missing files, bad checksums).

For **list**: show manifest metadata (name, version, author) then a table of all samples.

**Step 5 — GitHub Release (for create):**
If creating a pack, offer to publish it:
```bash
gh release create "<slug>" --title "<name>" --notes "Sample pack" "<slug>.smpack"
```
Ask before running this (it's a network operation).
