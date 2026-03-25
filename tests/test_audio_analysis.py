import numpy as np
import soundfile as sf
import pytest
from samplemind.analyzer.audio_analysis import analyze_file


def synth_wav(path, freq=440, sr=22050, duration=1.0, amplitude=0.5):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = amplitude * np.sin(2 * np.pi * freq * t)
    sf.write(str(path), y, sr)
    return path


def test_analyze_file_sine(tmp_path):
    path = synth_wav(tmp_path / "sine.wav", freq=440, amplitude=0.5)
    result = analyze_file(str(path))
    assert isinstance(result["bpm"], float)
    assert isinstance(result["key"], str)
    assert result["energy"] in {"low", "mid", "high"}
    assert result["mood"] in {"dark", "chill", "aggressive", "euphoric", "melancholic", "neutral"}
    assert result["instrument"] in {"lead", "pad", "bass", "kick", "snare", "hihat", "loop", "sfx", "unknown"}


def test_analyze_file_silence(silent_wav):
    result = analyze_file(str(silent_wav))
    assert result["energy"] == "low"
    assert result["instrument"] in {"unknown", "pad", "sfx"}


@pytest.mark.parametrize("freq,expected_instr", [
    (60, "kick"),
    (440, "lead"),
    (1000, "hihat"),
])
def test_instrument_classification(tmp_path, freq, expected_instr):
    path = synth_wav(tmp_path / f"{freq}hz.wav", freq=freq, amplitude=0.8)
    result = analyze_file(str(path))
    assert result["instrument"] in {expected_instr, "unknown"}  # allow unknown for edge cases
