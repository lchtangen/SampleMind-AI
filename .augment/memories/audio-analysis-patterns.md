# Memory: Audio Analysis Patterns

Canonical librosa patterns for feature extraction in `src/samplemind/analyzer/`.
Always use these exact patterns — deviations will produce wrong classifier results.

## Feature Extraction (audio_analysis.py)

```python
y, sr = librosa.load(path)                              # default sr=22050, soxr_hq resampling
rms = float(np.sqrt(np.mean(y ** 2)))                   # ⚠ NOT librosa.feature.rms()
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_norm = float(centroid.mean()) / (sr / 2)       # normalized to 0–1
zcr = float(librosa.feature.zero_crossing_rate(y).mean())
flatness = float(librosa.feature.spectral_flatness(y=y).mean())
rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
rolloff_norm = float(rolloff.mean()) / (sr / 2)
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
onset_mean = float(onset_env.mean())
onset_max = float(onset_env.max())
low_freq_ratio = float(np.mean(np.abs(librosa.stft(y)[:int(300*len(y)/sr), :])))
duration = float(len(y) / sr)
bpm, _ = librosa.beat.beat_track(y=y, sr=sr)
```

## Audio Fingerprinting (fingerprint.py)

SHA-256 of first 64 KB — used for deduplication on import:

```python
def fingerprint_file(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()
```

## WAV Fixture Patterns (tests/conftest.py)

Never commit real audio. Use these synthetic patterns:

```python
# Silent WAV
sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)

# Kick (high amplitude, low frequency, short)
t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)

# Hihat (white noise, short)
samples = np.random.uniform(-0.3, 0.3, 2205).astype(np.float32)  # 0.1s
```

## Key librosa Conventions

- Always use `sr=22050` (default) — do not pass a different sample rate unless testing
- Use `soxr_hq` resampler (librosa default from v0.10+)
- `bpm` from `beat_track` is a numpy scalar — always cast to `float()`
- All feature values stored in DB as `Float` (SQLModel) — never as `int`

