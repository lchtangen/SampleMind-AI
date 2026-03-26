---
type: conditional
pattern: tests/**
---

## Testing Rules — Active When Editing Test Files

### WAV fixtures — always synthetic, never commit real audio files

```python
# Fixtures live in tests/conftest.py
@pytest.fixture
def silent_wav(tmp_path: Path) -> Path:
    sf.write(str(tmp_path / "test.wav"), np.zeros(22050, dtype=np.float32), 22050)
    return tmp_path / "test.wav"

@pytest.fixture
def kick_wav(tmp_path: Path) -> Path:
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    sf.write(str(tmp_path / "kick.wav"), (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32), 22050)
    return tmp_path / "kick.wav"

@pytest.fixture
def hihat_wav(tmp_path: Path) -> Path:
    sf.write(str(tmp_path / "hihat.wav"), np.random.uniform(-0.3, 0.3, 2205).astype(np.float32), 22050)
    return tmp_path / "hihat.wav"
```

### Markers

```python
@pytest.mark.slow    # tests > 1s (subprocess or audio analysis) — skip in fast mode
@pytest.mark.macos   # requires macOS (AppleScript, AU validation)
@pytest.mark.juce    # requires JUCE plugin to be built
```

Fast mode (default CI): `pytest -m "not slow"`
Full suite: `pytest -m slow` or `pytest tests/ -v`

### Coverage targets (CI enforces 60% overall minimum)

| Module | Target |
|--------|--------|
| `analyzer/` | 80%+ |
| `analyzer/classifier.py` | 90%+ |
| `cli/` | 70%+ |

### SSE streaming test pattern — critical gotcha

```python
# CORRECT: consume r.data INSIDE the mock context
with patch("samplemind.web.blueprints.import_.analyze_file", return_value=fake):
    r = client.post("/api/import", json={"folder": str(tmp_path)})
    raw = r.data.decode()  # ← must be here, generator is lazy

# WRONG: r.data outside the mock — mock already exited, generator runs without it
r = client.post(...)
with patch(...):
    raw = r.data.decode()
```

### DB isolation for web tests

Use the `orm_engine` fixture from `conftest.py` which swaps to an in-memory SQLite engine.
The `client` fixture depends on `orm_engine` — always use `client`, not `app.test_client()`.
