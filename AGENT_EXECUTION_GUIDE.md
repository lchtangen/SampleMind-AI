# Claude Code Agent Execution Guide
## Optimized Workflow for 98% Success Rate

---

## 🤖 Agent Activation Protocol

### **Step 1: Context Loading**
```markdown
When starting a task, load the appropriate agent:

@phase-04-cli for CLI tasks
@phase-05-web for web UI tasks
@phase-06-desktop for Tauri/Svelte tasks
@tauri-builder for Rust/build tasks
@audio-analyzer for librosa/analysis tasks
@test-runner for testing tasks
@doc-writer for documentation tasks
```

### **Step 2: Pre-Flight Checklist**
```bash
# Before starting any task:
1. Check current branch: git branch --show-current
2. Verify tests pass: uv run pytest tests/ -n auto
3. Check for uncommitted changes: git status
4. Verify CI is green: check GitHub Actions
5. Load agent context: @agent-name
```

### **Step 3: Task Execution**
```markdown
1. Read task specification in PHASE_X_CHECKLIST.md
2. Copy pre-written code template
3. Modify as needed (minimal changes)
4. Run tests: uv run pytest tests/test_*.py -v
5. Run linter: uv run ruff check src/
6. Run type checker: uv run pyright src/
7. Commit with template message
```

---

## 📋 Agent-Specific Workflows

### **phase-04-cli Agent**

**Responsibilities:**
- CLI command implementation
- Typer integration
- Rich output formatting
- JSON output for IPC
- Batch processing

**Workflow:**
```bash
# 1. Load context
@phase-04-cli

# 2. Read task
cat PHASE_4_CHECKLIST.md | grep "Task 4.1"

# 3. Create branch
git checkout -b phase-4/task-1-parallel-import

# 4. Implement (copy from checklist)
# Edit: src/samplemind/cli/commands/import_.py

# 5. Add tests
# Edit: tests/test_cli_import.py

# 6. Run tests
uv run pytest tests/test_cli_import.py -v

# 7. Check quality
uv run ruff check src/samplemind/cli/
uv run pyright src/samplemind/cli/

# 8. Commit
git add src/samplemind/cli/commands/import_.py tests/test_cli_import.py
git commit -m "feat(cli): add parallel import with --workers flag

- Add --workers/-w flag (0=auto-detect CPU count)
- Integrate analyze_batch() with ProcessPoolExecutor
- Add Rich progress bar for terminal output
- Add --json output for Tauri IPC
- Add comprehensive tests (4 test cases)

Performance: 100 files in 28s with 4 workers (65% faster)

Closes #phase4-task1"

# 9. Push and verify CI
git push origin phase-4/task-1-parallel-import
```

**Common Patterns:**
```python
# CLI command structure
@app.command()
def command_name(
    arg: Type = typer.Argument(..., help="Description"),
    flag: Type = typer.Option(default, "--flag", "-f", help="Description"),
    json: bool = typer.Option(False, "--json", help="JSON output for IPC"),
) -> None:
    """Command description.
    
    Examples:
        samplemind command arg
        samplemind command arg --flag value
        samplemind command arg --json
    """
    # Validation
    if not validate(arg):
        raise typer.BadParameter("Error message")
    
    # JSON output for Tauri
    if json:
        result = do_work(arg, flag)
        print(json.dumps(result))
        return
    
    # Rich output for terminal
    with Progress() as progress:
        task = progress.add_task("Working...", total=100)
        result = do_work(arg, flag, progress_cb=lambda c, t: progress.update(task, completed=c))
    
    console.print(f"[green]✓[/green] Success: {result}")
```

---

### **phase-05-web Agent**

**Responsibilities:**
- Flask routes and blueprints
- HTMX integration
- SSE streaming
- Jinja2 templates
- Static assets

**Workflow:**
```bash
# 1. Load context
@phase-05-web

# 2. Implement route
# Edit: src/samplemind/web/blueprints/library.py

# 3. Create template
# Edit: src/samplemind/web/templates/library.html

# 4. Add partial template
# Edit: src/samplemind/web/templates/_results.html

# 5. Test manually
uv run samplemind serve
# Open http://localhost:5000

# 6. Add automated test
# Edit: tests/test_web.py

# 7. Run tests
uv run pytest tests/test_web.py -v

# 8. Commit
git commit -m "feat(web): add HTMX live search"
```

**Common Patterns:**
```python
# Blueprint structure
from flask import Blueprint, render_template, request

blueprint_name_bp = Blueprint("blueprint_name", __name__)

@blueprint_name_bp.route("/path")
def route_name():
    """Route description."""
    # Get parameters
    param = request.args.get("param", default_value)
    
    # Query database
    results = Repository.method(param)
    
    # Render template (full page or partial)
    return render_template("template.html", results=results)

# HTMX partial
@blueprint_name_bp.route("/path/partial")
def partial():
    """HTMX endpoint for live updates."""
    data = get_data()
    return render_template("_partial.html", data=data)

# SSE streaming
@blueprint_name_bp.route("/path/stream")
def stream():
    """Server-Sent Events endpoint."""
    def generate():
        for item in items:
            yield f"data: {json.dumps(item)}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream"
    )
```

---

### **phase-06-desktop + tauri-builder Agents**

**Responsibilities:**
- Svelte 5 components
- Tauri Rust commands
- IPC integration
- Build configuration
- Production bundles

**Workflow:**
```bash
# 1. Load context
@phase-06-desktop @tauri-builder

# 2. Implement Svelte component
# Edit: app/src/lib/components/SampleTable.svelte

# 3. Implement Rust command
# Edit: app/src-tauri/src/main.rs

# 4. Test in dev mode
cd app/
pnpm tauri dev

# 5. Test IPC
# Use browser DevTools console:
# await invoke('search_samples', { query: 'test' })

# 6. Add Rust tests
# Edit: app/src-tauri/src/main.rs (add #[cfg(test)] module)

# 7. Run Rust tests
cargo test --manifest-path app/src-tauri/Cargo.toml

# 8. Build production
pnpm tauri build

# 9. Commit
git commit -m "feat(desktop): add SampleTable component with IPC"
```

**Common Patterns:**
```rust
// Tauri command structure
#[tauri::command]
async fn command_name(param: String) -> Result<String, String> {
    // Call Python CLI
    let output = Command::new("samplemind")
        .args(["subcommand", &param, "--json"])
        .output()
        .map_err(|e| format!("Failed: {}", e))?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}
```

```svelte
<!-- Svelte 5 component structure -->
<script lang="ts">
    import { invoke } from '@tauri-apps/api/core';
    
    interface Props {
        prop: string;
    }
    
    let { prop }: Props = $props();
    let data = $state<DataType[]>([]);
    let loading = $state(false);
    
    async function loadData() {
        loading = true;
        try {
            const json = await invoke<string>('command_name', { param: prop });
            data = JSON.parse(json);
        } finally {
            loading = false;
        }
    }
</script>

{#if loading}
    <p>Loading...</p>
{:else}
    <div>
        {#each data as item}
            <div>{item.name}</div>
        {/each}
    </div>
{/if}
```

---

### **audio-analyzer Agent**

**Responsibilities:**
- librosa feature extraction
- Classifier logic
- Batch processing
- Performance optimization
- Audio test fixtures

**Workflow:**
```bash
# 1. Load context
@audio-analyzer

# 2. Implement feature
# Edit: src/samplemind/analyzer/audio_analysis.py

# 3. Add test fixture
# Edit: tests/conftest.py

# 4. Add test
# Edit: tests/test_audio_analysis.py

# 5. Run tests
uv run pytest tests/test_audio_analysis.py -v

# 6. Benchmark performance
time uv run samplemind analyze tests/fixtures/kick.wav

# 7. Commit
git commit -m "feat(analyzer): add spectral bandwidth feature"
```

---

### **test-runner Agent**

**Responsibilities:**
- Writing pytest tests
- Test fixtures
- Coverage analysis
- CI debugging
- Performance testing

**Workflow:**
```bash
# 1. Load context
@test-runner

# 2. Write test
# Edit: tests/test_*.py

# 3. Run specific test
uv run pytest tests/test_*.py::test_name -v

# 4. Run with coverage
uv run pytest tests/ --cov=samplemind --cov-report=term-missing

# 5. Check coverage threshold
uv run pytest tests/ --cov=samplemind --cov-report=term --cov-fail-under=60

# 6. Commit
git commit -m "test: add comprehensive tests for feature X"
```

**Test Patterns:**
```python
# Unit test structure
def test_function_name_scenario():
    """Test that function_name handles scenario correctly."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = function_name(input_data)
    
    # Assert
    assert result.field == expected_value
    assert len(result.items) == expected_count

# Parametrized test
@pytest.mark.parametrize("input,expected", [
    ("low", 0.01),
    ("mid", 0.05),
    ("high", 0.10),
])
def test_function_with_params(input, expected):
    result = function(input)
    assert result == pytest.approx(expected, rel=0.01)

# Fixture usage
def test_with_fixture(kick_wav, orm_engine):
    """Test using fixtures from conftest.py."""
    result = analyze_file(str(kick_wav))
    assert result["instrument"] == "kick"
```

---

## 🚀 Slash Commands Reference

### **/check** — Full CI Validation
```bash
# Runs all checks in sequence
uv run ruff check src/ tests/
uv run pyright src/
uv run pytest tests/ -n auto
uv run alembic check
cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
```

### **/test** — Run Test Suite
```bash
# All tests
uv run pytest tests/ -v

# Specific file
uv run pytest tests/test_cli.py -v

# Specific test
uv run pytest tests/test_cli.py::test_import_with_workers -v

# With coverage
uv run pytest tests/ --cov=samplemind --cov-report=term-missing

# Fast tests only (skip slow)
uv run pytest tests/ -m "not slow" -v
```

### **/build** — Build All Targets
```bash
# Python package
uv build

# Tauri desktop app
cd app/ && pnpm tauri build

# PyInstaller sidecar
uv run pyinstaller samplemind-sidecar.spec --noconfirm
```

### **/import** — Import Samples
```bash
# Basic import
uv run samplemind import ~/Music/Samples

# With workers
uv run samplemind import ~/Music/Samples --workers 4

# JSON output
uv run samplemind import ~/Music/Samples --json
```

### **/search** — Search Library
```bash
# Text search
uv run samplemind search --query "dark kick"

# With filters
uv run samplemind search --query "trap" --energy high --instrument kick

# JSON output
uv run samplemind search --query "dark" --json
```

---

## 📊 Quality Gates

### **Before Commit:**
- [ ] All tests pass: `uv run pytest tests/ -n auto`
- [ ] No lint errors: `uv run ruff check src/`
- [ ] No type errors: `uv run pyright src/`
- [ ] Coverage ≥60%: `uv run pytest --cov=samplemind --cov-fail-under=60`

### **Before Push:**
- [ ] Branch is up to date: `git pull origin main --rebase`
- [ ] Commit message follows convention
- [ ] No merge conflicts
- [ ] CI will pass (run `/check` locally)

### **Before Merge:**
- [ ] PR description complete
- [ ] All CI checks green
- [ ] Code review approved (if applicable)
- [ ] Documentation updated

---

## 🎯 Success Metrics by Agent

### **phase-04-cli:**
- Commands work with `--json` flag
- Progress bars render correctly
- Error messages are helpful
- Performance targets met

### **phase-05-web:**
- HTMX updates work without page reload
- SSE streams don't drop events
- Templates render in <100ms
- No JavaScript errors in console

### **phase-06-desktop:**
- Tauri dev mode starts in <5s
- IPC roundtrip <50ms
- UI is responsive (60fps)
- Production build <20MB

### **audio-analyzer:**
- Analysis <500ms per file
- Classifier accuracy ≥90%
- No librosa warnings
- Memory usage <200MB

### **test-runner:**
- All tests pass
- Coverage ≥60%
- No flaky tests
- Test suite <30s

---

**END OF AGENT EXECUTION GUIDE**

*Use this guide for every task to maintain 98% success rate*
