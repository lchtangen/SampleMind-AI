# Phase 2 Agent — Audio Analysis & Testing

Handles: librosa feature extraction, BPM detection, key detection, spectral analysis, WAV fixtures, pytest audio tests, LUFS, stereo analysis.

## Triggers
- Phase 2, librosa, audio_analysis.py, classifier.py, conftest.py, WAV fixture, LUFS, pyloudnorm, stereo, spectral, BPM detection, key detection

## Key Files
- `src/samplemind/analyzer/audio_analysis.py`
- `src/samplemind/analyzer/classifier.py`
- `src/samplemind/analyzer/loudness.py`
- `src/samplemind/analyzer/stereo.py`
- `tests/conftest.py`

## Canonical Patterns

```python
y, sr = librosa.load(path)                               # default sr=22050
rms = float(np.sqrt(np.mean(y ** 2)))                    # NOT librosa.feature.rms()
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_norm = float(centroid.mean()) / (sr / 2)        # normalized 0–1
zcr = float(librosa.feature.zero_crossing_rate(y).mean())
```

## Classifier Output Values

| Field | Valid values | ⚠ Never |
|-------|-------------|---------|
| `energy` | `"low"` `"mid"` `"high"` | `"medium"` |
| `mood` | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` | |
| `instrument` | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` | |

## Rules
1. Never commit real WAV files — always use synthetic fixtures
2. `@pytest.mark.slow` for tests > 1s
3. WAV fixtures use `soundfile.write()` with synthetic numpy arrays
4. LUFS uses pyloudnorm (ITU-R BS.1770-4)

