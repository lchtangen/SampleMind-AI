# Phase 2 — Audio Analysis & AI Classification

> Understand, test, and extend the audio analysis pipeline that extracts BPM, key, and 8 acoustic
> features from WAV files using librosa 0.11.

---

## Prerequisites

- Phase 1 complete (`uv sync --extra dev` works)
- Basic understanding of sound waves (frequency, amplitude) helpful but not required

---

## Goal State

- Full understanding of what `audio_analysis.py` and `classifier.py` do line by line
- All 8 audio features explained with acoustic intuition
- pytest tests for all `classify_*` functions
- Batch analysis with parallel processing

---

## 1. librosa 0.11.0 — Key Changes

librosa is the primary audio analysis library for Python. Version 0.11 contains changes you need
to know about:

| Change | librosa 0.10 | librosa 0.11 |
|--------|-------------|-------------|
| FFT backend | NumPy | **scipy** (more numerically stable) |
| Resampling default | `kaiser_best` (resampy) | **`soxr_hq`** (soxr) |
| `librosa.load()` | identical | now supports open file objects |
| `effects.deemphasis()` | modified input in-place | **non-destructive** |

For SampleMind this doesn't change behavior significantly, but be aware that scipy FFT produces
marginally different float values in tests.

---

## 2. The Analysis Pipeline — Step by Step

```
WAV file on disk
    │
    ▼
librosa.load(file_path)
    │  → y: numpy array of the sound wave (amplitude per sample)
    │  → sr: sample rate (e.g. 44100 samples/second)
    │
    ├──► analyze_bpm(y, sr)
    │       └─ librosa.beat.beat_track() → tempo in BPM
    │
    ├──► analyze_key(y, sr)
    │       ├─ chroma_cens() → 12 frequency bands (C through B)
    │       └─ tonnetz()     → major/minor determined here
    │
    └──► classify(y, sr, key)          ← classifier.py
            ├─ _features(y, sr, dur)   → dict of 8 values
            ├─ classify_energy(f)      → "low" | "mid" | "high"
            ├─ classify_mood(f, key)   → "dark" | "chill" | ...
            └─ classify_instrument(f)  → "kick" | "snare" | ...
```

---

## 3. The 8 Audio Features Explained

### 3.1 RMS — Root Mean Square (average loudness)

```python
# From classifier.py
rms = float(np.sqrt(np.mean(y ** 2)))
```

RMS is the physical definition of signal power. For 16-bit WAV files:
- `0.0` = complete silence
- `1.0` = maximum amplitude (hard clipping)
- Typical production samples: `0.01` – `0.15`

```
Threshold logic in classify_energy():
  rms < 0.015  → "low"   (quiet pads, atmospheric sounds)
  rms < 0.06   → "mid"   (normal melodic samples)
  rms >= 0.06  → "high"  (drums, strong bass hits)
```

### 3.2 Spectral Centroid — Centre of Gravity of Sound

```python
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_mean = float(centroid.mean()) / (sr / 2)  # normalised 0–1
```

Think of this as a "balance point" along the frequency axis:
- Low value (~0.05): warm, dark sound (bass, sub, dark pads)
- High value (~0.3+): bright, crispy sound (hi-hats, leads, synth arpeggios)

Dividing by `sr / 2` (Nyquist frequency) normalises to `0–1` regardless of sample rate.

### 3.3 Zero Crossing Rate (ZCR) — Noise Measure

```python
zcr = float(librosa.feature.zero_crossing_rate(y).mean())
```

Counts how often the waveform crosses the zero line per unit time:
- **Low ZCR** (0.01–0.03): tonal sounds — bass, pads, leads
- **High ZCR** (0.1+): noisy sounds — hi-hats, snares, white noise

A 440 Hz sine wave crosses zero 880 times per second (2× frequency). A hi-hat crosses thousands
of times per second because it contains countless frequency components.

### 3.4 Spectral Flatness — Tone vs Noise

```python
flatness = float(librosa.feature.spectral_flatness(y=y).mean())
```

Measures the ratio of geometric to arithmetic mean of the spectrum:
- `0.0`: pure sine wave (all energy at one frequency)
- `1.0`: white noise (equal energy across all frequencies)

```
Practical use in classify_instrument():
  flat > 0.2  → likely hi-hat/cymbal
  flat < 0.05 → tonal sound (bass, lead, pad)
```

### 3.5 Spectral Rolloff — High-Frequency Boundary

```python
rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
rolloff_norm = float(rolloff.mean()) / (sr / 2)
```

The frequency below which 85% of total energy resides, normalised to `0–1`.
- Kick/bass: low rolloff (~0.1) — most energy in bass
- Hi-hat/cymbal: high rolloff (~0.5+) — energy spread into bright frequencies

### 3.6 Onset Strength — Rhythmic Attack

```python
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
onset_mean = float(onset_env.mean())
onset_max  = float(onset_env.max())
```

`onset_strength` detects moments where the sound "starts" — transients. A kick drum hit has one
strong onset; a pad with slow attack has almost none.

- `onset_mean`: average attack strength over the whole sample
- `onset_max`: strongest single attack — used to identify powerful percussive one-shots

### 3.7 Low Frequency Ratio — Bass Content

```python
stft = np.abs(librosa.stft(y))                      # Spectrogram (frequency × time)
freqs = librosa.fft_frequencies(sr=sr)               # Frequency for each STFT row
low_mask = freqs < 300                               # Mask: True for frequencies below 300 Hz
low_energy = float(stft[low_mask].sum())
total_energy = float(stft.sum()) + 1e-8              # 1e-8 prevents division by zero
low_freq_ratio = low_energy / total_energy
```

STFT (Short-Time Fourier Transform) decomposes the audio signal into frequency components over
time. `low_freq_ratio` indicates what fraction of total energy is below 300 Hz:
- Kick: `0.4–0.7` (dominant bass)
- Hi-hat: `0.01–0.05` (almost no bass)
- Bass: `0.3–0.6`

### 3.8 Duration — Length

```python
duration = float(len(y)) / sr  # seconds
```

Simple calculation: number of samples divided by sample rate = seconds.
- One-shots (kick, snare, hi-hat): typically `0.1–1.0s`
- Loops: typically `2.0s+`
- Pads/leads: variable

---

## 4. Classification Decision Trees

### Energy Classification

```
RMS value
├── < 0.015  → "low"   (quiet, atmospheric samples)
├── < 0.060  → "mid"   (normal melodic samples)
└── >= 0.060 → "high"  (percussive, powerful samples)
```

### Mood Classification

```
ZCR > 0.08 AND onset_mean > 3.0 AND centroid > 0.15
    └→ "aggressive"  (noisy + rhythmic + bright = intense)

centroid < 0.12 AND minor_key
    └→ "dark"        (dark timbre + minor key)

minor_key AND rms < 0.03 AND onset_mean < 1.5
    └→ "melancholic" (minor + quiet + low rhythm)

centroid < 0.15 AND rms < 0.05 AND onset_mean < 2.0
    └→ "chill"       (calm, low energy, non-percussive)

NOT minor_key AND centroid > 0.12 AND rms > 0.02
    └→ "euphoric"    (major + bright + enough energy)

(none of the above)
    └→ "neutral"
```

### Instrument Classification (priority order)

```
dur > 2.0 AND onset_mean > 0.8
    └→ "loop"    (long file = almost always a loop)

flatness > 0.2 AND zcr > 0.1 AND rolloff > 0.3 AND dur < 1.0
    └→ "hihat"   (noisy + bright + short)

low_freq_ratio > 0.35 AND onset_max > 4.0 AND dur < 0.8 AND zcr < 0.08
    └→ "kick"    (dominant bass + strong attack + short + tonal)

onset_max > 3.0 AND flatness > 0.05 AND dur < 0.8 AND low_freq_ratio < 0.35
    └→ "snare"   (strong attack + some noise + short + not bass-dominated)

low_freq_ratio > 0.3 AND flatness < 0.05 AND dur > 0.3
    └→ "bass"    (heavy bass + tonal + not too short)

dur > 1.5 AND onset_mean < 1.5 AND centroid > 0.08
    └→ "pad"     (long + smooth + bright enough)

centroid > 0.15 AND flatness < 0.1 AND dur < 3.0
    └→ "lead"    (melodic + tonal + medium length)

flatness > 0.1
    └→ "sfx"     (flat spectrum = noise-type sound)

(none of the above)
    └→ "unknown"
```

---

## 5. Adding a New Feature — Spectral Bandwidth

Here is how to add a new feature without changing existing logic:

```python
# filename: src/samplemind/analyzer/classifier.py
# Add inside the _features() function:

# Spectral bandwidth — spread of frequencies around the centroid
# High value = wide, "rich" sound; low value = narrow, pure tone
bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
bandwidth_norm = float(bandwidth.mean()) / (sr / 2)

# Return in the features dict:
return {
    ...,
    "bandwidth_norm": bandwidth_norm,
}
```

---

## 6. Batch Analysis with Parallel Processing

For large sample libraries (1000+ files), serial analysis takes too long.
`ProcessPoolExecutor` lets us analyse multiple files simultaneously on different CPU cores:

```python
# filename: src/samplemind/analyzer/batch.py

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from samplemind.analyzer.audio_analysis import analyze_file


def analyze_batch(folder: Path, max_workers: int = 4) -> list[dict]:
    """
    Analyse all WAV files in a folder in parallel.

    max_workers: number of CPU cores to use (default: 4)
    Returns: list of analysis results (same format as analyze_file)
    """
    wav_files = list(folder.glob("**/*.wav"))

    results = []
    # ProcessPoolExecutor uses separate processes — bypasses Python GIL
    # ThreadPoolExecutor would be blocked by GIL for CPU-intensive code like librosa
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs — they run in parallel
        futures = {executor.submit(analyze_file, str(f)): f for f in wav_files}

        # Collect results as they complete
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                result = future.result()
                result["path"] = str(file_path)
                results.append(result)
            except Exception as e:
                print(f"Error analysing {file_path.name}: {e}", file=__import__("sys").stderr)

    return results
```

---

## 7. pytest — Test Setup

### conftest.py — shared fixtures

The actual `tests/conftest.py` defines these audio fixtures (never commit real audio files —
always generate them synthetically with `numpy` and `soundfile`):

```python
# filename: tests/conftest.py  (audio fixtures — excerpt)

import numpy as np
import pytest
import soundfile as sf
from pathlib import Path


@pytest.fixture
def silent_wav(tmp_path: Path) -> Path:
    """1-second silent WAV — tests that analyzer handles zero-energy audio without crashing.

    Expected: energy='low', low_freq_ratio≈0, no meaningful BPM/key estimate.
    """
    path = tmp_path / "test.wav"
    sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)
    return path


@pytest.fixture
def kick_wav(tmp_path: Path) -> Path:
    """Simulated kick: loud 60 Hz sine burst, 0.5 s.

    Characteristics: high amplitude (RMS≈0.64), very low centroid, low ZCR,
    low flatness, high low_freq_ratio.
    Expected classifier output: energy='high', instrument='kick', mood='dark'.
    """
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)
    path = tmp_path / "kick.wav"
    sf.write(str(path), samples, 22050)
    return path


@pytest.fixture
def hihat_wav(tmp_path: Path) -> Path:
    """Simulated hihat: white noise burst, 0.1 s (2205 samples at 22050 Hz).

    Characteristics: high ZCR (noise crosses zero constantly), high spectral
    centroid (energy spread across all frequencies), high flatness.
    Expected classifier output: instrument='hihat'.
    """
    rng = np.random.default_rng(seed=42)   # fixed seed for reproducibility
    samples = rng.uniform(-0.3, 0.3, 2205).astype(np.float32)
    path = tmp_path / "hihat.wav"
    sf.write(str(path), samples, 22050)
    return path
```

### test_classifier.py — unit tests

```python
# filename: tests/test_classifier.py

import pytest
from samplemind.analyzer.classifier import (
    classify_energy,
    classify_mood,
    classify_instrument,
)


class TestClassifyEnergy:
    def test_low_energy(self):
        """RMS below 0.015 should return 'low'."""
        assert classify_energy({"rms": 0.005}) == "low"

    def test_mid_energy(self):
        """RMS between 0.015 and 0.06 should return 'mid'."""
        assert classify_energy({"rms": 0.03}) == "mid"

    def test_high_energy(self):
        """RMS above 0.06 should return 'high'."""
        assert classify_energy({"rms": 0.10}) == "high"

    def test_boundary_low_mid(self):
        """Boundary value: exactly 0.015 should return 'mid' (not 'low')."""
        assert classify_energy({"rms": 0.015}) == "mid"


class TestClassifyMood:
    def test_aggressive(self):
        """High ZCR + strong onset + bright centroid = 'aggressive'."""
        f = {"zcr": 0.09, "onset_mean": 4.0, "centroid_norm": 0.20, "rms": 0.05}
        assert classify_mood(f, "C maj") == "aggressive"

    def test_dark_minor(self):
        """Dark centroid + minor key = 'dark'."""
        f = {"zcr": 0.02, "onset_mean": 1.0, "centroid_norm": 0.08, "rms": 0.05}
        assert classify_mood(f, "A min") == "dark"

    def test_euphoric_major(self):
        """Major key + bright centroid + enough energy = 'euphoric'."""
        f = {"zcr": 0.02, "onset_mean": 1.0, "centroid_norm": 0.15, "rms": 0.05}
        assert classify_mood(f, "C maj") == "euphoric"

    def test_melancholic(self):
        """Minor key + quiet + low rhythm = 'melancholic'."""
        f = {"zcr": 0.01, "onset_mean": 1.0, "centroid_norm": 0.10, "rms": 0.02}
        assert classify_mood(f, "F min") == "melancholic"


class TestClassifyInstrument:
    def test_kick(self, sample_features_kick):
        assert classify_instrument(sample_features_kick) == "kick"

    def test_hihat(self, sample_features_hihat):
        assert classify_instrument(sample_features_hihat) == "hihat"

    def test_loop_long_file(self):
        """A file longer than 2 seconds with strong onsets = 'loop'."""
        f = {"duration": 3.0, "onset_mean": 2.0, "low_freq_ratio": 0.2,
             "flatness": 0.05, "zcr": 0.03, "centroid_norm": 0.1,
             "onset_max": 3.0, "rolloff_norm": 0.2}
        assert classify_instrument(f) == "loop"
```

### test_audio_analysis.py — integration test

```python
# filename: tests/test_audio_analysis.py
# These tests use the fixtures defined in tests/conftest.py.

import pytest
from samplemind.analyzer.audio_analysis import analyze_file

# Valid classifier output sets — used in multiple tests below
VALID_ENERGY    = {"low", "mid", "high"}
VALID_MOOD      = {"dark", "chill", "aggressive", "euphoric", "melancholic", "neutral"}
VALID_INSTRUMENT = {"kick", "snare", "hihat", "bass", "pad", "lead", "loop", "sfx", "unknown"}


def test_analyze_file_sine(kick_wav):
    """A loud low-frequency sine wave should return sensible values.

    Uses the kick_wav fixture (60 Hz, 0.5 s) which has clear spectral properties.
    This is the canonical 'does the full pipeline work?' integration test.
    """
    result = analyze_file(str(kick_wav))

    # analyze_file() must return exactly these 5 keys
    assert set(result.keys()) == {"bpm", "key", "energy", "mood", "instrument"}

    # BPM must be a positive float (beat_track always returns a guess)
    assert isinstance(result["bpm"], float)
    assert result["bpm"] > 0

    # Each classifier output must be one of the valid enum strings
    assert result["energy"]     in VALID_ENERGY
    assert result["mood"]       in VALID_MOOD
    assert result["instrument"] in VALID_INSTRUMENT


def test_analyze_file_silence(silent_wav):
    """Silent audio must return 'low' energy and not raise an exception.

    This guards against division-by-zero errors in low_freq_ratio
    (protected by the 1e-8 epsilon in classifier._features()).
    """
    result = analyze_file(str(silent_wav))
    assert result["energy"] == "low"


@pytest.mark.slow
def test_analyze_real_wav(tmp_path):
    """
    Marked with @pytest.mark.slow — skip with: pytest -m 'not slow'
    Writes a 4-second 130 Hz sine wave (C2 — typical bass note) and
    checks that the instrument classifier picks something reasonable.
    """
    import soundfile as sf
    import numpy as np

    sr = 44100
    t = np.linspace(0, 4.0, sr * 4)
    y = (0.3 * np.sin(2 * np.pi * 130 * t)).astype(np.float32)
    path = tmp_path / "bass_test.wav"
    sf.write(str(path), y, sr)

    result = analyze_file(str(path))
    # A long low-frequency sample should be classified as bass, pad, lead, or loop
    assert result["instrument"] in {"bass", "pad", "lead", "loop", "unknown"}
```

---

## 8. Known Edge Cases and Limitations

| Problem | Cause | Solution |
|---------|-------|---------|
| Very short files (<512 samples) | `n_fft > len(y)` in librosa | Warnings suppressed with `filterwarnings` |
| Clipped audio | Waveform exceeds ±1.0 | RMS calculation gives erroneously high energy |
| Silent files | `total_energy ≈ 0` | `+ 1e-8` in `low_freq_ratio` prevents division by zero |
| Samples without clear BPM | Atmospheric pads, SFX | `beat_track()` always returns a guess — may be inaccurate |
| Polyphonic samples | Chord stabs, chord pads | `analyze_key()` finds dominant pitch, not full chord |

---

## Migration Notes

- No code changes in this phase — documentation and tests only
- Import paths update to `from samplemind.analyzer.audio_analysis import analyze_file` in Phase 4

---

## Testing Checklist

```bash
# Run all tests (skipping slow-marked ones)
$ uv run pytest tests/ -m "not slow" -v

# Run only classifier tests
$ uv run pytest tests/test_classifier.py -v

# Run slow tests explicitly (takes longer)
$ uv run pytest tests/ -m slow -v

# Check test coverage
$ uv run pytest --cov=samplemind.analyzer tests/
```

---

## Troubleshooting

**Error: `UserWarning: n_fft=2048 is too large`**
```python
# Already handled in classifier.py:
import warnings
warnings.filterwarnings("ignore", message="n_fft=.*is too large")
```

**Error: `audioread.NoBackendError`**
```bash
# librosa needs an audio backend for MP3/FLAC (WAV works without)
# WSL2: install ffmpeg
$ sudo apt install ffmpeg

# macOS:
$ brew install ffmpeg
```

**Error: Wrong BPM for samples without a clear beat**
```
This is a limitation of beat_track() — it always guesses a BPM.
For samples without a clear beat (pads, SFX) the BPM value will not be meaningful.
Consider filtering BPM display based on instrument type in the UI.
```

---

## 7. Advanced Analysis Features (2026)

### Audio Fingerprinting (`src/samplemind/analyzer/fingerprint.py`)

SHA-256 fingerprinting detects exact duplicate files before running expensive librosa analysis:

```python
# src/samplemind/analyzer/fingerprint.py
import hashlib
from pathlib import Path


def fingerprint_file(path: Path) -> str:
    """Compute SHA-256 of first 64KB — fast dedup detection.

    Reading only the first 64KB is a deliberate trade-off:
    - Fast enough to fingerprint 1000 files in under 1 second
    - Catches exact duplicates and most near-duplicates (same file, different path)
    - Does NOT catch re-encoded versions (different bitrate/format)
    """
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()


def find_duplicates(paths: list[Path]) -> dict[str, list[Path]]:
    """Group paths by fingerprint. Groups with len > 1 are duplicates.

    Returns only groups that have more than one file.
    """
    groups: dict[str, list[Path]] = {}
    for path in paths:
        fp = fingerprint_file(path)
        groups.setdefault(fp, []).append(path)
    return {fp: ps for fp, ps in groups.items() if len(ps) > 1}
```

CLI integration:
```bash
uv run samplemind duplicates               # list all duplicates
uv run samplemind duplicates --remove      # delete all but first occurrence
uv run samplemind analyze file.wav --fingerprint  # fingerprint + check library
```

### Batch Processing (`src/samplemind/analyzer/batch.py`)

Concurrent batch analysis using `ProcessPoolExecutor` — scales with available CPUs:

```python
# src/samplemind/analyzer/batch.py
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path
from typing import Callable

from samplemind.analyzer.audio_analysis import analyze_file


def analyze_batch(
    paths: list[Path],
    workers: int = 0,
    progress_cb: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """Analyze multiple files in parallel.

    Args:
        paths: List of audio file paths to analyze.
        workers: Number of worker processes. 0 = os.cpu_count().
        progress_cb: Optional callback(completed, total) for progress reporting.

    Returns:
        List of analysis result dicts, in input order.
    """
    workers = workers or os.cpu_count() or 1
    results: list[dict] = [{}] * len(paths)

    with ProcessPoolExecutor(max_workers=workers) as pool:
        future_to_idx = {pool.submit(analyze_file, p): i for i, p in enumerate(paths)}
        completed = 0
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = {"error": str(e), "path": str(paths[idx])}
            completed += 1
            if progress_cb:
                progress_cb(completed, len(paths))

    return results
```

### Coverage Configuration

Add to `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["samplemind"]
omit = ["*/tests/*", "*/__pycache__/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 70
show_missing = true
skip_covered = false

[tool.coverage.html]
directory = "htmlcov"
```

Run with coverage:
```bash
uv run pytest tests/ --cov=samplemind --cov-report=term-missing
uv run pytest tests/ --cov=samplemind --cov-report=html  # htmlcov/index.html
```

### Audio Test Fixtures in conftest.py

All three audio fixtures below are already defined in `tests/conftest.py` and available to every
test without any extra imports. Use them directly as function parameters:

```python
# tests/conftest.py  (audio fixtures — full definitions)

@pytest.fixture
def silent_wav(tmp_path: Path) -> Path:
    """1-second silence at 22050 Hz — baseline zero-energy test."""
    path = tmp_path / "test.wav"
    sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)
    return path


@pytest.fixture
def kick_wav(tmp_path: Path) -> Path:
    """Simulated kick: high amplitude, 60 Hz sine burst, 0.5 s.

    Why 60 Hz: Nyquist is 11025 Hz at sr=22050. Most kick drum energy lives
    below 200 Hz. A 60 Hz sine gives a very clear low_freq_ratio > 0.35 so
    the classifier reliably returns instrument='kick'.
    """
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)
    path = tmp_path / "kick.wav"
    sf.write(str(path), samples, 22050)
    return path


@pytest.fixture
def hihat_wav(tmp_path: Path) -> Path:
    """Simulated hihat: white noise, 0.1 s (2205 samples), seeded RNG.

    Using a fixed seed (42) keeps the test deterministic across machines and
    Python versions, so the expected instrument='hihat' assertion is stable.
    """
    rng = np.random.default_rng(seed=42)
    samples = rng.uniform(-0.3, 0.3, 2205).astype(np.float32)
    path = tmp_path / "hihat.wav"
    sf.write(str(path), samples, 22050)
    return path
```

To add a **bass** or **batch** fixture for your own extension tests:

```python
@pytest.fixture
def bass_wav(tmp_path: Path) -> Path:
    """Simulated bass: 80 Hz sine, 2 s, medium amplitude.
    Expected: high low_freq_ratio, instrument='bass' or 'pad'.
    """
    t = np.linspace(0, 2.0, int(22050 * 2.0), dtype=np.float32)
    samples = (0.5 * np.sin(2 * np.pi * 80 * t)).astype(np.float32)
    path = tmp_path / "bass.wav"
    sf.write(str(path), samples, 22050)
    return path


@pytest.fixture
def batch_wav_dir(tmp_path: Path) -> Path:
    """Directory with 5 synthetic WAV files for batch processing tests.

    Frequencies span sub-bass to treble so the 5 files get different
    classifier labels, making it easy to verify batch result diversity.
    """
    for i, freq in enumerate([60, 80, 200, 1000, 5000]):
        t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
        samples = (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
        sf.write(str(tmp_path / f"sample_{i:02d}.wav"), samples, 22050)
    return tmp_path
```

