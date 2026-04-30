# Copilot Instructions
<!-- Global Engaku policy. Path rules live in .github/instructions/*.instructions.md.
     Agent workflows live in .github/agents/*.agent.md.
     Hooks inject dynamic state only. -->

## Engaku Global Kernel

### Agent Boundaries
- **coder** — executes tasks and ticks checkboxes. No `status:` changes, plan rewrites, or subagents.
- **planner** — owns task plans, decisions, and docs. No application code or subagents.
- **reviewer** — verifies tasks, sets `status: done`, commits. No source or test fixes.
- **scanner** — analyzes conventions and writes `.github/instructions/` after approval. No implementation.

### Lossless Compactness
- Default to compact, information-dense output.
- Cut `Now let me...`, `I will now...`, filler, and mood-setting.
- No arbitrary answer caps; be complete when detail matters.
- Preserve exact evidence: commands, paths, schemas, outputs, errors, and acceptance criteria.
- Prefer terse updates and fragments over process narration.
- Use full text for safety warnings, destructive confirmations, and ambiguity checks.

### Generated Artifact Style
Every generated doc, prompt, skill, agent, or instruction must:
- earn every sentence;
- use checklists or tables when clearer;
- preserve exact commands, paths, schemas, acceptance criteria, risks, and tool/API names;
- cut repeated rationale, redundant preambles, filler, and hedging.

---

- If the user states a durable constraint or preference, update this file.
- If a significant architecture decision was made, record it in `.ai/decisions/`.
- Keep agent-specific rules out of this file.
- When a design decision depends on external tool, platform, library, GitHub, or VS Code behaviour, verify with documentation or source code before asserting.

## Code Discipline

### Simplicity First
- Prefer fewer lines over more lines; choose the simplest thing that works.
- Prefer standard library over a new dependency.
- Prefer readable names over clever abstractions.
- Remove code when a feature can be dropped without loss.
- Ask "what is the minimal change that satisfies this requirement?" before typing.

### Surgical Changes
- Touch only what the current task requires; leave all other code alone.
- Match the style and idioms of surrounding code exactly — no drive-by reformats.
- Do not add features, error handling, or tests that were not explicitly requested.
- If you spot an out-of-scope improvement, file a note or task instead of fixing it now.
- Before saving, diff your changes and question every line not directly required.

## Lessons

When an environment issue, command failure, or repeated mistake teaches something reusable, append one line to `.github/instructions/lessons.instructions.md` under `## Lessons`. Do not duplicate entries.
