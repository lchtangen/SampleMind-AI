"""
analyzer/audio_analysis.py — Full audio feature extraction pipeline.

Extracts 5 auto-detected fields from a WAV/AIFF file:
  - bpm:        Tempo in beats per minute (librosa beat tracker)
  - key:        Root note + quality ("C maj", "F# min") via chroma_cens + tonnetz
  - energy:     "low" | "mid" | "high" (RMS amplitude threshold)
  - mood:       "dark" | "chill" | "aggressive" | "euphoric" | "melancholic" | "neutral"
  - instrument: "loop" | "hihat" | "kick" | "snare" | "bass" | "pad" | "lead" | "sfx" | "unknown"

Public API:
  analyze_file(file_path: str) -> dict[str, float | str]

Internal helpers (_load, analyze_bpm, analyze_key) are not part of the public API.
All analysis results are stored in the samples table via SampleRepository.upsert().
"""

from typing import TypedDict

import librosa
import numpy as np

from samplemind.analyzer.classifier import classify


class AudioFeatures(TypedDict):
    """Typed return value for analyze_file() — each field has a precise type."""

    bpm: float
    key: str
    energy: str
    mood: str
    instrument: str


def _load(file_path: str) -> tuple[np.ndarray, int | float]:
    """Load audio once — reused by all analysis functions.

    Returns (y, sr) where sr may be int or float depending on the librosa backend.
    The default sr=22050 Hz is always returned as int, but resampled or
    native-rate loads can produce float sample rates.
    """
    return librosa.load(file_path, sr=22050)


def analyze_bpm(y: np.ndarray, sr: int | float) -> float:
    """Estimate tempo in beats per minute using librosa's beat tracker.

    Uses onset strength envelope and dynamic programming to find the most
    consistent inter-beat interval. Returns 0.0 for silent or very short clips.
    Accuracy is ±2 BPM for most electronic music.
    """
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # tempo may be a 0-dim array, a 1-element array, or a Python float
        # depending on librosa version and audio length.  Flatten to scalar:
        tempo_arr = np.asarray(tempo).ravel()
        bpm_val = float(tempo_arr[0]) if tempo_arr.size > 0 else 0.0
        return round(bpm_val, 2)
    except Exception:
        return 0.0


def analyze_key(y: np.ndarray, sr: int | float) -> str:
    """
    Detect root note + major/minor quality.

    - chroma_cens: 12 energy values, one per semitone (C through B)
    - Highest average energy note = root note
    - tonnetz: harmonic tension — minor keys score higher than major
    """
    try:
        chroma = librosa.feature.chroma_cens(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        key_index = int(chroma_mean.argmax())
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        root = notes[key_index]

        tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=sr)
        quality = "min" if np.abs(tonnetz).mean() > 0.1 else "maj"

        return f"{root} {quality}"
    except Exception:
        return "C maj"  # Default fallback


def analyze_file(file_path: str) -> AudioFeatures:
    """
    Full analysis of a WAV file. Returns a dict with:
      bpm, key, energy, mood, instrument

    All fields are auto-detected from the audio signal.
    """
    y, sr = _load(file_path)
    bpm = analyze_bpm(y, sr)
    key = analyze_key(y, sr)
    ai = classify(y, sr, key)

    return {
        "bpm": bpm,
        "key": key,
        "energy": ai["energy"],
        "mood": ai["mood"],
        "instrument": ai["instrument"],
    }
