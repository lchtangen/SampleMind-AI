# Skill: analyze-audio

Extract all audio features from a WAV or AIFF file using librosa and run the
rule-based classifiers. Outputs a JSON feature dict with 13 fields.

## When to use

Use this skill when the user asks to:
- Analyze a WAV/AIFF file for BPM, key, mood, energy, or instrument
- Debug a wrong classifier result
- Extract raw feature values (RMS, ZCR, centroid, flatness, rolloff, onset, low_freq_ratio)
- Compute an audio fingerprint (SHA-256 of first 64 KB)

## Command

```bash
uv run samplemind analyze "<path>" --json
```

For batch mode (directory):
```bash
uv run samplemind analyze "<dir>" --json --workers <N>
```

## Inputs

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| path      | string | yes      | Absolute or relative path to WAV/AIFF file or directory |
| --workers | int    | no       | Parallel workers for batch (default: auto = cpu_count) |
| --json    | flag   | yes      | Output JSON to stdout (always pass this) |

## Output fields (JSON to stdout)

| Field          | Example   | Notes |
|----------------|-----------|-------|
| filename       | kick.wav  | |
| bpm            | 140.0     | librosa beat_track |
| key            | C min     | |
| rms            | 0.072     | `sqrt(mean(y**2))` — NOT `librosa.feature.rms()` |
| centroid_norm  | 0.143     | normalized to 0–1 (divided by sr/2) |
| zcr            | 0.043     | zero-crossing rate |
| flatness       | 0.031     | 0 = pure tone, 1 = white noise |
| rolloff_norm   | 0.298     | normalized spectral rolloff |
| onset_mean     | 3.2       | mean rhythmic attack strength |
| onset_max      | 5.1       | peak rhythmic attack strength |
| low_freq_ratio | 0.41      | bass presence below 300 Hz |
| duration       | 0.48      | seconds |
| energy         | high      | `low` / `mid` / `high` — **never `medium`** |
| instrument     | kick      | loop/hihat/kick/snare/bass/pad/lead/sfx/unknown |
| mood           | dark      | dark/chill/aggressive/euphoric/melancholic/neutral |
| sha256         | a3f2...   | SHA-256 of first 64 KB (fingerprint for dedup) |

## Classifier thresholds

**Energy** (checked in order):
- `high`: rms ≥ 0.060
- `mid`:  rms ≥ 0.015
- `low`:  rms < 0.015

**Instrument** (first match wins):
1. loop   — dur > 2.0 AND onset_mean > 0.8
2. hihat  — flat > 0.2 AND zcr > 0.1 AND rolloff > 0.3 AND dur < 1.0
3. kick   — lfr > 0.35 AND onset_max > 4.0 AND dur < 0.8 AND zcr < 0.08
4. snare  — onset_max > 3.0 AND flat > 0.05 AND dur < 0.8 AND lfr < 0.35
5. bass   — lfr > 0.3 AND flat < 0.05 AND dur > 0.3
6. pad    — dur > 1.5 AND onset_mean < 1.5 AND centroid > 0.08
7. lead   — centroid > 0.15 AND flat < 0.1 AND dur < 3.0
8. sfx    — flat > 0.1
9. unknown — (none matched)

**Mood** (first match wins):
1. aggressive  — zcr > 0.08 AND onset_mean > 3.0 AND centroid > 0.15
2. dark        — centroid < 0.12 AND minor_key
3. melancholic — minor_key AND rms < 0.03 AND onset_mean < 1.5
4. chill       — centroid < 0.15 AND rms < 0.05 AND onset_mean < 2.0
5. euphoric    — major_key AND centroid > 0.12 AND rms > 0.02
6. neutral     — (none matched)

## Examples

```bash
# Analyze a single file
uv run samplemind analyze ~/Music/kick_808.wav --json

# Pretty-print the JSON output
uv run samplemind analyze ~/Music/kick_808.wav --json | python -m json.tool

# Batch-analyze a folder with 4 workers
uv run samplemind analyze ~/Music/Samples/ --json --workers 4
```

## Debugging wrong classification

If a file is misclassified, compare its `rms`, `zcr`, `flatness`, `onset_max`,
and `low_freq_ratio` values against the thresholds above. The relevant source
files are:
- `src/samplemind/analyzer/audio_analysis.py` — feature extraction
- `src/samplemind/analyzer/classifier.py` — threshold rules

## Related skills

- `import-samples` — bulk import and analyze
- `search-library` — query the library after analysis
- `run-tests` — run `tests/test_audio_analysis.py` and `tests/test_classifier.py`

