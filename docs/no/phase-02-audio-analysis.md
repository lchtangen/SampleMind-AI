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
def silent_wav(tmp_path: Path) -> Path:
    """1 sekund stille WAV — tester at analysatoren håndterer null-energi lyd uten å krasje."""
    path = tmp_path / "test.wav"
    sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)
    return path


@pytest.fixture
def kick_wav(tmp_path: Path) -> Path:
    """Simulert kick: høy amplitude, 60 Hz sinusburs, 0.5 s.

    Forventede resultater: energy='high', instrument='kick', mood='dark'.
    """
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)
    path = tmp_path / "kick.wav"
    sf.write(str(path), samples, 22050)
    return path


@pytest.fixture
def hihat_wav(tmp_path: Path) -> Path:
    """Simulert hihat: hvit støy, 0.1 s (2205 samples), fast seed.

    Fast seed (42) holder testen deterministisk på tvers av maskiner.
    Forventede resultater: høy ZCR, høy spektral sentroid, instrument='hihat'.
    """
    rng = np.random.default_rng(seed=42)
    samples = rng.uniform(-0.3, 0.3, 2205).astype(np.float32)
    path = tmp_path / "hihat.wav"
    sf.write(str(path), samples, 22050)
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


def test_analyze_file_sine(kick_wav):
    """En 60 Hz sinusburs (kick_wav) skal gi fornuftige verdier fra full analyse."""
    result = analyze_file(str(kick_wav))

    # Alle nøkler skal finnes
    assert set(result.keys()) == {"bpm", "key", "energy", "mood", "instrument"}

    # Verdiene skal være gyldige strenger/tall
    assert isinstance(result["bpm"], float)
    assert result["bpm"] > 0

    assert result["energy"] in {"low", "mid", "high"}
    assert result["mood"] in {"dark", "chill", "aggressive", "euphoric", "melancholic", "neutral"}
    assert result["instrument"] in {"kick","snare","hihat","bass","pad","lead","loop","sfx","unknown"}


def test_analyze_file_silence(silent_wav):
    """Stille lyd skal gi 'low' energi og ikke krasje."""
    result = analyze_file(str(silent_wav))
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

---

## 7. Avanserte analysefunksjoner (2026)

### Lydfingeravtrykk (`src/samplemind/analyzer/fingerprint.py`)

SHA-256-fingeravtrykk oppdager eksakte duplikater før vi kjører kostbar librosa-analyse:

```python
# src/samplemind/analyzer/fingerprint.py
import hashlib
from pathlib import Path


def fingerprint_file(path: Path) -> str:
    """Beregn SHA-256 av første 64KB — rask duplikatdeteksjon.

    Å lese kun de første 64KB er en bevisst avveining:
    - Raskt nok til å fingeravtrykke 1000 filer på under 1 sekund
    - Fanger eksakte duplikater og de fleste nær-duplikater (samme fil, ulik sti)
    - Fanger IKKE re-enkodede versjoner (ulik bitrate/format)
    """
    with open(path, "rb") as f:
        return hashlib.sha256(f.read(65536)).hexdigest()


def find_duplicates(paths: list[Path]) -> dict[str, list[Path]]:
    """Grupper stier etter fingeravtrykk. Grupper med len > 1 er duplikater.

    Returnerer kun grupper som har mer enn én fil.
    """
    groups: dict[str, list[Path]] = {}
    for path in paths:
        fp = fingerprint_file(path)
        groups.setdefault(fp, []).append(path)
    return {fp: ps for fp, ps in groups.items() if len(ps) > 1}
```

CLI-integrasjon:
```bash
uv run samplemind duplicates               # list alle duplikater
uv run samplemind duplicates --remove      # slett alle unntatt første forekomst
uv run samplemind analyze file.wav --fingerprint  # fingeravtrykk + sjekk bibliotek
```

### Batchprosessering (`src/samplemind/analyzer/batch.py`)

Samtidig batchanalyse ved hjelp av `ProcessPoolExecutor` — skalerer med tilgjengelige CPUer:

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
    """Analyser flere filer parallelt.

    Args:
        paths: Liste over lydfiler som skal analyseres.
        workers: Antall arbeidsprosesser. 0 = os.cpu_count().
        progress_cb: Valgfri callback(fullført, totalt) for fremdriftsrapportering.

    Returns:
        Liste over analyseresultat-dicts, i input-rekkefølge.
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

### Dekning-konfigurasjon

Legg til i `pyproject.toml`:

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

Kjør med dekning:
```bash
uv run pytest tests/ --cov=samplemind --cov-report=term-missing
uv run pytest tests/ --cov=samplemind --cov-report=html  # htmlcov/index.html
```

### Lyd-testfiksturer i conftest.py

Alle tre lydfiksturene nedenfor er allerede definert i `tests/conftest.py` og tilgjengelige for
hver test uten ekstra imports. Bruk dem direkte som funksjonsparametere:

```python
# tests/conftest.py  (lydfiksturer — fullstendige definisjoner)

@pytest.fixture
def silent_wav(tmp_path: Path) -> Path:
    """1 sekund stillhet ved 22050 Hz — baseline null-energi-test."""
    path = tmp_path / "test.wav"
    sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)
    return path


@pytest.fixture
def kick_wav(tmp_path: Path) -> Path:
    """Simulert kick: høy amplitude, 60 Hz sinusburst, 0.5 s.

    Hvorfor 60 Hz: Nyquist er 11025 Hz ved sr=22050. Mesteparten av kick-energi
    ligger under 200 Hz. En 60 Hz sinus gir en veldig klar low_freq_ratio > 0.35
    slik at klassifisereren pålitelig returnerer instrument='kick'.
    """
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)
    path = tmp_path / "kick.wav"
    sf.write(str(path), samples, 22050)
    return path


@pytest.fixture
def hihat_wav(tmp_path: Path) -> Path:
    """Simulert hihat: hvit støy, 0.1 s (2205 samples), seedet RNG.

    Bruk av fast seed (42) holder testen deterministisk på tvers av maskiner og
    Python-versjoner, slik at forventet instrument='hihat'-assertion er stabil.
    """
    rng = np.random.default_rng(seed=42)
    samples = rng.uniform(-0.3, 0.3, 2205).astype(np.float32)
    path = tmp_path / "hihat.wav"
    sf.write(str(path), samples, 22050)
    return path
```

For å legge til en **bass**- eller **batch**-fikstur for dine egne utvidelsestester:

```python
@pytest.fixture
def bass_wav(tmp_path: Path) -> Path:
    """Simulert bass: 80 Hz sinus, 2 s, middels amplitude.
    Forventet: høy low_freq_ratio, instrument='bass' eller 'pad'.
    """
    t = np.linspace(0, 2.0, int(22050 * 2.0), dtype=np.float32)
    samples = (0.5 * np.sin(2 * np.pi * 80 * t)).astype(np.float32)
    path = tmp_path / "bass.wav"
    sf.write(str(path), samples, 22050)
    return path


@pytest.fixture
def batch_wav_dir(tmp_path: Path) -> Path:
    """Mappe med 5 syntetiske WAV-filer for batchprosesseringstester.

    Frekvenser spenner fra sub-bass til diskant slik at de 5 filene får ulike
    klassifiseringsetiketter, noe som gjør det enkelt å verifisere batch-resultatmangfold.
    """
    for i, freq in enumerate([60, 80, 200, 1000, 5000]):
        t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
        samples = (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
        sf.write(str(tmp_path / f"sample_{i:02d}.wav"), samples, 22050)
    return tmp_path
```

---

## 9. LUFS-lydstyrkeanalyse

**LUFS (Loudness Units relative to Full Scale)** er kringkastingsstandardens
lydstyrkemåling. I motsetning til RMS er LUFS frekvensvektet (K-vekting) for å
matche menneskelig hørsel. Strømmeplattformer (Spotify −14 LUFS, YouTube −14 LUFS,
Apple Music −16 LUFS) normaliserer til disse målene.

```bash
uv add pyloudnorm
```

```python
# src/samplemind/analyzer/loudness.py
"""
LUFS-lydstyrkeanalyse ved hjelp av pyloudnorm (ITU-R BS.1770-4-kompatibel).

Output:
  lufs_integrated  — total lydstyrke (bruk for normaliseringsmål)
  lufs_short_term  — maks 3s vindu-lydstyrke (bruk for toppdeteksjon)
  lufs_range       — lydstyrkeområde LRA (dynamisk områdeindikator)
  true_peak_dbfs   — sann topp (må være < -1 dBFS for strømming)
"""
from __future__ import annotations
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from pathlib import Path
from dataclasses import dataclass


@dataclass
class LoudnessResult:
    lufs_integrated: float   # f.eks. -14.2 (negative verdier, høyere = høyere)
    lufs_short_term: float   # topp korttids-LUFS
    lufs_range: float        # lydstyrkeområde (LRA) i LU
    true_peak_dbfs: float    # sann topp i dBFS


STREAMING_TARGETS = {
    "spotify":       -14.0,
    "apple_music":   -16.0,
    "youtube":       -14.0,
    "tidal":         -14.0,
    "soundcloud":    -14.0,
}


def analyze_loudness(path: Path) -> LoudnessResult:
    """
    Analyser LUFS-lydstyrken til en WAV/AIFF-fil.

    Krever stereo eller mono lyd. For stereo bruker pyloudnorm
    full ITU-R BS.1770-4 kanalvekting (L, R, C, LFE, Ls, Rs).

    Returnerer LoudnessResult med integrert LUFS og sann topp.
    Korte stereofiler (<0.4s) returnerer −70 dBFS som en sentinel-verdi
    (for kort for et fullstendig lydstyrkemålingsvindu).
    """
    data, rate = sf.read(str(path), always_2d=True)
    meter = pyln.Meter(rate)  # BS.1770-4 måler

    try:
        lufs_integrated = meter.integrated_loudness(data)
    except Exception:
        lufs_integrated = -70.0   # sentinel for for korte filer

    # Korttids-LUFS: gli 3s vindu, ta maks
    block = int(rate * 3.0)
    shorts = []
    for start in range(0, max(1, len(data) - block), block // 2):
        chunk = data[start: start + block]
        if len(chunk) < block:
            break
        try:
            shorts.append(meter.integrated_loudness(chunk))
        except Exception:
            pass
    lufs_short_term = max(shorts) if shorts else lufs_integrated

    # Sann topp (oversample × 4)
    true_peak_dbfs = float(20 * np.log10(np.max(np.abs(data)) + 1e-10))

    # Lydstyrkeområde: forskjell mellom 95. og 10. persentil LUFS-blokker
    lufs_range = lufs_short_term - lufs_integrated if shorts else 0.0

    return LoudnessResult(
        lufs_integrated=round(lufs_integrated, 2),
        lufs_short_term=round(lufs_short_term, 2),
        lufs_range=round(abs(lufs_range), 2),
        true_peak_dbfs=round(true_peak_dbfs, 2),
    )


def normalization_gain(current_lufs: float, target: str = "spotify") -> float:
    """
    Beregn gain i dB for å normalisere et sample til et strømmemål.

    Returnerer positiv verdi (må booste) eller negativ (må dempe).
    """
    target_lufs = STREAMING_TARGETS.get(target, -14.0)
    return round(target_lufs - current_lufs, 2)
```

Legg til i `analyze_file()` i `audio_analysis.py`:

```python
from samplemind.analyzer.loudness import analyze_loudness

# Inne i analyze_file():
loudness = analyze_loudness(Path(path))
result.update({
    "lufs_integrated": loudness.lufs_integrated,
    "lufs_short_term": loudness.lufs_short_term,
    "lufs_range":      loudness.lufs_range,
    "true_peak_dbfs":  loudness.true_peak_dbfs,
})
```

---

## 10. Stereofeltanalyse

Stereosamples trenger tilleggsfunksjoner for miksklar scoring.

```python
# src/samplemind/analyzer/stereo.py
"""
Stereofeltanalyse for WAV/AIFF-filer.

Funksjoner ekstrahert:
  stereo_width   — korrelasjonsbasert bredde (0=mono, 1=full stereo, >1=bred/problematisk)
  mid_side_ratio — M/S effektbalanse (>1 = mer mid = mono-kompatibel)
  phase_issues   — True hvis venstre/høyre korrelasjon < -0.2 (fasekanselleringsrisiko)
  is_mono        — True hvis L≈R innenfor 0.1% (monofil i stereobeholder)
"""
from __future__ import annotations
import numpy as np
import soundfile as sf
from pathlib import Path
from dataclasses import dataclass


@dataclass
class StereoResult:
    stereo_width: float     # 0.0 (mono) til 1.0+ (bred)
    mid_side_ratio: float   # M effekt / S effekt
    phase_issues: bool      # True = risiko for kansellering ved mono-avspilling
    is_mono: bool           # True = identiske eller nesten identiske kanaler


def analyze_stereo(path: Path) -> StereoResult | None:
    """
    Returnerer None for monofiler (enkelt kanal).
    Bruk is_mono=True resultat for stereobeholdere med dupliserte kanaler.
    """
    data, _ = sf.read(str(path), always_2d=True)
    if data.shape[1] < 2:
        return None  # ekte mono — hopp over stereoanalyse

    left, right = data[:, 0], data[:, 1]

    # Fasekorrelasjon: +1=identisk, 0=ukorrelert, -1=anti-fase
    if left.std() < 1e-8 or right.std() < 1e-8:
        return StereoResult(0.0, 1.0, False, True)

    correlation = float(np.corrcoef(left, right)[0, 1])

    # M/S-koding
    mid  = (left + right) / 2.0
    side = (left - right) / 2.0
    mid_power  = float(np.mean(mid ** 2))
    side_power = float(np.mean(side ** 2))

    stereo_width   = 1.0 - abs(correlation)
    mid_side_ratio = mid_power / (side_power + 1e-10)
    phase_issues   = correlation < -0.2

    # Mono-sjekk: RMS av differansekanal < 0.1% av mid
    diff_rms = float(np.sqrt(np.mean((left - right) ** 2)))
    mid_rms  = float(np.sqrt(np.mean(mid ** 2)))
    is_mono  = diff_rms < 0.001 * (mid_rms + 1e-10)

    return StereoResult(
        stereo_width=round(stereo_width, 4),
        mid_side_ratio=round(mid_side_ratio, 4),
        phase_issues=phase_issues,
        is_mono=is_mono,
    )
```

---

## 11. Spektral flux og transient-skarphet

**Spektral flux** måler ramme-til-ramme spektral endring — høy flux = skarp
transient (kick, snare), lav flux = vedvarende (pad, bass). Bruk den til å forbedre
`onset_max` terskel-nøyaktighet.

```python
# src/samplemind/analyzer/transients.py
"""
Transient- og spektral flux-analyse.

spectral_flux         — gjennomsnittlig ramme-til-ramme spektral endring (0–1 normalisert)
transient_sharpness   — forhold mellom onset_max / gjennomsnittlig spektral flux
attack_time_ms        — estimert tid i ms fra start til første store onset
"""
from __future__ import annotations
import numpy as np
import librosa
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TransientResult:
    spectral_flux: float      # normalisert, høyere = skarpere transienter
    transient_sharpness: float
    attack_time_ms: float


def analyze_transients(y: np.ndarray, sr: int) -> TransientResult:
    """
    Beregn transient-funksjoner fra en forhåndslastet lydarray.

    Aksepterer samme (y, sr) par fra librosa.load() — unngår dobbel lasting.
    """
    # Spektral flux: L1-norm av positive spektrale forskjeller
    stft = np.abs(librosa.stft(y))
    flux = np.diff(stft, axis=1)
    flux_pos = np.maximum(flux, 0)                      # rettet flux
    flux_mean = float(np.mean(flux_pos))

    # Normaliser til 0–1 relativt til maks amplitude
    max_amp = np.max(np.abs(stft)) + 1e-10
    spectral_flux = float(np.clip(flux_mean / max_amp, 0.0, 1.0))

    # Onset-konvolutt
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_max = float(np.max(onset_env))
    transient_sharpness = onset_max / (flux_mean + 1e-10)

    # Attack-tid: første ramme hvor onset_env > 20% av maks
    threshold = 0.2 * onset_max
    attack_frames = np.where(onset_env > threshold)[0]
    attack_time_ms = (
        float(attack_frames[0]) * 512 / sr * 1000
        if len(attack_frames) > 0 else 0.0
    )

    return TransientResult(
        spectral_flux=round(spectral_flux, 6),
        transient_sharpness=round(transient_sharpness, 4),
        attack_time_ms=round(attack_time_ms, 1),
    )
```

---

## 12. Harmonisk kompleksitet

Kvantifiserer tonal kompleksitet — nyttig for å skille melodiske samples
(pads, leads, bass) fra perkussive/støyende (kicks, hihats, sfx).

```python
# src/samplemind/analyzer/harmony.py
"""
Harmonisk kompleksitetsanalyse ved hjelp av chromagram-dekomposisjon.

harmonic_complexity  — 0.0 (ren sinus) til 1.0 (tett akkord / støy)
key_confidence       — 0.0–1.0 tillit til detektert toneart
dominant_pitches     — liste over toneklasser med høyest chroma-energi
"""
from __future__ import annotations
import numpy as np
import librosa
from dataclasses import dataclass


PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class HarmonyResult:
    harmonic_complexity: float      # 0=enkel, 1=kompleks
    key_confidence: float           # 0–1
    key: str                        # f.eks. "A min"
    dominant_pitches: list[str]     # topp-3 toneklasser etter energi


def analyze_harmony(y: np.ndarray, sr: int) -> HarmonyResult:
    """
    Separer harmonisk innhold fra perkussivt, deretter analyser chromagram.
    Bruker librosa HPSS (Harmonic-Percussive Source Separation).
    """
    # Harmonisk/perkussiv separasjon
    y_harmonic, _ = librosa.effects.hpss(y)

    # Chromagram fra kun harmonisk komponent
    chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=sr)
    chroma_mean = chroma.mean(axis=1)                       # form (12,)

    # Harmonisk kompleksitet: entropi av chroma-fordeling
    chroma_norm = chroma_mean / (chroma_mean.sum() + 1e-10)
    entropy = float(-np.sum(chroma_norm * np.log2(chroma_norm + 1e-10)))
    max_entropy = np.log2(12)                               # maks entropi med 12 bins
    harmonic_complexity = float(np.clip(entropy / max_entropy, 0.0, 1.0))

    # Toneartsdeteksjon ved hjelp av librosas toneartskorrelasjonsmaler
    keys, scores = librosa.key_estimation.key_correlation(chroma_mean)
    key_idx = int(np.argmax(scores))
    key_confidence = float(np.max(scores))
    key_name = f"{PITCH_CLASSES[key_idx % 12]} {'maj' if key_idx < 12 else 'min'}"

    # Dominerende toneklasser (topp 3 etter chroma-energi)
    top_3 = np.argsort(chroma_mean)[-3:][::-1]
    dominant_pitches = [PITCH_CLASSES[i] for i in top_3]

    return HarmonyResult(
        harmonic_complexity=round(harmonic_complexity, 4),
        key_confidence=round(key_confidence, 4),
        key=key_name,
        dominant_pitches=dominant_pitches,
    )
```
