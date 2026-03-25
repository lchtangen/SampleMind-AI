# Agent Index

This directory contains routing agents used to specialize implementation by phase and domain.

## Cross-Cutting Domain Agents

| Agent | Model | Trigger |
|-------|-------|---------|
| `audio-analyzer` | sonnet | librosa, BPM, key, classifier, WAV, fingerprinting, batch |
| `test-runner` | sonnet | pytest, tests, coverage, CI, fixtures, conftest |
| `tauri-builder` | sonnet | Tauri, Rust, Svelte, app/, IPC, pnpm |
| `doc-writer` | haiku | docs/, README, phase docs, ARCHITECTURE |
| `fl-studio-agent` | sonnet | FL Studio, JUCE, VST3, AU, AppleScript, sidecar |
| `api-agent` | sonnet | FastAPI, uvicorn, /api/v1/, JWT endpoints, OpenAPI |
| `web-agent` | sonnet | Flask, web UI, Jinja2, /api/samples, HTMX, SSE |
| `security-agent` | sonnet | JWT, bcrypt, RBAC, UserRole, Permission, OAuth2 |
| `devops-agent` | sonnet | setup-dev.sh, scripts/, WSL2, CI/CD, GitHub Actions |
| `ml-agent` | sonnet | ML models, transformers, embeddings, semantic search |

## Phase-Specific Agents

| Agent | Phase | Focus |
|-------|-------|-------|
| `phase-02-audio-testing` | 2 | pytest WAV fixtures, analyzer coverage |
| `phase-03-database` | 3 | SQLModel, Alembic, ORM migration |
| `phase-04-cli` | 4 | Typer, Rich, --json flag, CLI UX |
| `phase-05-web` | 5 | Flask API, HTMX, SSE progress |
| `phase-06-desktop` | 6 | Tauri commands, Svelte 5 Runes |
| `phase-07-fl-studio` | 7 | FL Studio automation, AppleScript |
| `phase-08-vst-plugin` | 8 | JUCE plugin, VST3/AU, CMake |
| `phase-09-sample-packs` | 9 | .smpack format, distribution |
| `phase-10-production` | 10 | signing, notarization, CI/CD release |

## Routing Rules

1. If the task explicitly references a phase number → use the matching `phase-NN` agent
2. If the task touches `api/`, `FastAPI`, `/api/v1/` → `api-agent`
3. If the task touches `web/`, `Flask`, templates → `web-agent`
4. If the task touches `auth/`, JWT, RBAC → `security-agent`
5. If the task touches `scripts/`, CI, setup → `devops-agent`
6. If the task touches ML models, embeddings → `ml-agent`
7. Otherwise → most specific cross-cutting agent for touched files
