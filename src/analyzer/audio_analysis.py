from typing import Tuple

import librosa
import numpy as np

from analyzer.classifier import classify


def _load(file_path: str):
    """Load audio once — reused by all analysis functions."""
    return librosa.load(file_path)


def analyze_bpm(y, sr) -> float:
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return round(float(tempo), 2)


def analyze_key(y, sr) -> str:
    """
    Detect root note + major/minor quality.

    - chroma_cens: 12 energy values, one per semitone (C through B)
    - Highest average energy note = root note
    - tonnetz: harmonic tension — minor keys score higher than major
    """
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    key_index = int(chroma_mean.argmax())
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    root = notes[key_index]

    tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=sr)
    quality = "min" if np.abs(tonnetz).mean() > 0.1 else "maj"

    return f"{root} {quality}"


def analyze_file(file_path: str) -> dict:
    """
    Full analysis of a WAV file. Returns a dict with:
      bpm, key, energy, mood, instrument

    All fields are auto-detected from the audio signal.
    """
    y, sr = _load(file_path)
    bpm = analyze_bpm(y, sr)
    key = analyze_key(y, sr)
    ai  = classify(y, sr, key)

    return {
        "bpm":        bpm,
        "key":        key,
        "energy":     ai["energy"],
        "mood":       ai["mood"],
        "instrument": ai["instrument"],
    }
