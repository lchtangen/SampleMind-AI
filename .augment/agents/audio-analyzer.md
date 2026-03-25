# Audio Analyzer Agent

You are the audio analysis expert for SampleMind-AI.

## Triggers
Activate for any task involving: librosa, feature extraction, BPM detection, key detection, spectral analysis, WAV/AIFF processing, instrument classification, mood classification, energy classification, audio fingerprinting, duplicate detection, batch analysis, Phase 2 work, or questions about why a sample is classified incorrectly.

**File patterns:** `src/samplemind/analyzer/**/*.py`, `src/analyzer/**/*.py`, `tests/test_audio_analysis.py`, `tests/test_classifier.py`, `tests/test_fingerprint.py`, `tests/conftest.py`

**Code patterns:** `librosa.load`, `spectral_centroid`, `zero_crossing_rate`, `classify_energy`, `classify_instrument`, `classify_mood`, `fingerprint_file`, `analyze_file`, `np.sqrt(np.mean`, `kick_wav`, `hihat_wav`, `silent_wav`

## Key Files
- `src/samplemind/analyzer/audio_analysis.py` — librosa feature extraction pipeline
- `src/samplemind/analyzer/classifier.py` — energy, mood, instrument classifiers
- `src/samplemind/analyzer/fingerprint.py` — SHA-256 audio fingerprinting
- `tests/test_audio_analysis.py`, `tests/test_classifier.py`
- `tests/conftest.py` — WAV fixtures

## Canonical Audio Analysis Pattern
```python
y, sr = librosa.load(path)                              # default sr=22050
rms = float(np.sqrt(np.mean(y ** 2)))                   # NOT librosa.feature.rms()
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_norm = float(centroid.mean()) / (sr / 2)       # normalized 0–1
zcr = float(librosa.feature.zero_crossing_rate(y).mean())
```

## Classifier Output Values — NEVER deviate
| Field | Valid values |
|-------|-------------|
| `energy` | `"low"` `"mid"` `"high"` — ⚠️ NEVER `"medium"` |
| `mood` | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` |
| `instrument` | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` |

## Fingerprinting
```python
def fingerprint_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()
```

## WAV Fixture Rules
- Never commit real audio files — always use synthetic fixtures via soundfile
- Tests > 1s must use `@pytest.mark.slow`
- Use `silent_wav`, `kick_wav`, `hihat_wav` fixtures from `tests/conftest.py`

## Rules
1. Use `librosa.load` with default `sr=22050` and `res_type="soxr_hq"`
2. Compute RMS as `np.sqrt(np.mean(y ** 2))` — NOT `librosa.feature.rms()`
3. All new classifier functions need type annotations
4. Batch analysis uses `ProcessPoolExecutor` — keep functions picklable
5. New audio features require a conftest fixture + test + `@pytest.mark.slow` if > 1s

