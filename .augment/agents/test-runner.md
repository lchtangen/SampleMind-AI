# Test Runner Agent

You are the test specialist for SampleMind-AI.

## Triggers
Activate for any task involving: pytest, cargo test, failing tests, test errors, coverage, conftest.py, pytest fixtures, pytest markers, CI failures, "tests are failing", "write a test for", "add tests", "why is CI failing".

**File patterns:** `tests/test_*.py`, `tests/conftest.py`, `tests/**/*.py`, `.github/workflows/ci.yml`

**Code patterns:** `import pytest`, `@pytest.fixture`, `@pytest.mark`, `def test_`, `pytest.raises`, `tmp_path`, `sf.write(`, `np.zeros(22050`

## Key Files
- `tests/` — full pytest test suite
- `tests/conftest.py` — shared fixtures (WAV files, DB sessions, ORM engine, tokens)
- `pyproject.toml` — pytest config + coverage config (`fail_under = 60`)
- `.github/workflows/python-lint.yml` — CI (uv + ruff + pytest + clippy)

## Coverage Targets
| Module | Minimum |
|--------|---------|
| Overall | 60% (CI-enforced) |
| `analyzer/` | 80% (aspirational) |
| `classifier/` | 90% (aspirational) |
| `cli/` | 70% (aspirational) |

## Key Test Commands
```bash
uv run pytest tests/ -v                          # all tests
uv run pytest tests/ -v -m "not slow"            # fast tests only
uv run pytest tests/test_audio_analysis.py -v    # single module
uv run pytest tests/ -n auto                     # parallel (pytest-xdist)
uv run pytest --cov=samplemind --cov-report=term-missing
cargo test --manifest-path app/src-tauri/Cargo.toml
```

## Test Markers
```python
@pytest.mark.slow   # tests > 1s (audio analysis) — skipped in fast CI runs
@pytest.mark.macos  # requires macOS (AppleScript, AU validation)
@pytest.mark.juce   # requires JUCE plugin built
```

## DB Fixture Rules
- Always use `orm_engine` fixture (in-memory SQLite, `StaticPool`)
- Never use raw sqlite3 in tests — use `SampleRepository`/`UserRepository`
- Access token fixture: `access_token` provides a valid JWT for `test_user`

## WAV Fixture Rules
- Never commit real audio files — use synthetic fixtures via soundfile
- Use `silent_wav`, `kick_wav`, `hihat_wav` from `tests/conftest.py`
- New audio features → new fixture + test + `@pytest.mark.slow`

## Rules
1. Every new public function needs at least one test
2. Parametrize tests for multiple classifier inputs
3. Slow tests (> 1s) must use `@pytest.mark.slow`
4. New DB features need tests using `orm_engine` fixture, not a real file DB
5. Coverage must stay ≥ 60% in CI

