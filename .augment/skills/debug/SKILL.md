---
name: debug
description: Debug wrong instrument, energy, or mood classifier labels using feature value inspection
---

# Skill: debug

Debug audio classification issues: wrong instrument, energy, or mood labels.
Walks through classifier rules step-by-step against raw feature values.

## When to use

Use this skill when the user asks to:
- Debug why a sample is classified as the wrong instrument
- Understand why energy is `low` when it should be `high`
- Walk through classifier thresholds for a specific file
- Find which threshold to adjust to fix a misclassification
- Debug a failing classifier test

## Step-by-step debug process

### Step 1 — Extract raw features

```bash
uv run samplemind analyze "<path>" --json | python -m json.tool
```

Focus on these 9 values: `rms`, `centroid_norm`, `zcr`, `flatness`, `rolloff_norm`,
`onset_mean`, `onset_max`, `low_freq_ratio`, `duration`

### Step 2 — Check energy first

| Your `rms` | Result |
|-----------|--------|
| ≥ 0.060 | `"high"` |
| ≥ 0.015 | `"mid"` |
| < 0.015 | `"low"` |

### Step 3 — Walk instrument rules (first match wins)

Check each rule in order with your values:

| Instrument | Conditions to check |
|-----------|---------------------|
| `loop` | `dur > 2.0` AND `onset_mean > 0.8` |
| `hihat` | `flat > 0.2` AND `zcr > 0.1` AND `rolloff > 0.3` AND `dur < 1.0` |
| `kick` | `lfr > 0.35` AND `onset_max > 4.0` AND `dur < 0.8` AND `zcr < 0.08` |
| `snare` | `onset_max > 3.0` AND `flat > 0.05` AND `dur < 0.8` AND `lfr < 0.35` |
| `bass` | `lfr > 0.3` AND `flat < 0.05` AND `dur > 0.3` |
| `pad` | `dur > 1.5` AND `onset_mean < 1.5` AND `centroid > 0.08` |
| `lead` | `centroid > 0.15` AND `flat < 0.1` AND `dur < 3.0` |
| `sfx` | `flat > 0.1` |

### Step 4 — Walk mood rules (first match wins)

| Mood | Conditions |
|------|-----------|
| `aggressive` | `zcr > 0.08` AND `onset_mean > 3.0` AND `centroid > 0.15` |
| `dark` | `centroid < 0.12` AND minor key |
| `melancholic` | minor key AND `rms < 0.03` AND `onset_mean < 1.5` |
| `chill` | `centroid < 0.15` AND `rms < 0.05` AND `onset_mean < 2.0` |
| `euphoric` | major key AND `centroid > 0.12` AND `rms > 0.02` |
| `neutral` | none matched |

### Step 5 — Fix location

If the wrong rule fired because of a borderline value:
- **Adjust threshold**: `src/samplemind/analyzer/classifier.py`
- **Fix test fixture**: `tests/conftest.py` → `kick_wav`, `hihat_wav`, etc.
- **Fix extraction**: `src/samplemind/analyzer/audio_analysis.py`

## Debug prompt template

> "I have `<path>` classified as `<actual>` but expected `<expected>`. Here are the raw values: `rms=X, zcr=X, flat=X, ...`. Which condition failed?"

## Common misclassification causes

| Symptom | Likely cause |
|---------|-------------|
| Kick classified as `snare` | `onset_max` just above 3.0 but `lfr` not high enough |
| Hihat classified as `sfx` | `flatness > 0.1` fires before hihat rule |
| Short bass classified as `kick` | `dur < 0.8` makes it look like a one-shot |
| Aggressive mood when expecting chill | `zcr > 0.08` or `onset_mean > 3.0` |

## Related skills

- `analyze-audio` — full feature extraction reference
- `run-tests` — run `tests/test_classifier.py` after fixing thresholds

