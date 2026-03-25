# /analyze — Analyze a WAV File

Run audio feature extraction on a WAV file and show all 8 features, classifications,
optional audio fingerprint, and raw feature table.

## Arguments

$ARGUMENTS
Required: path to a WAV or AIFF file (absolute or relative to repo root)
Optional flags:
  --fingerprint   also compute SHA-256 fingerprint and check for duplicates in library
  --features      show raw feature values in a detailed table
  --batch <dir>   analyze all WAV files in a directory (batch mode)
  --workers N     number of parallel workers for batch mode (0 = auto)

Examples:
  /analyze ~/Music/Samples/kick_808.wav
  /analyze samples/test.wav --fingerprint
  /analyze ~/Music/Samples/kick_808.wav --features
  /analyze ~/Music/Samples/ --batch --workers 4

---

Analyze the audio file or directory specified in: $ARGUMENTS

**Step 1 — Parse arguments:**
Check for `--batch`, `--fingerprint`, `--features`, `--workers` flags in $ARGUMENTS.
Extract the file/directory path (the non-flag argument).

**Step 2 — Batch mode (if --batch flag or path is a directory):**
If batch mode, scan the path for all .wav, .aif, .aiff files.
Count total files and report.
Run batch analysis:
```bash
uv run samplemind analyze "<dir>" --json --workers <N>
```
Or if workers flag: `uv run samplemind analyze "<dir>" --json --workers <N>`
Show progress (N/total).
After completion, show a summary table:
| Filename | BPM | Key | Instrument | Mood | Energy |
|----------|-----|-----|------------|------|--------|
| ...      | ... | ... | ...        | ...  | ...    |
Skip to Step 6 for batch.

**Step 3 — Validate the file (single file mode):**
- Check the path exists and is a WAV/AIFF file
- If not found, suggest checking the path

**Step 4 — Run analysis:**
Try the appropriate command based on project state:

*If `uv` and `pyproject.toml` exist (Phase 1+ complete):*
```bash
uv run samplemind analyze "<path>" --json
```

*If still on the current flat layout:*
```bash
python src/main.py analyze "<path>"
```

*Direct Python (fallback):*
```python
import sys
sys.path.insert(0, "src")
from analyzer.audio_analysis import analyze_file
result = analyze_file("<path>")
print(result)
```

**Step 5 — Display results:**

Show a formatted summary table:

| Feature | Value | Meaning |
|---------|-------|---------|
| BPM | — | Tempo in beats per minute |
| Key | — | Musical key (e.g. "C min") |
| Instrument | — | Detected type (kick/snare/hihat/bass/pad/unknown) |
| Mood | — | dark / neutral / bright |
| Energy | — | low / medium / high |
| Duration | — | Length in seconds |

If `--features` flag was passed, also show the raw feature table:

| Raw Feature | Value | Notes |
|-------------|-------|-------|
| rms | — | Amplitude (>0.06=high energy, >0.015=medium) |
| spectral_centroid | — | Brightness normalized to Nyquist |
| zero_crossing_rate | — | Texture (hihats≈0.35, kicks≈0.03) |
| spectral_flatness | — | 0=pure tone, 1=white noise |
| spectral_rolloff | — | 85% energy frequency (normalized) |
| onset_mean | — | Average rhythmic attack strength |
| onset_max | — | Peak rhythmic attack strength |
| low_freq_ratio | — | Bass presence below 300 Hz |

**Step 6 — Fingerprint check (if --fingerprint flag):**
Compute SHA-256 of first 64KB of the file:
```python
import hashlib
with open(path, "rb") as f:
    fp = hashlib.sha256(f.read(65536)).hexdigest()
print(f"Fingerprint: {fp[:16]}...{fp[-8:]}")
```
Then check the library for existing samples with the same fingerprint:
```bash
uv run samplemind search --fingerprint "<fp>" --json
```
If duplicates found: report "⚠ Duplicate detected: this file already exists as <filename>"
If no duplicates: report "✓ No duplicates found in library"

**Step 7 — Interpret results:**
Briefly explain what the classification means for this sample in FL Studio context.
For example:
- "kick (high energy, dark) → good for trap/hip-hop drop sections"
- "hihat (low energy, bright) → works as open hat in rhythmic patterns"

If the classification seems wrong (e.g., a kick classified as hihat), explain:
- Which specific feature values triggered the classification
- What the classifier thresholds are (from classifier.py)
- Suggest: "run /check and examine classifier.py thresholds for calibration"
