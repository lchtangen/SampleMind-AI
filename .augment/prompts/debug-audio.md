# Prompt: Debug Audio Classification

Use this prompt when a sample is classified incorrectly (wrong instrument, energy, or mood).

---

## How to invoke

Ask Auggie: `"Why is <filename> classified as <instrument> instead of <expected>?"`
Or run: `auggie workflow debug-classifier path=<file.wav>`

---

## Prompt template (for Auggie)

```
I have a WAV file at <path> that is being classified as <actual_result> but I expected <expected_result>.

Please:
1. Run: uv run samplemind analyze "<path>" --json
2. Show me ALL 9 raw feature values (rms, centroid_norm, zcr, flatness, rolloff_norm,
   onset_mean, onset_max, low_freq_ratio, duration) with their exact numeric values
3. Walk through each classifier rule for <actual_result> and <expected_result> — show
   whether each condition passed or failed with the actual value vs. threshold
4. Identify which specific condition is causing the wrong classification
5. Show me which threshold(s) I would need to adjust in classifier.py to fix it
6. If it's a test fixture, show me what numpy parameters to change in conftest.py
```

---

## Reference: Classifier Thresholds

### Energy (`classify_energy`)
| Value | Condition |
|-------|-----------|
| `low` | rms < 0.015 |
| `mid` | rms < 0.060 |
| `high` | rms ≥ 0.060 |

### Instrument (`classify_instrument`) — first match wins
| Result | Conditions |
|--------|-----------|
| `loop` | dur>2.0 AND onset_mean>0.8 |
| `hihat` | flat>0.2 AND zcr>0.1 AND rolloff>0.3 AND dur<1.0 |
| `kick` | lfr>0.35 AND onset_max>4.0 AND dur<0.8 AND zcr<0.08 |
| `snare` | onset_max>3.0 AND flat>0.05 AND dur<0.8 AND lfr<0.35 |
| `bass` | lfr>0.3 AND flat<0.05 AND dur>0.3 |
| `pad` | dur>1.5 AND onset_mean<1.5 AND centroid>0.08 |
| `lead` | centroid>0.15 AND flat<0.1 AND dur<3.0 |
| `sfx` | flat>0.1 |
| `unknown` | none matched |

### Mood (`classify_mood`) — first match wins
| Result | Conditions |
|--------|-----------|
| `aggressive` | zcr>0.08 AND onset_mean>3.0 AND centroid>0.15 |
| `dark` | centroid<0.12 AND minor_key |
| `melancholic` | minor_key AND rms<0.03 AND onset_mean<1.5 |
| `chill` | centroid<0.15 AND rms<0.05 AND onset_mean<2.0 |
| `euphoric` | major_key AND centroid>0.12 AND rms>0.02 |
| `neutral` | none matched |

---

## Fix locations
- Thresholds: `src/samplemind/analyzer/classifier.py` → `classify_energy()`, `classify_instrument()`, `classify_mood()`
- Test fixtures: `tests/conftest.py` → `kick_wav`, `hihat_wav`, `bass_wav`, etc.
- Feature extraction: `src/samplemind/analyzer/audio_analysis.py` → `analyze_file()`

