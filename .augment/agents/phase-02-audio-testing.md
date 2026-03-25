# Phase 2 Agent — Audio Analysis & Testing

Handles: librosa feature extraction, WAV fixtures, pytest audio tests, Phase 2 implementation.

## Triggers
Phase 2, audio analysis tests, WAV fixture setup, `tests/conftest.py`, `kick_wav`, `hihat_wav`, `silent_wav`, `soundfile` fixture creation, `@pytest.mark.slow`

## Key Files
- `src/samplemind/analyzer/audio_analysis.py`
- `src/samplemind/analyzer/classifier.py`
- `tests/conftest.py` — WAV and DB fixtures
- `tests/test_audio_analysis.py`, `tests/test_classifier.py`
- `docs/en/phase-02-audio-analysis.md`

## WAV Fixture Templates
```python
@pytest.fixture
def silent_wav(tmp_path: Path) -> Path:
    path = tmp_path / "test.wav"
    sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)
    return path

@pytest.fixture
def kick_wav(tmp_path: Path) -> Path:
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)
    path = tmp_path / "kick.wav"
    sf.write(str(path), samples, 22050)
    return path

@pytest.fixture
def hihat_wav(tmp_path: Path) -> Path:
    samples = np.random.uniform(-0.3, 0.3, 2205).astype(np.float32)
    path = tmp_path / "hihat.wav"
    sf.write(str(path), samples, 22050)
    return path
```

## Rules
1. Never commit real audio files — only synthetic soundfile fixtures
2. Audio analysis tests > 1s must use `@pytest.mark.slow`
3. New audio features need: fixture + test + `@pytest.mark.slow` if needed
4. Classifier output: `"low"/"mid"/"high"` for energy — NEVER `"medium"`

