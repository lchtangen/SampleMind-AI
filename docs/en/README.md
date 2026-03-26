# SampleMind-AI — Documentation Index

English documentation for all 16 phases of the SampleMind-AI project.

---

## Phase Documentation

| Phase | Document | Status | Agent |
|-------|----------|--------|-------|
| 1 | [Foundation & Project Structure](phase-01-foundation.md) | ✅ Complete | `phase-01-foundation` |
| 2 | [Audio Analysis & AI Classification](phase-02-audio-analysis.md) | ✅ Complete | `audio-analyzer` |
| 3 | [Database & Data Layer](phase-03-database.md) | ✅ Complete | `phase-03-database` |
| 4 | [CLI with Typer and Rich](phase-04-cli.md) | ✅ Complete | `phase-04-cli` |
| 5 | [Web UI with Flask and HTMX](phase-05-web-ui.md) | ✅ Complete | `web-agent` |
| 6 | [Desktop App with Tauri 2 and Svelte 5](phase-06-desktop-app.md) | 📋 Planned | `phase-06-desktop` |
| 7 | [FL Studio Integration](phase-07-fl-studio.md) | 📋 Planned | `fl-studio-agent` |
| 8 | [VST3/AU Plugin with JUCE 8](phase-08-vst-plugin.md) | 📋 Planned — spec ready | `phase-08-vst-plugin` |
| 9 | [Sample Packs (.smpack)](phase-09-sample-packs.md) | 📋 Planned | `phase-09-sample-packs` |
| 10 | [Production and Distribution](phase-10-production.md) | 📋 Planned | `phase-10-production` |
| 11 | [Semantic Search & Vector Embeddings](phase-11-semantic-search.md) | 📋 Planned — spec ready | `phase-11-semantic-search` |
| 12 | [AI Curation Agent](phase-12-ai-curation.md) | 📋 Planned | `phase-12-ai-curation` |
| 13 | [Cloud Sync & Multi-Device](phase-13-cloud-sync.md) | 📋 Planned | `phase-13-cloud-sync` |
| 14 | [Advanced Analytics Dashboard](phase-14-analytics-dashboard.md) | 📋 Planned | `phase-14-analytics` |
| 15 | [Sample Pack Marketplace](phase-15-marketplace.md) | 📋 Planned | `phase-15-marketplace` |
| 16 | [AI-Assisted Sample Generation](phase-16-ai-sample-generation.md) | 📋 Planned | `phase-16-ai-generation` |

---

## ML / Utility Docs

| Document | Purpose |
|----------|---------|
| [remote_inference.md](remote_inference.md) | Remote inference APIs — LiteLLM, Ollama, OpenAI, HuggingFace |
| [quantization_and_offloading.md](quantization_and_offloading.md) | Load large models on low-VRAM systems with bitsandbytes |

---

## Specs (KFC Workflow Starting Points)

| Phase | Spec |
|-------|------|
| Phase 8 — VST Plugin | [`.claude/specs/phase-08-vst-plugin/requirements.md`](../../.claude/specs/phase-08-vst-plugin/requirements.md) |
| Phase 11 — Semantic Search | [`.claude/specs/phase-11-semantic-search/requirements.md`](../../.claude/specs/phase-11-semantic-search/requirements.md) |

---

## Archive

Historical planning documents (superseded by phase docs and `.claude/IMPLEMENTATION.md`):

```
docs/en/archive/
  EXECUTION_PLAN.md
  FIRST_SAMPLEMIND_PROJECT_ROADMAP.md
  PHASE_4_CHECKLIST.md
  PHASE_5_PROGRESS.md
  PREMIUM_AI_EXECUTION_PLAN.md
  PREMIUM_EXECUTION_FRAMEWORK.md
  PREMIUM_EXECUTION_FRAMEWORK_PART2.md
```

---

## Norwegian Docs

Norwegian translations are in [`docs/no/`](../no/).

---

## Other Key References

| File | Purpose |
|------|---------|
| [`ARCHITECTURE.md`](../../ARCHITECTURE.md) | System diagram, IPC contract table, all layer boundaries |
| [`CLAUDE.md`](../../CLAUDE.md) | Claude Code project guide — agents, commands, routing rules |
| [`.claude/IMPLEMENTATION.md`](../../.claude/IMPLEMENTATION.md) | Live phase status, agent index, command index |
