# .auggie/ — Project Automation YAML Reference

> ⚠️ **This directory (`.auggie/`) is NOT read by the Augment Code VS Code extension.**
>
> If you have the Augment Code extension open in VS Code, it reads from `.augment/` only.

---

## What `.auggie/` Contains

This directory contains rich YAML reference files used as **project automation documentation**
and as the source of truth for generating content in the other AI tool directories.

| File | Purpose |
|------|---------|
| `settings.yaml` | Project metadata, tech stack, environment settings |
| `agents.yaml` | Full agent registry (all 25 agents with trigger patterns) |
| `routing.yaml` | Agent routing rules and keyword maps |
| `rules.md` | Extended project rules reference |
| `skills/*.yaml` | Detailed skill specs (richer format than SKILL.md) |
| `workflows/*.yaml` | Step-by-step workflow automation scripts |
| `tools/*.yaml` | External tool configurations |
| `environments/*.yaml` | Environment-specific settings |
| `hooks/*.yaml` | Git hooks and automation triggers |
| `prompts/*.md` | Reusable prompt templates |

---

## Correct AI Tool Config Paths

| Tool | Config | Read automatically? |
|------|--------|-------------------|
| **Augment Code** (VS Code ext) | `.augment/rules.md`, `.augment/memories/`, `.augment/skills/*/SKILL.md` | ✅ Yes |
| **Claude Code** | `CLAUDE.md`, `.claude/agents/`, `.claude/commands/` | ✅ Yes |
| **GitHub Copilot** | `.github/copilot-instructions.md`, `.github/agents/` | ✅ Yes |
| **Universal routing** | `AGENTS.md` (project root) | 📖 Reference |
| **This directory** | `.auggie/` | ❌ No (manual reference only) |

---

## How to Use `.auggie/` Content

### For Augment Code extension:
→ See `.augment/rules.md` (master rules)
→ See `.augment/memories/` (workspace context)
→ See `.augment/skills/*/SKILL.md` (skill definitions)

### For Claude Code:
→ See `CLAUDE.md` (root)
→ See `.claude/agents/*.md`
→ See `.claude/commands/*.md`

### For GitHub Copilot:
→ See `.github/copilot-instructions.md`
→ See `.github/agents/*.md`

### For universal routing:
→ See `AGENTS.md` at project root

---

## Keeping `.auggie/` in Sync

When adding a new skill, agent, or workflow:

1. **Primary:** Add/update `.augment/skills/{name}/SKILL.md` for Augment Code
2. **Claude Code:** Add/update `.claude/agents/{name}.md` (if agent)
3. **Copilot:** Add/update `.github/agents/{name}.md` (if agent)
4. **Universal:** Update `AGENTS.md` routing table
5. **Reference:** Optionally update `.auggie/skills/{name}.yaml` (detailed spec)

The YAML files in `.auggie/` are the **richest format** — use them as templates when
creating the lighter-weight SKILL.md and agent.md files for other tools.

