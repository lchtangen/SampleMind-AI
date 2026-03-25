# /workflow — Run an Auggie Workflow

Execute a named multi-step workflow. Workflows coordinate multiple agents and skills
into a structured sequence. All workflow definitions live in `.auggie/workflows/`.

## Arguments

$ARGUMENTS
Required: workflow name
  ci-check              Full CI suite (ruff + pytest + coverage + clippy)
  dev-start             Start all services with ordered health checks
  new-feature           Guided checklist for implementing a new feature
  debug-classifier      Walk through classifier decisions for a WAV file
  add-audio-feature     Full-stack guide for adding a new librosa feature
  onboard-dev           First-time developer setup from zero
  release               macOS Universal Binary release pipeline (prod only)

Optional arguments passed through to the workflow:
  path=<wav>            For debug-classifier workflow
  name=<feature>        For add-audio-feature workflow

Examples:
  /workflow ci-check
  /workflow dev-start
  /workflow debug-classifier path=~/Music/kick.wav
  /workflow new-feature
  /workflow onboard-dev
  /workflow release

---

Parse the workflow name and any key=value arguments from $ARGUMENTS.

**Workflow: ci-check**

Execute in sequence — stop on first failure:

1. `uv run ruff check src/ tests/` → lint
2. `uv run ruff format --check src/ tests/` → format
3. `uv run pytest tests/ -v --tb=short -n auto` → tests
4. `uv run pytest tests/ --cov=samplemind --cov-report=term-missing --cov-fail-under=60 -q` → coverage
5. `cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings` → Rust lint

Report ✓/❌ per step. Final verdict: CI PASS or CI FAIL.

**Workflow: dev-start**

Read `.auggie/workflows/dev-start.yaml` and execute:
1. Verify env (uv, pnpm)
2. Init DB (init_db + alembic check)
3. Start FastAPI (background, validate port 8000)
4. Start Flask (background, validate port 5000)
5. Optionally start Tauri dev (if pnpm available)

**Workflow: new-feature**

Interactive guided checklist — ask the user what feature they're adding, then walk through:
1. Read relevant source files
2. Implement with type hints + src-layout imports
3. Write pytest fixture + test
4. Lint and format
5. Coverage check
6. IPC contract verification
7. Rust clippy (if Tauri touched)
8. Note which phase doc needs updating

**Workflow: debug-classifier path=<path>**

See `.auggie/workflows/debug-classifier.yaml`:
Extract all 9 features, trace each classifier rule, identify tipping point, suggest fix.

**Workflow: add-audio-feature name=<feature>**

See `.auggie/workflows/add-audio-feature.yaml`:
Guide through: librosa extraction → classifier update → SQLModel column → Alembic migration → SampleRepository → pytest fixture → coverage check.

**Workflow: onboard-dev**

See `.auggie/workflows/onboard-dev.yaml`:
Full first-time setup from zero — WSL2 check, uv install, deps, DB init, test run, hook install, git config, codebase tour.

**Workflow: release**

⚠️ REQUIRES macOS + confirmation.
See `.auggie/workflows/release.yaml`:
CI check → sidecar build → Universal Binary → sign → notarize → staple → auval → GitHub release.
Requires: `APPLE_SIGNING_IDENTITY`, `APPLE_TEAM_ID`, `APPLE_ID`, `APPLE_PASSWORD` env vars.

**Unknown workflow:**

If the name doesn't match any known workflow, list all available workflows and their descriptions.
Suggest: "Check `.auggie/workflows/` for the full list."

