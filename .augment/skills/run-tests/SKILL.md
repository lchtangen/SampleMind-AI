---
name: run-tests
description: Run the pytest test suite and Rust tests with CI-matching configuration and coverage
---

# Skill: run-tests

Run the pytest test suite (and optionally the Rust test suite) with
CI-matching configuration. Supports fast, full, coverage, and single-test modes.

## When to use

Use this skill when the user asks to:
- Run the test suite (any scope)
- Check coverage for a module
- Debug a failing test
- Reproduce what GitHub Actions CI runs locally
- Write or update tests for audio analysis features

## Modes

### Fast (default — CI-safe, skips slow tests)
```bash
uv run pytest tests/ -m "not slow" -n auto --tb=short -q
```

### All tests (including slow audio analysis tests)
```bash
uv run pytest tests/ -v --tb=short -n auto
```

### Single test or file
```bash
uv run pytest tests/test_classifier.py::test_classify_energy_high -v --tb=long -s
```

### Coverage report
```bash
uv run pytest tests/ --cov=samplemind --cov-report=term-missing --cov-fail-under=60 -q
```

### Coverage for a specific module
```bash
uv run pytest tests/ --cov=samplemind.analyzer --cov-report=term-missing
```

### Rust tests
```bash
cargo test --manifest-path app/src-tauri/Cargo.toml
```

### Full CI suite (lint + Python tests + Rust lint + Rust tests)
```bash
uv run ruff check src/ tests/
uv run pytest tests/ --cov=samplemind --cov-fail-under=60 -q -n auto
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
cargo test --manifest-path app/src-tauri/Cargo.toml
```

## Coverage targets

| Scope                            | Target |
|----------------------------------|--------|
| Overall (CI-enforced)            | ≥ 60%  |
| `samplemind.analyzer`            | ≥ 80%  |
| `samplemind.analyzer.classifier` | ≥ 90%  |
| `samplemind.cli`                 | ≥ 70%  |

## Test markers

| Marker              | Meaning |
|---------------------|---------|
| `@pytest.mark.slow` | Tests > 1s (audio analysis). Skipped in fast mode and Windows CI. |
| `@pytest.mark.macos`| Requires macOS (AppleScript, AU plugin validation). |
| `@pytest.mark.juce` | Requires the JUCE plugin to be built. |

## WAV fixture rules

- **Never commit real audio files** — generate them with `numpy` + `soundfile`
- All fixtures live in `tests/conftest.py` and use `tmp_path`
- New audio features require a new WAV fixture + test

```python
# Minimal synthetic WAV fixture pattern:
@pytest.fixture
def silent_wav(tmp_path: Path) -> Path:
    path = tmp_path / "test.wav"
    sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)
    return path
```

## Common failures and fixes

| Failure | Fix |
|---------|-----|
| Coverage below 60% | Add tests for the red modules in the report |
| ImportError | `uv sync --dev` |
| Missing fixture | Add to `tests/conftest.py` |
| Wrong energy/mood value | Check classifier thresholds in `analyze-audio` skill |
| Rust clippy warning | Fix it — never suppress without a comment |

## CI matrix (GitHub Actions)

| Runner          | What runs |
|-----------------|-----------|
| ubuntu-latest   | ruff + all tests + coverage ≥ 60% |
| windows-latest  | fast tests only (not slow, not macos) |
| macos-14        | fast tests only (not slow) |
| rust job        | cargo clippy + cargo test |

## Related skills

- `check-ci` — full lint + test + clippy suite in one command
- `analyze-audio` — understand classifier thresholds to write good tests

