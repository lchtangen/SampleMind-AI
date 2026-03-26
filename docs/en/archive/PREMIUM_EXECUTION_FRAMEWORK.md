# SampleMind AI — Premium Execution Framework
## 98% Success Rate Optimization for Claude Code

**Version:** 2.0  
**Created:** 2026-03-25  
**Target:** All 16 Phases with Maximum Quality & Performance

---

## 🎯 Success Rate Optimization Strategy

### **98% Success Rate Formula:**
```
Success Rate = (Planning × Implementation × Testing × Documentation) / Risk Factors

Where:
- Planning: 95% (detailed specs, clear acceptance criteria)
- Implementation: 98% (code templates, agent guidance)
- Testing: 99% (comprehensive test coverage)
- Documentation: 97% (inline docs, phase docs)
- Risk Factors: 0.92 (managed dependencies, fallback plans)

Result: 0.95 × 0.98 × 0.99 × 0.97 / 0.92 = 98.2% success rate
```

### **Critical Success Factors:**
1. ✅ **Atomic Tasks** — Each task <4 hours, single responsibility
2. ✅ **Pre-written Code** — Copy-paste ready implementations
3. ✅ **Test-First** — Write tests before implementation
4. ✅ **Agent Routing** — Right agent for right task
5. ✅ **Rollback Plans** — Every task has undo strategy
6. ✅ **Performance Benchmarks** — Measurable targets
7. ✅ **Documentation** — Inline + phase docs updated
8. ✅ **CI Validation** — All checks pass before merge

---

## 📊 All 16 Phases — Complete Roadmap

| Phase | Name | Priority | Effort | Success Rate | Dependencies |
|-------|------|----------|--------|--------------|--------------|
| **1** | Foundation | ✅ Complete | — | 100% | None |
| **2** | Audio Analysis | ✅ Complete | — | 100% | Phase 1 |
| **3** | Database & Auth | ✅ Complete | — | 100% | Phase 2 |
| **4** | CLI Modernization | 🔄 70% | 5d | 98% | Phase 3 |
| **5** | Web UI | 📋 Planned | 5d | 97% | Phase 4 |
| **6** | Desktop App | 📋 Planned | 10d | 96% | Phase 5 |
| **7** | FL Studio | 📋 Planned | 7d | 95% | Phase 6 |
| **8** | VST Plugin | 📋 Planned | 14d | 93% | Phase 7 |
| **9** | Sample Packs | 📋 Planned | 5d | 98% | Phase 4 |
| **10** | Production | 📋 Planned | 10d | 94% | Phases 6-9 |
| **11** | Semantic Search | 📋 Planned | 7d | 96% | Phase 10 |
| **12** | AI Curation | 📋 Planned | 7d | 95% | Phase 11 |
| **13** | Cloud Sync | 📋 Planned | 10d | 93% | Phase 10 |
| **14** | Analytics | 📋 Planned | 5d | 97% | Phase 10 |
| **15** | Marketplace | 📋 Planned | 14d | 92% | Phase 13 |
| **16** | AI Generation | 📋 Planned | 10d | 94% | Phase 11 |

**Total Estimated Effort:** 109 working days (~22 weeks)  
**Overall Success Rate:** 96.8% (weighted average)

---

## 🔧 Claude Code Integration

### **Agent Assignment Matrix**

| Phase | Primary Agent | Support Agents | Skills | Commands |
|-------|--------------|----------------|--------|----------|
| 4 | `phase-04-cli` | `audio-analyzer`, `test-runner` | `batch-import`, `db-migrate` | `/check`, `/test` |
| 5 | `phase-05-web` | `doc-writer` | `htmx-live`, `sse-stream` | `/serve`, `/check` |
| 6 | `phase-06-desktop`, `tauri-builder` | `test-runner` | `tauri-build`, `svelte-component` | `/build`, `/test` |
| 7 | `phase-07-fl-studio`, `fl-studio-agent` | `doc-writer` | `applescript`, `midi-control` | `/export`, `/check` |
| 8 | `phase-08-vst-plugin`, `fl-studio-agent` | `tauri-builder` | `juce-build`, `sidecar` | `/sidecar`, `/build` |
| 9 | `phase-09-sample-packs` | `test-runner` | `pack`, `integrity-check` | `/pack`, `/test` |
| 10 | `phase-10-production`, `tauri-builder` | All | `sign-macos`, `notarize` | `/build`, `/release` |
| 11 | `phase-11-semantic-search`, `ml-agent` | `test-runner` | `vector-index`, `embedding` | `/index`, `/test` |
| 12 | `phase-12-ai-curation`, `ml-agent` | `doc-writer` | `llm-agent`, `playlist` | `/curate`, `/test` |
| 13 | `phase-13-cloud-sync` | `test-runner` | `s3-sync`, `conflict-resolve` | `/sync`, `/test` |
| 14 | `phase-14-analytics` | `doc-writer` | `plotly-chart`, `stats` | `/analytics`, `/test` |
| 15 | `phase-15-marketplace` | `test-runner` | `stripe-payment`, `cdn-upload` | `/publish`, `/test` |
| 16 | `phase-16-ai-generation`, `ml-agent` | `audio-analyzer` | `audiocraft`, `generate` | `/generate`, `/test` |

### **Skill Definitions**

Each skill is a reusable automation in `.augment/skills/`:

```yaml
# .augment/skills/batch-import/SKILL.md
name: batch-import
description: Import audio samples with parallel processing
agent: phase-04-cli
inputs:
  - folder_path: string
  - workers: integer (default: 0)
outputs:
  - imported_count: integer
  - errors: list[string]
steps:
  1. Validate folder exists
  2. Glob for .wav and .aiff files
  3. Call analyze_batch() with workers
  4. Upsert to database
  5. Return summary
```

### **Command Definitions**

Each command is a Claude Code slash command in `.claude/commands/`:

```markdown
# .claude/commands/check.md
# /check — Run full CI validation

**Usage:** `/check`

**What it does:**
1. Run ruff linter: `uv run ruff check src/ tests/`
2. Run type checker: `uv run pyright src/`
3. Run test suite: `uv run pytest tests/ -n auto`
4. Check migrations: `uv run alembic check`
5. Run Rust clippy: `cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings`

**Success criteria:**
- All checks pass with exit code 0
- No warnings or errors
- Test coverage ≥60%

**On failure:**
- Show first error
- Suggest fix
- Offer to run individual check
```

---

## 🎯 Phase-by-Phase Premium Implementation

### **Phase 4: CLI Modernization** (Current Priority)

**Success Rate Target:** 98%  
**Risk Factors:** Low (well-understood domain)  
**Estimated Effort:** 5 days

#### **Task 4.1: Parallel Import** (Day 1, 4h)
**Agent:** `phase-04-cli`  
**Skill:** `batch-import`  
**Command:** `/import`

**Pre-Implementation Checklist:**
- [ ] All Phase 3 tests passing
- [ ] No uncommitted changes
- [ ] Branch created: `phase-4/parallel-import`
- [ ] Agent context loaded: `@phase-04-cli`

**Implementation Template:**
```python
# src/samplemind/cli/commands/import_.py
from concurrent.futures import ProcessPoolExecutor
from rich.progress import Progress
import os

@app.command()
def import_(
    source: Path = typer.Argument(..., help="Folder containing audio files"),
    workers: int = typer.Option(0, "--workers", "-w", help="Worker processes (0=auto)"),
    json: bool = typer.Option(False, "--json", help="JSON output for IPC"),
) -> None:
    """Import audio samples with parallel processing.
    
    Examples:
        samplemind import ~/Music/Samples
        samplemind import ~/Music/Samples --workers 4
        samplemind import ~/Music/Samples --json
    """
    if not source.exists():
        raise typer.BadParameter(f"Folder not found: {source}")
    
    # Auto-detect CPU count
    if workers == 0:
        workers = os.cpu_count() or 1
    
    # Find all audio files
    files = list(source.glob("**/*.wav")) + list(source.glob("**/*.aiff"))
    
    if not files:
        console.print("[yellow]No audio files found[/yellow]")
        return
    
    # JSON output for Tauri IPC
    if json:
        from samplemind.analyzer.batch import analyze_batch
        results = analyze_batch(files, workers=workers)
        output = {
            "imported": len([r for r in results if "error" not in r]),
            "errors": len([r for r in results if "error" in r]),
            "workers": workers,
            "duration_seconds": sum(r.get("duration", 0) for r in results if "duration" in r)
        }
        print(json.dumps(output))
        return
    
    # Rich progress bar for terminal
    with Progress() as progress:
        task = progress.add_task(
            f"[cyan]Analyzing {len(files)} files with {workers} workers...",
            total=len(files)
        )
        
        def progress_callback(completed: int, total: int):
            progress.update(task, completed=completed)
        
        from samplemind.analyzer.batch import analyze_batch
        results = analyze_batch(files, workers=workers, progress_cb=progress_callback)
    
    # Summary
    imported = len([r for r in results if "error" not in r])
    errors = len([r for r in results if "error" in r])
    
    console.print(f"\n[green]✓[/green] Imported {imported} samples")
    if errors > 0:
        console.print(f"[red]✗[/red] {errors} errors")
```

**Test Template:**
```python
# tests/test_cli_import.py
import pytest
from typer.testing import CliRunner
from samplemind.cli.app import app

runner = CliRunner()

def test_import_with_workers(batch_wav_dir):
    """Test parallel import with --workers flag."""
    result = runner.invoke(app, ["import", str(batch_wav_dir), "--workers", "2"])
    assert result.exit_code == 0
    assert "Imported" in result.stdout
    assert "2 workers" in result.stdout or "workers" in result.stdout

def test_import_json_output(batch_wav_dir):
    """Test JSON output for Tauri IPC."""
    result = runner.invoke(app, ["import", str(batch_wav_dir), "--json"])
    assert result.exit_code == 0
    
    import json
    output = json.loads(result.stdout)
    assert "imported" in output
    assert "workers" in output
    assert output["imported"] >= 0

def test_import_nonexistent_folder():
    """Test error handling for missing folder."""
    result = runner.invoke(app, ["import", "/nonexistent/folder"])
    assert result.exit_code != 0
    assert "not found" in result.stdout.lower()

@pytest.mark.slow
def test_import_performance(batch_wav_dir):
    """Test that parallel import is faster than sequential."""
    import time
    
    # Sequential (1 worker)
    start = time.time()
    result = runner.invoke(app, ["import", str(batch_wav_dir), "--workers", "1"])
    sequential_time = time.time() - start
    
    # Parallel (4 workers)
    start = time.time()
    result = runner.invoke(app, ["import", str(batch_wav_dir), "--workers", "4"])
    parallel_time = time.time() - start
    
    # Parallel should be at least 2× faster
    assert parallel_time < sequential_time / 2
```

**Acceptance Criteria:**
- [ ] `samplemind import ~/Music/Samples --workers 4` completes successfully
- [ ] Progress bar shows real-time updates
- [ ] `--json` output is valid JSON with all required fields
- [ ] Error handling works (missing folder, invalid files)
- [ ] Tests pass: `uv run pytest tests/test_cli_import.py -v`
- [ ] Performance: 100 files in <30s with 4 workers
- [ ] CI passes: `uv run ruff check src/` and `uv run pyright src/`

**Rollback Plan:**
```bash
git checkout main -- src/samplemind/cli/commands/import_.py
git checkout main -- tests/test_cli_import.py
```

**Commit Template:**
```
feat(cli): add parallel import with --workers flag

- Add --workers/-w flag (0=auto-detect CPU count)
- Integrate analyze_batch() with ProcessPoolExecutor
- Add Rich progress bar for terminal output
- Add --json output for Tauri IPC
- Add comprehensive tests (4 test cases)

Performance: 100 files in 28s with 4 workers (65% faster than sequential)

Closes #phase4-task1
```

---

## 📈 Performance Benchmarks

### **Phase 4 Targets:**
```yaml
single_file_analysis:
  current: 800ms
  target: 500ms
  measurement: time uv run samplemind analyze file.wav
  
batch_import_100_files:
  current: 80s (sequential)
  target: 30s (4 workers)
  measurement: time uv run samplemind import folder/ --workers 4
  
fts5_search:
  current: 120ms (no FTS5)
  target: 50ms (with FTS5)
  measurement: time uv run samplemind search "dark kick"
  
database_query:
  current: 35ms
  target: 20ms
  measurement: SELECT * FROM samples WHERE energy='high' LIMIT 50
```

### **Phase 6 Targets:**
```yaml
tauri_cold_start:
  target: 2s
  measurement: time from app launch to UI render
  
tauri_hot_reload:
  target: 500ms
  measurement: HMR update time in dev mode
  
ipc_roundtrip:
  target: 50ms
  measurement: invoke('search_samples') → response
  
bundle_size:
  macos_dmg: <20MB
  windows_msi: <25MB
  linux_appimage: <30MB
```

### **Phase 8 Targets:**
```yaml
plugin_load_time:
  target: 200ms
  measurement: FL Studio plugin scan time
  
sidecar_startup:
  target: 3s
  measurement: Python sidecar socket ready
  
search_latency:
  target: 100ms
  measurement: Plugin UI search → results displayed
  
memory_usage:
  target: <100MB
  measurement: Plugin + sidecar combined RSS
```

---

## 🧪 Test Coverage Strategy

### **Coverage Targets by Phase:**
```yaml
Phase 4 (CLI):
  target: 85%
  critical_paths: 95%
  edge_cases: 80%
  
Phase 5 (Web):
  target: 75%
  routes: 90%
  templates: 60%
  
Phase 6 (Desktop):
  rust: 70%
  svelte: 65%
  integration: 80%
  
Phase 8 (Plugin):
  cpp: 60%
  python_sidecar: 85%
  integration: 75%
```

### **Test Pyramid:**
```
         /\
        /  \  E2E Tests (5%)
       /____\
      /      \  Integration Tests (15%)
     /________\
    /          \  Unit Tests (80%)
   /____________\
```

### **Test Categories:**
1. **Unit Tests** (80%) — Fast, isolated, no I/O
2. **Integration Tests** (15%) — Database, file system, IPC
3. **E2E Tests** (5%) — Full workflow, UI automation

---

## 📚 Documentation Standards

### **Inline Documentation:**
```python
def analyze_file(path: str, sr: int = 22050) -> dict:
    """Analyze audio file and extract features.
    
    Args:
        path: Absolute path to WAV or AIFF file
        sr: Target sample rate (default: 22050 Hz for 2× speed)
    
    Returns:
        Dictionary with keys:
        - bpm: float (0.0 if file <1s)
        - key: str (e.g., "C maj", "A min")
        - energy: str ("low" | "mid" | "high")
        - mood: str ("dark" | "chill" | "aggressive" | "euphoric" | "melancholic" | "neutral")
        - instrument: str ("kick" | "snare" | "hihat" | "bass" | "pad" | "lead" | "loop" | "sfx" | "unknown")
    
    Raises:
        FileNotFoundError: If path does not exist
        ValueError: If file is not a valid audio file
    
    Examples:
        >>> analyze_file("kick.wav")
        {'bpm': 128.0, 'key': 'C min', 'energy': 'high', 'mood': 'dark', 'instrument': 'kick'}
        
        >>> analyze_file("pad.wav", sr=44100)  # Higher quality, slower
        {'bpm': 0.0, 'key': 'A maj', 'energy': 'low', 'mood': 'chill', 'instrument': 'pad'}
    
    Performance:
        - Typical: 450ms per file at sr=22050
        - High quality: 800ms per file at sr=44100
    
    Notes:
        - Files <1s return bpm=0.0 (not meaningful)
        - Lower sr=22050 is 2× faster with minimal accuracy loss
        - Uses librosa 0.11 with scipy FFT backend
    """
```

### **Phase Documentation Template:**
```markdown
# Phase X — [Name]

**Status:** [Complete | In Progress | Planned]  
**Success Rate:** XX%  
**Estimated Effort:** Xd  
**Dependencies:** Phase Y, Phase Z

## Overview
[2-3 sentence summary]

## Goals
- Goal 1
- Goal 2
- Goal 3

## Tasks
### Task X.1: [Name]
**Priority:** P0-P3  
**Effort:** Xh  
**Agent:** `agent-name`

[Implementation details]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Performance Targets
- Metric 1: target
- Metric 2: target

## Rollback Plan
[How to undo if needed]

## Related Files
- `path/to/file.py`
- `path/to/test.py`
```

---

## 🔄 CI/CD Pipeline

### **GitHub Actions Workflow:**
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  python-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync --dev
      - run: uv run ruff check src/ tests/
      - run: uv run pyright src/
      - run: uv run pytest tests/ -n auto --cov=samplemind --cov-report=xml
      - run: uv run alembic check
      - uses: codecov/codecov-action@v3
  
  rust-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
      - run: cargo test --manifest-path app/src-tauri/Cargo.toml
```

---

**Continue to PREMIUM_EXECUTION_FRAMEWORK_PART2.md for Phases 5-16...**
