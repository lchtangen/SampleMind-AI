# /phase-doc — Scaffold a New Phase Document

Create a new phase document pair (Norwegian + English) following the SampleMind doc conventions.

## Arguments

$ARGUMENTS
Required: phase number and title
Examples:
  /phase-doc 11 "Advanced Search and Recommendations"
  /phase-doc 12 "Mobile App (React Native)"

---

Create a new phase document pair for SampleMind-AI. Arguments: $ARGUMENTS

**Step 1 — Parse arguments:**
Extract phase number (N) and title from $ARGUMENTS.
- Norwegian filename: `docs/no/fase-NN-<slug>.md`
- English filename: `docs/en/phase-NN-<slug>.md`
- Slug: title in lowercase, spaces → hyphens, remove special chars

**Step 2 — Check for conflicts:**
Verify no file already exists at those paths.

**Step 3 — Determine what phases precede this one:**
Read the plan or check docs/en/ to understand what prerequisites to list.
The previous phase (N-1) is always a prerequisite.

**Step 4 — Create both documents using the standard template:**

Every SampleMind phase doc has these 7 sections:
1. Title + one-sentence summary (as blockquote)
2. Prerequisites (phases N-1 complete, tools needed)
3. Goal State (bullet list of concrete outcomes)
4. Main sections (numbered, e.g. "1. Architecture", "2. Implementation", ...)
5. Migration Notes (what changes, what's preserved)
6. Testing Checklist (bash commands)
7. Troubleshooting (common errors + fixes)

**Conventions to follow:**
- Every code block has a language tag (python, bash, rust, typescript, cpp)
- Every code block representing a file has `# filename: path/from/repo/root` on line 1
- Shell commands use `$` prefix; output has no prefix
- English doc: prose in English, code comments in English
- Norwegian doc: headings in Norwegian, prose in Norwegian (informal "du"), code identical to English version

**Step 5 — Write the files:**
Create both `docs/en/phase-NN-<slug>.md` and `docs/no/fase-NN-<slug>.md`.
The Norwegian doc mirrors the English doc with translated headings and prose.
Code blocks are identical in both versions.

**Step 6 — Confirm:**
Show the paths of the created files and list the section headings.
Remind the user to reference ARCHITECTURE.md when designing the architecture section.
