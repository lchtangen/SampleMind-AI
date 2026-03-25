# Skill: coverage

Run test coverage reports and identify untested code paths.

## Commands

```bash
# Full coverage report (terminal)
uv run pytest --cov=samplemind --cov-report=term-missing tests/

# HTML report (opens in browser)
uv run pytest --cov=samplemind --cov-report=html tests/
open htmlcov/index.html

# Coverage for a specific module
uv run pytest --cov=samplemind.analyzer --cov-report=term-missing tests/test_audio_analysis.py

# Fast coverage (skip slow audio tests)
uv run pytest --cov=samplemind --cov-report=term-missing -m "not slow" tests/

# Parallel coverage
uv run pytest --cov=samplemind --cov-report=term-missing -n auto tests/

# Check minimum threshold (CI-enforced)
uv run pytest --cov=samplemind --cov-fail-under=60 tests/
```

## Coverage Thresholds

| Module | Minimum | Aspirational |
|--------|---------|--------------|
| Overall | 60% | 80% |
| `analyzer/` | 60% | 80% |
| `analyzer/classifier.py` | 60% | 90% |
| `cli/` | 50% | 70% |
| `data/` | 60% | 75% |
| `search/` | 50% | 70% |
| `agent/` | 50% | 65% |

CI minimum: **60% overall** (`fail_under = 60` in `pyproject.toml`)

## Configuration

```toml
# pyproject.toml
[tool.coverage.run]
source = ["samplemind"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "src/main.py",          # legacy, not part of new package
]

[tool.coverage.report]
fail_under = 60
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

## Key Files

```
pyproject.toml        # coverage config
.coveragerc           # optional override
htmlcov/              # HTML report output (gitignored)
tests/conftest.py     # fixtures shared across all tests
tests/test_*.py       # test files
```

## Test Markers

```python
@pytest.mark.slow    # > 1s (audio analysis) — excluded in fast CI
@pytest.mark.macos   # requires macOS (AppleScript, auval)
@pytest.mark.juce    # requires JUCE plugin to be built
```

```bash
# Run only fast tests (CI default)
uv run pytest -m "not slow" tests/

# Run including slow tests
uv run pytest tests/

# Run macos-only tests
uv run pytest -m macos tests/
```

## WAV Fixtures (never commit real audio files)

```python
# tests/conftest.py — all test audio is synthetic
@pytest.fixture
def silent_wav(tmp_path):
    path = tmp_path / "test.wav"
    sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)
    return path

@pytest.fixture
def kick_wav(tmp_path):
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)
    path = tmp_path / "kick.wav"
    sf.write(str(path), samples, 22050)
    return path
```

## Coverage Improvement Strategy

1. Check `htmlcov/index.html` for red lines (uncovered)
2. Prioritize `classifier.py` — highest value, directly affects output quality
3. Add parametrized tests for edge cases (silent audio, very short clips, extreme BPM)
4. Mock external calls (`litellm.completion`, `boto3.client`, `stripe.*`) to test error paths
5. Use `--cov-report=xml` for SonarQube / CI badge integration

