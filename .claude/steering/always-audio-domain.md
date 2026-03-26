---
type: always
---

## Audio Domain Rules — Always Active

### Classifier Output Values (exact strings — stored in DB, never change)

| Field      | Valid values |
|------------|-------------|
| energy     | `"low"` `"mid"` `"high"` — **NEVER `"medium"`** |
| mood       | `"dark"` `"chill"` `"aggressive"` `"euphoric"` `"melancholic"` `"neutral"` |
| instrument | `"loop"` `"hihat"` `"kick"` `"snare"` `"bass"` `"pad"` `"lead"` `"sfx"` `"unknown"` |

### IPC Contract (stdout/stderr split — critical for Tauri integration)

- JSON for machine consumption → **stdout ONLY**
- Human-readable output → **stderr** (or Rich Progress to stderr)
- Never mix: Tauri/Rust reads stdout with `serde_json::from_slice` — mixed output breaks silently

### Canonical Audio Analysis Pattern

```python
y, sr = librosa.load(path)                              # default sr=22050, soxr_hq resampling
rms = float(np.sqrt(np.mean(y ** 2)))                   # NOT librosa.feature.rms()
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_norm = float(centroid.mean()) / (sr / 2)       # normalized to 0–1
zcr = float(librosa.feature.zero_crossing_rate(y).mean())
```

### BPM Extraction (handles any array shape from librosa)

```python
tempo_arr = np.asarray(tempo).ravel()
bpm_val = float(tempo_arr[0]) if tempo_arr.size > 0 else 0.0
```

### FL Studio Sample Paths (reference)

- macOS FL Studio 20: `~/Documents/Image-Line/FL Studio/Data/Patches/Samples/SampleMind/`
- macOS FL Studio 21: `~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind/`
- Windows: `C:\Users\<name>\Documents\Image-Line\FL Studio\Data\Patches\Samples\SampleMind\`
