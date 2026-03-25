# Memory: Classifier Thresholds

Rule-based classifiers in `src/samplemind/analyzer/classifier.py`.
These exact thresholds are tested in `tests/test_classifier.py` — changing them breaks tests.

## Energy — `classify_energy(rms)`

Evaluated top-to-bottom; first match wins:

| Result | Condition |
|--------|-----------|
| `"high"` | `rms >= 0.060` |
| `"mid"` | `rms >= 0.015` |
| `"low"` | `rms < 0.015` |

⚠ **Never use `"medium"`** — the valid values are `"low"`, `"mid"`, `"high"` only.

## Instrument — `classify_instrument(...)` — first match wins

| Result | Conditions |
|--------|-----------|
| `"loop"` | `dur > 2.0` AND `onset_mean > 0.8` |
| `"hihat"` | `flat > 0.2` AND `zcr > 0.1` AND `rolloff > 0.3` AND `dur < 1.0` |
| `"kick"` | `lfr > 0.35` AND `onset_max > 4.0` AND `dur < 0.8` AND `zcr < 0.08` |
| `"snare"` | `onset_max > 3.0` AND `flat > 0.05` AND `dur < 0.8` AND `lfr < 0.35` |
| `"bass"` | `lfr > 0.3` AND `flat < 0.05` AND `dur > 0.3` |
| `"pad"` | `dur > 1.5` AND `onset_mean < 1.5` AND `centroid > 0.08` |
| `"lead"` | `centroid > 0.15` AND `flat < 0.1` AND `dur < 3.0` |
| `"sfx"` | `flat > 0.1` |
| `"unknown"` | none matched |

Variable aliases: `lfr` = `low_freq_ratio`, `flat` = `flatness`, `centroid` = `centroid_norm`

## Mood — `classify_mood(...)` — first match wins

| Result | Conditions |
|--------|-----------|
| `"aggressive"` | `zcr > 0.08` AND `onset_mean > 3.0` AND `centroid > 0.15` |
| `"dark"` | `centroid < 0.12` AND `minor_key` |
| `"melancholic"` | `minor_key` AND `rms < 0.03` AND `onset_mean < 1.5` |
| `"chill"` | `centroid < 0.15` AND `rms < 0.05` AND `onset_mean < 2.0` |
| `"euphoric"` | `major_key` AND `centroid > 0.12` AND `rms > 0.02` |
| `"neutral"` | none matched |

## Debugging Wrong Classifications

```bash
uv run samplemind analyze "<path>" --json | python -m json.tool
```

Compare raw values vs thresholds above. The first classifier whose ALL conditions are
satisfied wins — check conditions in order, not just the failing one.

Fix locations:
- Thresholds: `src/samplemind/analyzer/classifier.py`
- Fixtures: `tests/conftest.py` → `kick_wav`, `hihat_wav`, `bass_wav`, etc.
- Extraction: `src/samplemind/analyzer/audio_analysis.py` → `analyze_file()`

