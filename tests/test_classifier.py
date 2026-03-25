import numpy as np

from samplemind.analyzer.classifier import (
    classify,
    classify_energy,
    classify_instrument,
    classify_mood,
)


def make_features(**overrides):
    base = dict(
        rms=0.05,
        centroid_norm=0.15,
        zcr=0.05,
        flatness=0.05,
        rolloff_norm=0.2,
        onset_mean=2.0,
        onset_max=3.0,
        low_freq_ratio=0.2,
        duration=1.0,
    )
    base.update(overrides)
    return base


def test_classify_energy_thresholds():
    assert classify_energy(make_features(rms=0.01)) == "low"
    assert classify_energy(make_features(rms=0.03)) == "mid"
    assert classify_energy(make_features(rms=0.08)) == "high"


def test_classify_mood_variants():
    f = make_features()
    assert classify_mood(f, "C min") in {"dark", "melancholic", "chill", "neutral"}
    assert classify_mood(f, "C maj") in {"euphoric", "neutral", "chill"}


def test_classify_instrument_variants():
    # Hi-hat
    f = make_features(flatness=0.3, zcr=0.2, rolloff_norm=0.4, duration=0.5)
    assert classify_instrument(f) == "hihat"
    # Kick
    f = make_features(low_freq_ratio=0.4, onset_max=5.0, duration=0.5, zcr=0.05)
    assert classify_instrument(f) == "kick"
    # Snare
    f = make_features(onset_max=4.0, flatness=0.1, duration=0.5, low_freq_ratio=0.2)
    assert classify_instrument(f) == "snare"
    # Bass
    f = make_features(low_freq_ratio=0.35, flatness=0.01, duration=1.0)
    assert classify_instrument(f) == "bass"
    # Pad
    f = make_features(duration=2.0, onset_mean=1.0, centroid_norm=0.1)
    assert classify_instrument(f) == "pad"
    # Lead
    f = make_features(centroid_norm=0.2, flatness=0.05, duration=1.0)
    assert classify_instrument(f) == "lead"
    # SFX
    f = make_features(flatness=0.2)
    assert classify_instrument(f) == "sfx"
    # Loop
    f = make_features(duration=3.0, onset_mean=1.0)
    assert classify_instrument(f) == "loop"
    # Unknown
    f = make_features(flatness=0.01, zcr=0.01, duration=0.1)
    assert classify_instrument(f) == "unknown"


def test_classify_aggressive_mood() -> None:
    """High ZCR + strong onsets + bright spectrum → aggressive (line 108 branch)."""
    f = make_features(zcr=0.10, onset_mean=4.0, centroid_norm=0.20)
    assert classify_mood(f, "C maj") == "aggressive"


def test_classify_melancholic_mood() -> None:
    """Minor key + very low RMS + sparse onsets → melancholic (line 116 branch).

    centroid_norm=0.12 sits exactly at the 'dark' guard boundary (centroid < 0.12),
    so dark is skipped and melancholic fires on: minor + rms<0.03 + onset_mean<1.5.
    """
    f = make_features(rms=0.02, onset_mean=1.0, centroid_norm=0.12)
    assert classify_mood(f, "A min") == "melancholic"


def test_classify_full_api():
    y = np.zeros(22050)
    sr = 22050
    result = classify(y, sr, "C maj")
    assert set(result.keys()) == {"energy", "mood", "instrument"}
    assert result["energy"] in {"low", "mid", "high"}
    assert result["mood"] in {
        "dark",
        "chill",
        "aggressive",
        "euphoric",
        "melancholic",
        "neutral",
    }
    assert result["instrument"] in {
        "lead",
        "pad",
        "bass",
        "kick",
        "snare",
        "hihat",
        "loop",
        "sfx",
        "unknown",
    }
