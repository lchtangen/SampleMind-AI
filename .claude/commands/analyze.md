# /analyze — Analyze a WAV File

Run audio feature extraction on a WAV file and show all 8 features + classifications.

## Arguments

$ARGUMENTS
Required: path to a WAV or AIFF file (absolute or relative to repo root)
Example: /analyze ~/Music/Samples/kick_808.wav
Example: /analyze samples/test.wav

---

Analyze the audio file specified in: $ARGUMENTS

**Step 1 — Validate the file:**
- Check the path exists and is a WAV/AIFF/MP3 file
- If not found, suggest checking the path and confirm the file exists

**Step 2 — Run analysis:**
Try the appropriate command based on project state:

*If `uv` and `pyproject.toml` exist (Phase 1+ complete):*
```bash
uv run samplemind analyze "<path>" --json
```

*If still on the current flat layout:*
```bash
python src/main.py analyze "<path>"
```

*If Python CLI isn't set up yet, run analysis directly:*
```python
import sys
sys.path.insert(0, "src")
from analyzer.audio_analysis import analyze_file
result = analyze_file("<path>")
print(result)
```

**Step 3 — Display results:**
Show a formatted table of all features:

| Feature | Value | Meaning |
|---------|-------|---------|
| BPM | — | Tempo in beats per minute |
| Key | — | Musical key (e.g. "C min") |
| Instrument | — | Detected type (kick/snare/hihat/bass/pad/unknown) |
| Mood | — | dark / neutral / bright |
| Energy | — | low / medium / high |
| Duration | — | Length in seconds |
| RMS | — | Raw amplitude (0.0–1.0) |
| Spectral Centroid | — | Brightness (normalized) |
| ZCR | — | Zero-crossing rate |

**Step 4 — Interpret results:**
Briefly explain what the classification means for this sample and how it would be used in FL Studio.
If the classification seems wrong (e.g., a kick classified as hihat), explain what features caused it
and what the thresholds are (see audio_domain memory or src/analyzer/classifier.py).
