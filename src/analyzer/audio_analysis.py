import librosa
import numpy as np
from typing import Tuple


# Load audio once and reuse — avoids reading the file twice per analysis.
def _load(file_path: str):
    return librosa.load(file_path)


def analyze_bpm(y, sr) -> float:
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return round(float(tempo), 2)


def analyze_key(y, sr) -> str:
    """
    Detect root note + major/minor quality.

    How it works:
    - chroma_cens: 12 energy values, one per semitone (C, C#, D ... B)
    - The note with highest average energy = root note
    - tonnetz: encodes harmonic relationships (fifths, thirds, tritones)
      Minor keys have higher mean absolute tonnetz values than major keys
      because minor thirds create more harmonic "tension".
    """
    chroma = librosa.feature.chroma_cens(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    key_index = int(chroma_mean.argmax())
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    root = notes[key_index]

    tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=sr)
    quality = "min" if np.abs(tonnetz).mean() > 0.1 else "maj"

    return f"{root} {quality}"


def analyze_file(file_path: str) -> Tuple[float, str]:
    y, sr = _load(file_path)
    return analyze_bpm(y, sr), analyze_key(y, sr)
