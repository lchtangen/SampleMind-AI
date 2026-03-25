# /test — Run Tests

Run the pytest test suite with optional filter, marker, or path.

## Arguments

$ARGUMENTS
Examples:
  (none)           — run all tests
  audio            — run tests matching "audio" in name
  -m slow          — run only tests marked @pytest.mark.slow
  -m "not slow"    — skip slow tests (faster)
  test_classifier  — run only test_classifier.py
  -k "energy"      — run tests containing "energy" in name

---

Run the pytest test suite for SampleMind-AI. Parse arguments from: $ARGUMENTS

**Before running:**
Check if `tests/` directory exists. If it doesn't:
- Note that the test suite hasn't been set up yet (this is Phase 2 work)
- Offer to help scaffold `tests/conftest.py` with WAV fixtures
- Show what test files exist with `uv run pytest --collect-only` anyway

**Run the tests:**
Build the pytest command:
- Base: `uv run pytest tests/ -v --tb=short`
- Add any filter/marker from $ARGUMENTS
- If a specific file is named, add it directly: `uv run pytest tests/<file>.py -v`

**If tests fail:**
- Show the full failure output for each failed test
- Identify the root cause (import error, assertion, fixture issue)
- Suggest a fix — check if it's a missing dependency (`uv add <pkg>`), wrong import path, or actual logic bug

**Show summary:**
Number of passed, failed, skipped, and duration. Highlight any errors clearly.

**Tip:** If no tests exist yet, the correct starting point is `docs/en/phase-02-audio-analysis.md` which has full `tests/conftest.py` and test file examples using soundfile WAV fixtures.
