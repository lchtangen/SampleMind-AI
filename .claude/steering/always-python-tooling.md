---
type: always
---

## Python Tooling Rules — Always Active

### Package manager — always uv, never pip

```bash
uv sync --dev          # install dependencies
uv run pytest          # run tests
uv run ruff check src/ # lint
uv run samplemind      # run the CLI
```

- **Never suggest** `pip install`, `python -m venv`, `virtualenv`, `conda`
- **Never suggest** `black`, `flake8`, `pylint`, `isort` — the project uses `ruff` only

### Imports — src-layout only for new code

```python
# CORRECT — src-layout import
from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.data.repositories.sample_repository import SampleRepository

# WRONG — never use sys.path hacks in new code
import sys; sys.path.insert(0, "src")
```

### Type hints — required on all new public functions

```python
def analyze_file(path: str) -> dict[str, float | str | None]: ...
def upsert(data: SampleCreate) -> Sample: ...
```

### CLI output contract

- New CLI commands output JSON to **stdout** when `--json` flag is passed
- Human progress/status goes to **stderr** (or Rich Console with `stderr=True`)
- This contract is enforced by Rust/Tauri which reads stdout with `serde_json`

### Quality gate — always run before marking work complete

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pyright src/
uv run pytest tests/ -m "not slow" -q
```
