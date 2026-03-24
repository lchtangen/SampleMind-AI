# Fase 2 — Lydanalyse og AI-klassifisering

> Forstå, test og utvid lydanalyse-pipelinen som trekker ut BPM, toneart og 8 akustiske features
> fra WAV-filer ved hjelp av librosa 0.11.

---

## Forutsetninger

- Fase 1 fullført (`uv sync --extra dev` fungerer)
- Grunnleggende forståelse av lydbølger (frekvens, amplitude) er nyttig men ikke påkrevd

---

## Mål etter denne fasen

- Full forståelse av hva `audio_analysis.py` og `classifier.py` gjør linje for linje
- Alle 8 lydfeatures forklart med akustisk intuisjon
- pytest-tester for alle `classify_*`-funksjoner
- Batch-analyse med parallell prosessering

---

## 1. librosa 0.11.0 — Viktige endringer

librosa er det viktigste biblioteket for lydanalyse i Python. Versjon 0.11 inneholder noen
endringer du må kjenne til:

| Endring | librosa 0.10 | librosa 0.11 |
|---------|-------------|-------------|
| FFT-backend | NumPy | **scipy** (mer numerisk stabilt) |
| Resampling-standard | `kaiser_best` (resampy) | **`soxr_hq`** (soxr) |
| `librosa.load()` | identisk | støtter nå åpne fil-objekter |
| `effects.deemphasis()` | modifiserte input in-place | **ikke-destruktiv** |

For SampleMind endrer ikke dette oppførselen vesentlig, men det er greit å vite at scipy-FFT gir
marginalt ulike floatverdier i tester.

---

## 2. Analysepipelinen — steg for steg

```
WAV-fil på disk
    │
    ▼
librosa.load(file_path)
    │  → y: numpy array av lydbølgen (amplitude per sample)
    │  → sr: sample rate (f.eks. 44100 samples/sekund)
    │
    ├──► analyze_bpm(y, sr)
    │       └─ librosa.beat.beat_track() → tempo i BPM
    │
    ├──► analyze_key(y, sr)
    │       ├─ chroma_cens() → 12 frekvensband (C til B)
    │       └─ tonnetz()     → major/minor bestemmes her
    │
    └──► classify(y, sr, key)          ← classifier.py
            ├─ _features(y, sr, dur)   → dict med 8 verdier
            ├─ classify_energy(f)      → "low" | "mid" | "high"
            ├─ classify_mood(f, key)   → "dark" | "chill" | ...
            └─ classify_instrument(f)  → "kick" | "snare" | ...
```

---

## 3. De 8 lydfeaturene forklart

### 3.1 RMS — Root Mean Square (gjennomsnittlig lydstyrke)

```python
# Fra classifier.py
rms = float(np.sqrt(np.mean(y ** 2)))
```

RMS er den fysiske definisjonen på signalstyrke. For 16-bit WAV-filer:
- `0.0` = fullstendig stillhet
- `1.0` = maksimal amplitude (hard clipping)
- Typiske produksjonssaples: `0.01` – `0.15`

```
Terskel-logikk i classify_energy():
  rms < 0.015  → "low"   (stille pads, atmosfæriske sounds)
  rms < 0.06   → "mid"   (normale melodiske samples)
  rms >= 0.06  → "high"  (trommer, sterke bass-hits)
```

### 3.2 Spectral Centroid — Lysets tyngdepunkt

```python
centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
centroid_mean = float(centroid.mean()) / (sr / 2)  # normalisert 0–1
```

Tenk på dette som en "balansevekt" langs frekvensakselen:
- Lav verdi (~0.05): varmt, mørkt sound (bass, sub, mørke pads)
- Høy verdi (~0.3+): lyst, crispy sound (hihats, leads, synth-arpeggioer)

Divisjon med `sr / 2` (Nyquist-frekvens) normaliserer til `0–1` uavhengig av sample rate.

### 3.3 Zero Crossing Rate (ZCR) — Støymål

```python
zcr = float(librosa.feature.zero_crossing_rate(y).mean())
```

Teller hvor ofte lydbølgen krysser null-linjen per tidsenhet:
- **Lav ZCR** (0.01–0.03): tonale lyder — bass, pads, leads
- **Høy ZCR** (0.1+): støyrike lyder — hihats, snarer, hvit støy

En sinus-bølge på 440 Hz krysser null 880 ganger per sekund (2× frekvens). En hihat krysser
thousends of times per second fordi den inneholder utallige frekvenskomponenter.

### 3.4 Spectral Flatness — Tone vs Støy

```python
flatness = float(librosa.feature.spectral_flatness(y=y).mean())
```

Måler forholdet mellom geometrisk og aritmetisk gjennomsnitt av spekteret:
- `0.0`: ren sinusbølge (all energi på én frekvens)
- `1.0`: hvit støy (jevn energi på alle frekvenser)

```
Praktisk bruk i classify_instrument():
  flat > 0.2  → sannsynlig hihat/cymbal
  flat < 0.05 → tonal lyd (bass, lead, pad)
```

### 3.5 Spectral Rolloff — Høyfrekvensgrense

```python
rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
rolloff_norm = float(rolloff.mean()) / (sr / 2)
```

Frekvensen under hvilken 85% av den totale energien befinner seg, normalisert til `0–1`.
- Kick/bass: lav rolloff (~0.1) — det meste av energien er i bass
- Hihat/cymbal: høy rolloff (~0.5+) — energi spredt opp i de lyse frekvensene

### 3.6 Onset Strength — Rytmisk anslag

```python
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
onset_mean = float(onset_env.mean())
onset_max  = float(onset_env.max())
```

`onset_strength` oppdager øyeblikk der lyden "starter" — transients. Et kick-trommeslag har ett
kraftig onset; en pad med slow attack har nesten ingen.

- `onset_mean`: gjennomsnittlig anslagsstyrke over hele sampelet
- `onset_max`: sterkeste enkeltanslag — brukes til å identifisere kraftige perkussive one-shots

### 3.7 Low Frequency Ratio — Bassinnhold

```python
stft = np.abs(librosa.stft(y))                      # Spektrogram (frekvens × tid)
freqs = librosa.fft_frequencies(sr=sr)               # Frekvens for hver STFT-rad
low_mask = freqs < 300                               # Maske: True for frekvenser under 300 Hz
low_energy = float(stft[low_mask].sum())
total_energy = float(stft.sum()) + 1e-8              # 1e-8 for å unngå divisjon på null
low_freq_ratio = low_energy / total_energy
```

STFT (Short-Time Fourier Transform) deler lydsignalet i frekvenskomponenter over tid.
`low_freq_ratio` angir hvor mye av total energi som er under 300 Hz:
- Kick: `0.4–0.7` (dominerende bass)
- Hihat: `0.01–0.05` (nesten ingen bass)
- Bass: `0.3–0.6`

### 3.8 Duration — Lengde

```python
duration = float(len(y)) / sr  # sekunder
```

Enkel beregning: antall samples delt på sample rate = sekunder.
- One-shots (kick, snare, hihat): typisk `0.1–1.0s`
- Loops: typisk `2.0s+`
- Pads/leads: varierende

---

## 4. Beslutningstrær for klassifisering

### Energy-klassifisering

```
RMS-verdi
├── < 0.015  → "low"   (stille, atmosfæriske samples)
├── < 0.060  → "mid"   (normale melodiske samples)
└── >= 0.060 → "high"  (perkussive, kraftige samples)
```

### Mood-klassifisering

```
ZCR > 0.08 AND onset_mean > 3.0 AND centroid > 0.15
    └→ "aggressive"  (støyrik + rytmisk + lys = intens)

centroid < 0.12 AND minor_key
    └→ "dark"        (mørk klang + molltoneart)

minor_key AND rms < 0.03 AND onset_mean < 1.5
    └→ "melancholic" (moll + stille + lite rytmikk)

centroid < 0.15 AND rms < 0.05 AND onset_mean < 2.0
    └→ "chill"       (rolig, lav energi, ikke-perkussiv)

NOT minor_key AND centroid > 0.12 AND rms > 0.02
    └→ "euphoric"    (dur + lys + nok energi)

(ingen av de over)
    └→ "neutral"
```

### Instrument-klassifisering (prioritetsrekkefølge)

```
dur > 2.0 AND onset_mean > 0.8
    └→ "loop"    (lang fil = nesten alltid en loop)

flatness > 0.2 AND zcr > 0.1 AND rolloff > 0.3 AND dur < 1.0
    └→ "hihat"   (støyrik + lys + kort)

low_freq_ratio > 0.35 AND onset_max > 4.0 AND dur < 0.8 AND zcr < 0.08
    └→ "kick"    (dominerende bass + kraftig anslag + kort + tonal)

onset_max > 3.0 AND flatness > 0.05 AND dur < 0.8 AND low_freq_ratio < 0.35
    └→ "snare"   (kraftig anslag + litt støy + kort + ikke bass-dominert)

low_freq_ratio > 0.3 AND flatness < 0.05 AND dur > 0.3
    └→ "bass"    (tung bass + tonal + ikke for kort)

dur > 1.5 AND onset_mean < 1.5 AND centroid > 0.08
    └→ "pad"     (lang + jevn + lys nok)

centroid > 0.15 AND flatness < 0.1 AND dur < 3.0
    └→ "lead"    (melodisk + tonal + middels lang)

flatness > 0.1
    └→ "sfx"     (flat spektrum = støylyd)

(ingen av de over)
    └→ "unknown"
```

---

## 5. Legg til en ny feature — Spectral Bandwidth

Slik legger du til en ny feature uten å endre eksisterende logikk:

```python
# filename: src/samplemind/analyzer/classifier.py
# Legg til i _features()-funksjonen:

# Spectral bandwidth — spredning av frekvenser rundt centroid
# Høy verdi = bredt, "rikt" lydbilde; lav verdi = smal, ren tone
bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
bandwidth_norm = float(bandwidth.mean()) / (sr / 2)

# Returner i features-dicten:
return {
    ...,
    "bandwidth_norm": bandwidth_norm,
}
```

---

## 6. Batch-analyse med parallell prosessering

For store sample-biblioteker (1000+ filer) tar seriell analyse for lang tid.
`ProcessPoolExecutor` lar oss analysere flere filer samtidig på ulike CPU-kjerner:

```python
# filename: src/samplemind/analyzer/batch.py

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from samplemind.analyzer.audio_analysis import analyze_file


def analyze_batch(folder: Path, max_workers: int = 4) -> list[dict]:
    """
    Analyser alle WAV-filer i en mappe parallelt.

    max_workers: antall CPU-kjerner å bruke (standard: 4)
    Returnerer: liste med analyse-resultater (samme format som analyze_file)
    """
    wav_files = list(folder.glob("**/*.wav"))

    results = []
    # ProcessPoolExecutor bruker separate prosesser — unngår Python GIL-begrensningen
    # ThreadPoolExecutor ville vært blokkert av GIL for CPU-intensiv kode som librosa
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit alle jobber — de kjøres parallelt
        futures = {executor.submit(analyze_file, str(f)): f for f in wav_files}

        # Samle resultater etter hvert som de ferdigstilles
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                result = future.result()
                result["path"] = str(file_path)
                results.append(result)
            except Exception as e:
                print(f"Feil ved analyse av {file_path.name}: {e}", file=__import__("sys").stderr)

    return results
```

---

## 7. pytest — Testoppsett

### conftest.py — delte fixtures

```python
# filename: tests/conftest.py

import numpy as np
import pytest
import soundfile as sf
import tempfile
from pathlib import Path


@pytest.fixture
def silence_wav(tmp_path: Path) -> Path:
    """Lager en 1-sekunds stille WAV-fil for testing."""
    y = np.zeros(22050, dtype=np.float32)
    path = tmp_path / "silence.wav"
    sf.write(str(path), y, 22050)
    return path


@pytest.fixture
def sine_wav(tmp_path: Path) -> Path:
    """Lager en 1-sekunds 440 Hz sinusbølge (ren tone, A4)."""
    sr = 22050
    t = np.linspace(0, 1.0, sr, endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    path = tmp_path / "sine_440.wav"
    sf.write(str(path), y, sr)
    return path


@pytest.fixture
def noise_wav(tmp_path: Path) -> Path:
    """Lager en 0.3-sekunds hvit støy WAV (simulerer hihat)."""
    rng = np.random.default_rng(42)   # Fast seed for reproduserbarhet
    y = rng.uniform(-0.3, 0.3, 6615).astype(np.float32)
    path = tmp_path / "noise.wav"
    sf.write(str(path), y, 22050)
    return path


@pytest.fixture
def sample_features_kick() -> dict:
    """Feature-dict som representerer en typisk kick-tromme."""
    return {
        "rms": 0.10,           # Høy — kraftig kick
        "centroid_norm": 0.08, # Lav — mørkt/bass-dominert
        "zcr": 0.03,           # Lav — tonal (ikke støy)
        "flatness": 0.02,      # Lav — ikke-støyrig (ren bass-tone)
        "rolloff_norm": 0.12,  # Lav — energi i bass
        "onset_mean": 2.5,
        "onset_max": 6.0,      # Høy — kraftig enkelt-anslag
        "low_freq_ratio": 0.50,# Høy — bass-dominert
        "duration": 0.4,       # Kort one-shot
    }


@pytest.fixture
def sample_features_hihat() -> dict:
    """Feature-dict som representerer en typisk hihat."""
    return {
        "rms": 0.04,
        "centroid_norm": 0.40,  # Høy — lyst sound
        "zcr": 0.15,            # Høy — støyrik
        "flatness": 0.35,       # Høy — hvit støy-aktig
        "rolloff_norm": 0.55,   # Høy — mye energi i diskant
        "onset_mean": 3.0,
        "onset_max": 5.0,
        "low_freq_ratio": 0.03, # Lav — nesten ingen bass
        "duration": 0.2,        # Veldig kort
    }
```

### test_classifier.py — enhetstester

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
        """RMS under 0.015 skal gi 'low'."""
        assert classify_energy({"rms": 0.005}) == "low"

    def test_mid_energy(self):
        """RMS mellom 0.015 og 0.06 skal gi 'mid'."""
        assert classify_energy({"rms": 0.03}) == "mid"

    def test_high_energy(self):
        """RMS over 0.06 skal gi 'high'."""
        assert classify_energy({"rms": 0.10}) == "high"

    def test_boundary_low_mid(self):
        """Grenseverdi: nøyaktig 0.015 skal gi 'mid' (ikke 'low')."""
        assert classify_energy({"rms": 0.015}) == "mid"


class TestClassifyMood:
    def test_aggressive(self):
        """Høy ZCR + sterk onset + lys sentroid = 'aggressive'."""
        f = {"zcr": 0.09, "onset_mean": 4.0, "centroid_norm": 0.20, "rms": 0.05}
        assert classify_mood(f, "C maj") == "aggressive"

    def test_dark_minor(self):
        """Mørk sentroid + molltoneart = 'dark'."""
        f = {"zcr": 0.02, "onset_mean": 1.0, "centroid_norm": 0.08, "rms": 0.05}
        assert classify_mood(f, "A min") == "dark"

    def test_euphoric_major(self):
        """Durtoneart + lys sentroid + nok energi = 'euphoric'."""
        f = {"zcr": 0.02, "onset_mean": 1.0, "centroid_norm": 0.15, "rms": 0.05}
        assert classify_mood(f, "C maj") == "euphoric"

    def test_melancholic(self):
        """Molltoneart + stille + lav rytmikk = 'melancholic'."""
        f = {"zcr": 0.01, "onset_mean": 1.0, "centroid_norm": 0.10, "rms": 0.02}
        assert classify_mood(f, "F min") == "melancholic"


class TestClassifyInstrument:
    def test_kick(self, sample_features_kick):
        assert classify_instrument(sample_features_kick) == "kick"

    def test_hihat(self, sample_features_hihat):
        assert classify_instrument(sample_features_hihat) == "hihat"

    def test_loop_long_file(self):
        """En fil lengre enn 2 sekunder med sterke onsets = 'loop'."""
        f = {"duration": 3.0, "onset_mean": 2.0, "low_freq_ratio": 0.2,
             "flatness": 0.05, "zcr": 0.03, "centroid_norm": 0.1,
             "onset_max": 3.0, "rolloff_norm": 0.2}
        assert classify_instrument(f) == "loop"
```

### test_audio_analysis.py — integrasjonstest

```python
# filename: tests/test_audio_analysis.py

import pytest
from samplemind.analyzer.audio_analysis import analyze_file


def test_analyze_sine_wave(sine_wav):
    """En ren sinusbølge skal gi fornuftige verdier fra full analyse."""
    result = analyze_file(str(sine_wav))

    # Alle nøkler skal finnes
    assert set(result.keys()) == {"bpm", "key", "energy", "mood", "instrument"}

    # Verdiene skal være gyldige strenger/tall
    assert isinstance(result["bpm"], float)
    assert result["bpm"] > 0

    assert result["energy"] in {"low", "mid", "high"}
    assert result["mood"] in {"dark", "chill", "aggressive", "euphoric", "melancholic", "neutral"}
    assert result["instrument"] in {"kick","snare","hihat","bass","pad","lead","loop","sfx","unknown"}


def test_analyze_silence(silence_wav):
    """Stille lyd skal gi 'low' energi og ikke krasje."""
    result = analyze_file(str(silence_wav))
    assert result["energy"] == "low"


@pytest.mark.slow
def test_analyze_real_wav(tmp_path):
    """
    Marker med @pytest.mark.slow — hopp over med: pytest -m 'not slow'
    Krever en faktisk WAV-fil på disk.
    """
    import soundfile as sf
    import numpy as np
    # Lag en mer realistisk test-fil (4 sekunder, stereo-ish)
    sr = 44100
    t = np.linspace(0, 4.0, sr * 4)
    y = (0.3 * np.sin(2 * np.pi * 130 * t)).astype(np.float32)  # Bass-lignende tone
    path = tmp_path / "bass_test.wav"
    sf.write(str(path), y, sr)

    result = analyze_file(str(path))
    assert result["instrument"] in {"bass", "pad", "lead", "loop", "unknown"}
```

---

## 8. Kjente edge cases og begrensninger

| Problem | Årsak | Løsning |
|---------|-------|---------|
| Veldig korte filer (<512 samples) | `n_fft > len(y)` i librosa | Warnings undertrykkes med `filterwarnings` |
| Klippet audio (clipping) | Waveform overstiger ±1.0 | RMS-beregning gir feilaktig høy energi |
| Stille filer | `total_energy ≈ 0` | `+ 1e-8` i `low_freq_ratio` forhindrer divisjon på null |
| Samples uten klar BPM | Atmosfæriske pads, SFX | `beat_track()` returnerer en gjetting — kan være unøyaktig |
| Polyfoniske samples | Chord-stabs, akkordpad | `analyze_key()` finner dominant tonehøyde, ikke full akkord |

---

## Migrasjonsnotater

- Ingen kodeendringer i denne fasen — kun dokumentasjon og tester
- Importstier endres til `from samplemind.analyzer.audio_analysis import analyze_file` i Fase 4

---

## Testsjekkliste

```bash
# Kjør alle tester (hopper over slow-markerte)
$ uv run pytest tests/ -m "not slow" -v

# Kjør kun classifier-tester
$ uv run pytest tests/test_classifier.py -v

# Kjør slow-tester eksplisitt (tar lengre tid)
$ uv run pytest tests/ -m slow -v

# Sjekk test-dekning
$ uv run pytest --cov=samplemind.analyzer tests/
```

---

## Feilsøking

**Feil: `UserWarning: n_fft=2048 is too large`**
```python
# Allerede håndtert i classifier.py:
import warnings
warnings.filterwarnings("ignore", message="n_fft=.*is too large")
```

**Feil: `audioread.NoBackendError`**
```bash
# librosa trenger en audio-backend for MP3/FLAC (WAV fungerer uten)
# WSL2: installer ffmpeg
$ sudo apt install ffmpeg

# macOS:
$ brew install ffmpeg
```

**Feil: Feil BPM for samples uten klar beat**
```
Dette er en begrensning ved beat_track() — den gjetter alltid en BPM.
For samples uten tydelig beat (pads, SFX) vil BPM-verdien ikke være meningsfull.
Vurder å filtrere BPM-visning basert på instrument-type i UI.
```
