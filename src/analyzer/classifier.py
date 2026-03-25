"""
classifier.py — Rule-based audio classification for SampleMind AI

Classifies samples by energy, mood, and instrument type using
signal features extracted by librosa. No training data required —
these rules are based on acoustic properties of electronic music.

Feature quick reference:
  rms             Root Mean Square — average loudness/power of the signal
  spectral_centroid  Weighted mean frequency — high = bright, low = dark/warm
  zero_crossing_rate How often the waveform crosses zero — high = noisy/percussive
  spectral_flatness  0 = pure tone, 1 = white noise — identifies hihats vs bass
  spectral_rolloff   Freq below which 85% of energy lives — low = bass/kick
  onset_strength     Detects rhythmic attacks — high = percussive sample
"""

import warnings

import librosa
import numpy as np

# Suppress librosa warnings about very short audio files (< n_fft samples).
# These are expected when analyzing short one-shots like hihats.
warnings.filterwarnings("ignore", message="n_fft=.*is too large")


def _features(y: np.ndarray, sr: int, duration: float) -> dict:
    """Extract all classification features from a loaded audio signal."""

    # RMS energy — scalar representing overall loudness
    rms = float(np.sqrt(np.mean(y ** 2)))

    # Spectral centroid — average across time frames, normalized by Nyquist freq
    # Gives a value 0-1 where 0 = all energy at DC (silence) and 1 = all at top
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    centroid_mean = float(centroid.mean()) / (sr / 2)

    # Zero crossing rate — fraction of frames where signal crosses zero
    zcr = float(librosa.feature.zero_crossing_rate(y).mean())

    # Spectral flatness — 0 = pure tone (sine wave), 1 = white noise
    flatness = float(librosa.feature.spectral_flatness(y=y).mean())

    # Spectral rolloff — normalized frequency below 85% of energy
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
    rolloff_norm = float(rolloff.mean()) / (sr / 2)

    # Onset strength — mean strength of rhythmic attacks
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_mean = float(onset_env.mean())
    onset_max  = float(onset_env.max())

    # Low-frequency energy ratio — energy below 300 Hz vs total
    # Kicks and bass have very high low_freq_ratio; hihats have near zero
    stft = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    low_mask = freqs < 300
    low_energy = float(stft[low_mask].sum())
    total_energy = float(stft.sum()) + 1e-8
    low_freq_ratio = low_energy / total_energy

    return {
        "rms":           rms,
        "centroid_norm": centroid_mean,
        "zcr":           zcr,
        "flatness":      flatness,
        "rolloff_norm":  rolloff_norm,
        "onset_mean":    onset_mean,
        "onset_max":     onset_max,
        "low_freq_ratio": low_freq_ratio,
        "duration":      duration,
    }


def classify_energy(f: dict) -> str:
    """
    Energy = how loud and powerful the sample feels.
    RMS is the most direct measure — it's the physical definition of loudness.
    Thresholds are calibrated for typical 16-bit WAV production samples.
    """
    rms = f["rms"]
    if rms < 0.015:
        return "low"
    elif rms < 0.06:
        return "mid"
    else:
        return "high"


def classify_mood(f: dict, key: str) -> str:
    """
    Mood = emotional quality of the sample.

    dark:      low centroid + minor key → warm, heavy, ominous
    chill:     low centroid + low rms + slow → relaxed, laid-back
    aggressive: high zcr + high onset + high centroid → intense, driven
    euphoric:  major key + high centroid + mid-high energy → uplifting, bright
    melancholic: minor key + low energy + low onset → sad, introspective
    """
    is_minor   = "min" in (key or "")
    centroid   = f["centroid_norm"]
    rms        = f["rms"]
    zcr        = f["zcr"]
    onset_mean = f["onset_mean"]

    # Aggressive: noisy + percussive + bright
    if zcr > 0.08 and onset_mean > 3.0 and centroid > 0.15:
        return "aggressive"

    # Dark: warm spectrum + minor key
    if centroid < 0.12 and is_minor:
        return "dark"

    # Melancholic: minor key + quiet + low rhythmic activity
    if is_minor and rms < 0.03 and onset_mean < 1.5:
        return "melancholic"

    # Chill: low-mid centroid + low-mid energy + not percussive
    if centroid < 0.15 and rms < 0.05 and onset_mean < 2.0:
        return "chill"

    # Euphoric: major key + bright spectrum + decent energy
    if not is_minor and centroid > 0.12 and rms > 0.02:
        return "euphoric"

    # Default for unclassified
    return "neutral"


def classify_instrument(f: dict) -> str:
    """
    Instrument type — identifies what kind of sound this is.

    The decision logic mirrors how producers think about samples:
    - Kicks:   punchy low-end, short, strong attack, low ZCR
    - Snares:  mid-range, short, strong attack, moderate ZCR
    - Hi-hats: high frequency, noisy (high flatness + ZCR), short
    - Bass:    dominant low frequencies, long/looping, tonal (low flatness)
    - Pads:    mid-high, long, smooth (low onset), tonal
    - Leads:   bright, medium length, melodic
    - Loops:   long duration (> 2s) → almost certainly a loop
    - SFX:     flat spectrum + doesn't fit any other profile
    """
    dur  = f["duration"]
    lfr  = f["low_freq_ratio"]
    flat = f["flatness"]
    zcr  = f["zcr"]
    cen  = f["centroid_norm"]
    om   = f["onset_mean"]
    omax = f["onset_max"]
    roll = f["rolloff_norm"]

    # Loops — long files are almost always loops, check this first
    if dur > 2.0 and om > 0.8:
        return "loop"

    # Hi-hat / cymbal: very noisy, high ZCR, high rolloff, short
    if flat > 0.2 and zcr > 0.1 and roll > 0.3 and dur < 1.0:
        return "hihat"

    # Kick: dominant low-end, strong single attack, short
    if lfr > 0.35 and omax > 4.0 and dur < 0.8 and zcr < 0.08:
        return "kick"

    # Snare: moderate low-end, noisy (some flatness), strong attack, short
    if omax > 3.0 and flat > 0.05 and dur < 0.8 and lfr < 0.35:
        return "snare"

    # Bass: heavy low-end, tonal (low flatness), longer
    if lfr > 0.3 and flat < 0.05 and dur > 0.3:
        return "bass"

    # Pad: long, smooth (low onset), mid-high frequency
    if dur > 1.5 and om < 1.5 and cen > 0.08:
        return "pad"

    # Lead: melodic, shorter, brighter than a pad
    if cen > 0.15 and flat < 0.1 and dur < 3.0:
        return "lead"

    # SFX: noisy or doesn't fit anything else
    if flat > 0.1:
        return "sfx"

    return "unknown"


def classify(y: np.ndarray, sr: int, key: str) -> dict:
    """
    Main entry point — run all classifiers and return a dict of results.

    Returns:
        { "energy": "high", "mood": "dark", "instrument": "kick" }
    """
    duration = float(len(y)) / sr
    f = _features(y, sr, duration)

    return {
        "energy":     classify_energy(f),
        "mood":       classify_mood(f, key),
        "instrument": classify_instrument(f),
    }
