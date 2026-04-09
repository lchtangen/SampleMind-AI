# AI Integration Guide: Claude Code, MCP, Copilot Agents

> **For Solo Developers Who Code at 10x Velocity**
> Last updated: April 9, 2026

---

## TL;DR: Your New Development Workflow

```bash
# OLD (2025): Write code manually, run commands manually, debug manually
code .
# write feature in editor
python -m pytest tests/
# read error, fix code, repeat
uv run samplemind import ~/Music/

# NEW (2026): AI writes code, Claude Code orchestrates, Copilot suggests
code .
# Press Cmd+I → "Add semantic search for dark samples"
# Claude Code AI agent scaffolds entire feature (code + tests + docs)
# GitHub Copilot inline suggestions fix your typos instantly
# Type ↵ enter, tests pass, commit.
```

---

## Part 1: Claude Code Workspace (Primary Interface)

### What is Claude Code?

Claude Code (claude.ai/code) is an AI development environment where:
- You describe features in natural language
- Claude generates code, tests, and docs automatically
- The workspace understands SampleMind's architecture (via `.claude/agents/`, `CLAUDE.md`)
- You stay in VS Code, Claude handles scaffolding and reviews

### Setup: Claude Code Workspace for SampleMind-AI

**Step 1: Create `.claude/workspace.yaml`**

```yaml
name: SampleMind-AI
description: AI audio sample library manager for FL Studio
target_os: [macos, linux, windows]
vcs: git
vcs_branch: master

# Tell Claude about your architecture
context:
  - path: ARCHITECTURE.md
    purpose: System design and IPC contract
  - path: CLAUDE.md
    purpose: Project conventions and tech stack
  - path: docs/en/phase-*
    purpose: Feature specifications
  - path: src/samplemind/
    purpose: Active development path (src-layout)

# Define agent routing
agents:
  - name: audio-analyzer
    trigger_keywords: [librosa, BPM, classifier, energy, mood, instrument]
    files: [src/samplemind/analyzer/**, tests/test_audio_analysis.py]

  - name: api-agent
    trigger_keywords: [FastAPI, REST, endpoint, Pydantic]
    files: [src/samplemind/api/**, src/samplemind/core/models/]

  - name: tauri-builder
    trigger_keywords: [Tauri, Rust, Svelte, desktop, IPC]
    files: [app/src-tauri/**, app/src/**]

  # ... 21 more agents auto-route by context

# Development settings
development:
  python_version: "3.13"
  package_manager: uv
  test_runner: pytest
  linter: ruff
  formatter: ruff
  type_checker: pyright

  # Auto-run these after each Claude Code generation
  post_generation_steps:
    - run: uv run ruff format src/
    - run: uv run ruff check src/
    - run: uv run pyright src/
    - run: uv run pytest tests/ -m "not slow" --tb=short
    - run: git diff --stat

# Success criteria (Claude uses this to evaluate generated code)
success_criteria:
  test_coverage_minimum: 80
  type_checker_passing: true
  linter_warnings_max: 0
  classifier_f1_minimum: 0.88
```

**Step 2: Create `.claude/agents/audio-analyzer/profile.md`**

```markdown
# Audio Analyzer Agent

## Expertise
- librosa feature extraction (spectral, temporal, energy)
- Audio classifier design (SVM, XGBoost ensembles)
- WAV fixture generation (pytest)
- Batch processing and parallel workers
- Active learning for edge cases

## When to activate
- File edited: `src/samplemind/analyzer/**.py` or `tests/test_audio_analysis.py`
- Keywords: librosa, BPM, key_detection, classifier, energy, mood, instrument, spectral_centroid
- Symbols: analyze_file, classify_energy, classify_instrument, fingerprint_file

## Responsibilities
- Generate audio analysis code following librosa 0.11+ patterns
- Write WAV fixtures (no real audio files in repo)
- Ensure classifier outputs match canonical enum values (low|mid|high, etc.)
- Suggest accuracy improvements (threshold tuning, ensemble methods)
- Generate comprehensive tests with coverage > 85%

## Context requirements
- Read: ARCHITECTURE.md, docs/en/phase-02-audio-analysis.md
- Understand: Current classifier F1 scores, known edge cases
- Follow: Canonical patterns in src/samplemind/analyzer/audio_analysis.py

## Example assistance
"Debug why the energy classifier predicts 'mid' for loud kicks"
→ Audio Analyzer Agent:
  1. Reads current samples and thresholds
  2. Suggests ensemble methods or threshold tuning
  3. Generates property-based tests to verify fix
  4. Commits with changelog entry
```

**Step 3: Create `.claude/commands/` (Claude Code slash commands)**

```markdown
# .claude/commands/add-endpoint.md
## /add-endpoint

Add a new FastAPI endpoint with full type safety.

**Usage:**
```
/add-endpoint
Name: search-semantic
Description: Search samples by semantic similarity
Method: GET
Auth: Bearer JWT
Parameters: query (string), top (int, default=20)
Response: List[SamplePublic]
```

**What Claude generates:**
- OpenAPI schema + Pydantic models
- Route with full type hints
- Comprehensive docstring with examples
- Integration tests
- Postman collection entry

---

# .claude/commands/add-test.md
## /add-test

Generate comprehensive tests for a function.

**Usage:**
```
/add-test
Function: classify_energy
File: src/samplemind/analyzer/classifier.py
Coverage goal: 95%
```

**What Claude generates:**
- Unit tests for all code paths
- Property-based tests (Hypothesis)
- Performance regression tests
- Edge case tests
- Coverage report highlighting gaps
```

### Using Claude Code: Typical Workflow

**Scenario: Add semantic search to the API**

1. **In claude.ai/code, describe the feature:**
```
Add semantic search endpoint to SampleMind API.

Requirements:
- Endpoint: GET /api/v1/samples/semantic-search
- Parameter: query (string, e.g., "dark trap kicks")
- Returns: List of top 20 matching samples with confidence scores
- Uses: FAISS vector index (locally), CLAP embeddings
- Auth: Bearer JWT (viewer+ permission required)
- Test coverage: >90%

Follow the existing pattern in api/routes/samples.py.
Use Pydantic models from core/models/sample.py.
```

2. **Claude Code AI agent:**
   - Activates `api-agent` (sees FastAPI + endpoint keywords)
   - Generates Pydantic schema for request/response
   - Creates FastAPI route with dependencies
   - Writes comprehensive tests (unit + integration)
   - Auto-formats, lints, type-checks
   - Returns pull request preview

3. **You review in VS Code:**
   ```python
   # Claude generated:
   @router.get("/semantic-search")
   async def semantic_search(
       query: str = Query(..., min_length=1, max_length=255),
       top: int = Query(default=20, ge=1, le=100),
       current_user: User = Depends(get_current_active_user),
   ) -> List[SamplePublic]:
       """Search samples by semantic similarity to query."""
       RBACService.require_permission(
           UserRole(current_user.role),
           Permission.AUDIO_READ
       )
       results = await semantic_index.find_similar(query, limit=top)
       return [sample_to_public(s) for s in results]
   ```

4. **You approve:**
   - Cursor over the code → Copilot suggests optimizations
   - Press ↵ → Claude formats, runs tests, commits
   - GitHub Actions runs CI automatically

---

## Part 2: GitHub Copilot Chat Agents

### What are Copilot Agents?

Copilot Agents are specialized AI assistants that auto-activate when you mention them in VS Code chat. Each domain gets its own agent with specific expertise.

### Available Agents (24 total)

**Domain Specialists:**
- `@audio-analyzer` — librosa, classifiers, WAV processing
- `@api-agent` — FastAPI endpoints, OpenAPI, validation
- `@web-agent` — Flask, HTMX, template rendering
- `@tauri-builder` — Rust, Svelte 5, TypeScript IPC
- `@fl-studio-agent` — FL Studio integration, JUCE, sidecar
- `@security-agent` — JWT, RBAC, encryption
- `@test-runner` — pytest, coverage, CI failures

**Phase Specialists:**
- `@phase-01-foundation` — tooling, config, logging
- `@phase-03-database` — SQLModel, Alembic, Tortoise ORM
- `@phase-04-cli` — Typer, Rich, MCP commands
- `@phase-11-semantic-search` — CLAP, FAISS, embeddings
- ... (21 more)

### Usage in VS Code

**Scenario: Copilot fixes a test failure**

```
In VS Code Chat (Cmd+I):

"@test-runner why is test_classify_energy failing?"

Copilot immediately:
1. Finds the test file
2. Reads the error
3. Suggests fix based on canonical patterns
4. Offers to apply fix to all 15 similar tests
```

**Scenario: Copilot reviews your code**

```
In PR comments, mention Copilot:

"@audio-analyzer review this classifier for edge cases"

Copilot reviews:
- Checks thresholds match canonical values
- Spots missing test coverage
- Suggests ensemble methods if accuracy < 0.88
- Creates a detailed review comment
```

**Scenario: Copilot generates missing tests**

```
"@test-runner add tests for semantic_search endpoint"

Copilot generates:
- Unit tests (mocked FAISS index)
- Integration tests (real database)
- Performance regression tests
- Authorization tests (RBAC)
- Edge case tests (empty query, too many results)
```

---

## Part 3: Model Context Protocol (MCP) Servers

### What is MCP?

MCP (Model Context Protocol) is a standard for AI models to interact with tools, files, databases, and APIs. Replace Typer CLI with MCP servers that Claude/Copilot/IDEs can understand natively.

### MCP Server for SampleMind CLI

**Current (Typer):**
```bash
uv run samplemind search --query "dark" --energy high --json
```

**New (MCP): Same capability, but AI-aware**

```python
# src/samplemind/mcp/server.py
from mcp.server import Server
from mcp.types import Resource, ResourceTemplate
import json

server = Server("samplemind-audio")

@server.list_resources()
async def list_resources() -> list[Resource]:
    """Available operations on the SampleMind library."""
    return [
        Resource(
            uri="search://samples",
            name="Search samples",
            description="Find samples by keyword, energy, instrument, mood"
        ),
        Resource(
            uri="analyze://audio",
            name="Analyze audio",
            description="Extract features from a WAV/AIFF file (BPM, key, energy, mood)"
        ),
        Resource(
            uri="classify://sample",
            name="Classify sample",
            description="Predict energy, mood, instrument for a sample in library"
        ),
        Resource(
            uri="recommend://curate",
            name="AI curation",
            description="Get Claude's recommendation for sample organization"
        ),
    ]

@server.call_tool("search")
async def handle_search(
    query: str,
    energy: str | None = None,
    instrument: str | None = None,
    mood: str | None = None,
    limit: int = 20,
) -> str:
    """Search the sample library.

    Args:
        query: Text query (e.g., "dark trap")
        energy: Filter by energy (low, mid, high)
        instrument: Filter by instrument (kick, snare, hihat, bass, pad, lead, sfx, loop, unknown)
        mood: Filter by mood (dark, chill, aggressive, euphoric, melancholic, neutral)
        limit: Max results to return (1-100)

    Returns:
        JSON list of samples with metadata
    """
    results = await search_samples(
        query=query,
        energy=energy,
        instrument=instrument,
        mood=mood,
        limit=limit
    )

    for result in results:
        yield f"🎵 {result['name']} | {result['energy']} | {result['bpm']} BPM | {result['instrument']}"

    # Also return machine-readable JSON for tools
    yield json.dumps(results)

@server.call_tool("analyze")
async def handle_analyze(audio_path: str) -> str:
    """Analyze a WAV file's audio features.

    Args:
        audio_path: Path to WAV/AIFF file

    Returns:
        JSON with BPM, key, energy, mood, instrument classifications
    """
    features = await analyze_file(audio_path)

    # Stream human-readable analysis
    yield f"📊 Analyzing {Path(audio_path).name}..."
    yield f"  BPM: {features['bpm']:.1f}"
    yield f"  Key: {features['key']}"
    yield f"  Energy: {features['energy']}"
    yield f"  Mood: {features['mood']}"
    yield f"  Instrument: {features['instrument']}"

    # Return JSON
    yield json.dumps(features)

if __name__ == "__main__":
    server.run()
```

**How Claude uses it:**

```
In Claude Code, you can now write:

"Search for all dark trap samples and group by BPM"

Claude:
1. Calls search://samples with energy=dark, instrument=kick
2. Gets back JSON list
3. Groups by BPM naturally
4. Returns structured report + generates code to save results
```

**How Copilot uses it:**

```
In VS Code Copilot Chat:

"@audio-analyzer why is this sample classified as high energy?"

Copilot:
1. Calls analyze://audio on the file
2. Gets detailed features (RMS, centroid, etc.)
3. Compares to threshold (RMS > 0.08 for high)
4. Explains reasoning with exact numbers
```

### Running MCP Servers Locally

```bash
# Start the SampleMind MCP server
uv run python src/samplemind/mcp/server.py

# Tell Claude about it (.env or claude.md)
# Claude now has access to search, analyze, classify, recommend

# Test in Claude Code:
# Search for "dark samples"
# → Claude calls search://samples
# → Gets results, formats for you
```

---

## Part 4: From GitHub Copilot Instructions to Agents

### Current: `.github/copilot-instructions.md`

This file tells GitHub Copilot how to behave in your repo. Now we upgrade it to activate specialized agents.

**Update `.github/copilot-instructions.md`:**

```markdown
# SampleMind-AI Copilot Instructions

> Powered by AI agents specializing in audio analysis, API design, testing, and more.

## AI Agent Routing

Copilot automatically activates specialized agents based on context:

### When to activate @audio-analyzer
- File contains: `librosa.load`, `classify_energy`, `spectral_centroid`
- Keywords: BPM, key_detection, energy, mood, instrument, WAV
- Task: "Debug why classifier predicts wrong energy"

**Example:**
User: "@audio-analyzer why does this tight snare sound like a kick?"
→ @audio-analyzer reads the file, suggests ensemble methods or threshold tuning

### When to activate @api-agent
- File contains: `APIRouter`, `@router.get`, `Pydantic`, FastAPI
- Keywords: endpoint, REST, OpenAPI, Bearer token
- Task: "Add an endpoint for semantic search"

### When to activate @test-runner
- File is: `tests/test_*.py`, `.github/workflows/*.yml`
- Keywords: pytest, CI failure, coverage
- Task: "Why is the test suite failing on Windows?"

## Copilot Chat Commands

Type these in Copilot Chat (Cmd+I):

### CodeLens Preview
Hover over a function → see Copilot preview of what it does

### Explain Code
Select code → Cmd+I "Explain this function to me like I'm new"
→ Copilot explains in plain English, links to relevant docs

### Generate Tests
"@test-runner generate tests for this function"
→ Copilot writes comprehensive unit + property-based tests

### Fix Code
"@audio-analyzer fix the energy classifier to handle edge cases"
→ Copilot applies fix, updates tests automatically

### Review Code
In PR: mention @audio-analyzer or @api-agent
→ Copilot leaves detailed review comment

## Patterns to Follow

### Type Safety
- All new public functions must have type hints
- Pydantic v2 strict mode for all validation
- FastAPI responses must use explicit Pydantic models

### Audio Processing
- Use canonical thresholds (energy: low<0.02, mid<0.08, high>=0.08)
- Always validate classifier output is in enum (low|mid|high)
- Write property-based tests with Hypothesis

### MCP Commands
- All CLI commands should have MCP server equivalents
- Return both human-readable stdout + JSON on demand
- Support streaming for long operations

## Cascade: Copilot → AI Agents → Code

```
User: "Add dark sample detection"
     ↓
Copilot detects audio + API keywords
     ↓
Activates @audio-analyzer + @api-agent
     ↓
Agents work together:
  @audio-analyzer: How to detect "dark" samples? (energy, mood, instrument)
  @api-agent: What endpoint + models to create?
     ↓
Generate code + tests + docs
     ↓
You review, hit ↵, tests pass
```
```

---

## Part 5: Complete Developer Workflow

### Scenario: Add Semantic Search (Real Example)

#### Step 1: You describe in Claude Code

```
"Add semantic search to find samples by meaning, not keywords.

Requirements:
- Use CLAP embeddings (pre-computed for library)
- FAISS vector index for fast similarity search
- Endpoint: GET /api/v1/samples/semantic-search?query=dark trap kicks&top=20
- Also support: /api/v1/samples/similar?id=<sample_id> (find similar)
- Auth: Viewer+ permission required
- Performance: <100ms per query on 100k samples
- Test coverage: >90%
- Works offline (bundled CLAP model + local FAISS)"
```

#### Step 2: Claude Code AI Agents Auto-Activate

1. **`@api-agent`** (sees FastAPI endpoint)
   - Generates Pydantic models for request/response
   - Creates FastAPI route with proper auth
   - Adds OpenAPI docs

2. **`@audio-analyzer`** (sees embeddings + classifier)
   - Generates embedding pipeline
   - Suggests quantization for local deployment
   - Writes embedding generation script

3. **`@phase-11-semantic-search`**
   - Generates FAISS index manager
   - Implements similarity search
   - Adds vector caching

4. **`@test-runner`**
   - Generates integration tests (with mock FAISS)
   - Performance regression tests
   - Auth tests (ensure viewer-only access)

#### Step 3: Claude Code Generates Code

```python
# src/samplemind/api/routes/semantic.py (AI-generated)
from fastapi import APIRouter, Query, Depends
from samplemind.core.models.sample import SamplePublic
from samplemind.core.auth import get_current_active_user, RBACService, Permission, UserRole
from samplemind.search.semantic_index import semantic_index

router = APIRouter(prefix="/semantic-search", tags=["semantic-search"])

@router.get("")
async def search_semantic(
    query: str = Query(..., min_length=1, max_length=255),
    top: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
) -> List[SamplePublic]:
    """Search samples by semantic meaning using CLAP embeddings.

    Examples:
        GET /api/v1/samples/semantic-search?query=dark%20trap%20kicks&top=20
        GET /api/v1/samples/semantic-search?query=ambient%20pads

    Returns:
        Top N samples ranked by semantic similarity (cosine distance).
        Each sample includes confidence score (0-1).
    """
    RBACService.require_permission(UserRole(current_user.role), Permission.AUDIO_READ)

    results = await semantic_index.find_similar(query, limit=top)
    return [sample_to_public(s) for s in results]

@router.get("/{sample_id}")
async def search_similar_samples(
    sample_id: int,
    top: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
) -> List[SamplePublic]:
    """Find samples similar to a reference sample."""
    RBACService.require_permission(UserRole(current_user.role), Permission.AUDIO_READ)

    sample = await SampleRepository.get_by_id(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    results = await semantic_index.find_similar_samples(sample_id, limit=top)
    return [sample_to_public(s) for s in results]
```

```python
# tests/test_semantic_search_api.py (AI-generated)
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_semantic_search_requires_auth(client: AsyncClient):
    """Search endpoint requires Bearer token."""
    response = await client.get("/api/v1/samples/semantic-search?query=dark")
    assert response.status_code == 401  # Unauthorized

@pytest.mark.asyncio
async def test_semantic_search_viewer_permission(
    client: AsyncClient,
    viewer_token: str,
):
    """Viewer role can search samples."""
    with patch.object(semantic_index, 'find_similar') as mock_search:
        mock_search.return_value = [
            {"id": 1, "name": "kick_dark.wav", "energy": "high",confidence": 0.98},
            {"id": 2, "name": "kick_808.wav", "energy": "high", "confidence": 0.92},
        ]

        response = await client.get(
            "/api/v1/samples/semantic-search?query=dark%20trap%20kicks",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["confidence"] > 0.95

@pytest.mark.asyncio
async def test_semantic_search_query_validation(
    client: AsyncClient,
    user_token: str,
):
    """Query must be 1-255 characters."""
    # Empty query
    response = await client.get(
        "/api/v1/samples/semantic-search?query=",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 422  # Validation error

    # Very long query
    long_query = "a" * 256
    response = await client.get(
        f"/api/v1/samples/semantic-search?query={long_query}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 422

# ... 15 more tests generated automatically
```

#### Step 4: Claude Code Runs Post-Generation

```bash
# Automatically (configured in .claude/workspace.yaml):
✅ ruff format src/ && ruff check src/
✅ pyright src/samplemind/api/routes/semantic.py
✅ pytest tests/test_semantic_search_api.py -v
✅ git add -A && git commit -m "feat: add semantic search endpoint"
```

#### Step 5: You Review in VS Code

**Result of Claude generation visible in diff:**
- 150 lines of code (endpoint + data models + auth)
- 200 lines of tests (18 test cases, >95% coverage)
- 50 lines of documentation (docstrings + examples)
- All automated:
  - Type safety ✅ (Pydantic v2 strict)
  - Async support ✅ (query is awaited)
  - Auth ✅ (RBAC enforced)
  - Tests ✅ (>90% coverage)

**You make minimal edits:**
- Tweak the query validation (maybe allow wildcards?)
- Adjust parallelization (run 4 searches in parallel?)
- Everything else is production-ready

#### Step 6: GitHub Actions CI

```yaml
# .github/workflows/quality-gates.yml (auto-runs)
✅ Lint (ruff)
✅ Type check (Pyright)
✅ Tests (pytest)
✅ Coverage >80% ✓
✅ Performance regression <100ms ✓
✅ Security scan (no secrets leaked) ✓
✅ Copilot auto-review (checks patterns)
✅ Ready to merge!
```

#### Step 7: Deploy

```bash
# You merge to main
# GitHub Actions:
# 1. Builds macOS Universal Binary
# 2. Code signs + notarizes
# 3. Deploys to S3 + CloudFront
# 4. Updates version in app
# 5. Ships to users in next 24 hours

# You check dashboard:
# Semantic search: 2,500 queries/week
# Avg latency: 45ms (well under 100ms target)
# F1 accuracy: 0.91
```

---

## Advanced: AI Pair Programming

### Live Pair Programming with Claude Code

**Scenario: Real-time bug fix**

1. You open Claude Code while debugging
2. Describe the bug: "Classifier predicts 'low' for loud samples"
3. Claude Code:
   - Reads classifier thresholds
   - Analyzes test data
   - Suggests 3 fixes (threshold tuning, ensemble, active learning)
   - Generates tests for each approach
   - You pick fix #2 (ensemble)
4. Claude generates code, you hit ↵, tests pass
5. Commit, done

---

## Key Takeaways

| Old Way | New Way |
|---------|---------|
| You write code | Claude writes scaffolding, you review |
| Manual testing | LLM-generated comprehensive tests |
| Slow feedback loop | Instant Copilot inline suggestions |
| Hard to onboard contributors | 2-hour onboarding with AI agents |
| Maintenance burden | AI maintains docs, tests, code style |
| Deploy manually | GitOps + auto-notarization + feature flags |

---

## Next: Hands-On Setup

1. **This week:** Set up Claude Code workspace (.claude/workspace.yaml)
2. **Next week:** Activate first AI agent (@audio-analyzer)
3. **Week 3:** Launch semantic search using this workflow
4. **Ongoing:** Measure velocity improvements (target 3-5x faster feature shipping)

Your move. Ready to start?

---

*Maintained by: SampleMind AI Dev Team*
*Last updated: April 9, 2026*
