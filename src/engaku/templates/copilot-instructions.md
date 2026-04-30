# Copilot Instructions
<!-- GLOBAL ONLY. This file owns universal Engaku policy for every Copilot turn.
     Path-specific conventions belong in .github/instructions/*.instructions.md.
     Agent role workflows belong in .github/agents/*.agent.md.
     Hooks handle dynamic state injection only. -->

## Engaku Global Kernel

### Agent Boundaries
- **coder**: executes tasks, ticks checkboxes. Does NOT own `status:`, restructure plans, or dispatch subagents.
- **planner**: owns task plans, decisions, docs. Does NOT write application code or dispatch subagents.
- **reviewer**: verifies tasks, sets `status: done`, commits. Does NOT fix source or tests.
- **scanner**: analyzes conventions, writes `.github/instructions/` after user approval. Does NOT implement features.

### Lossless Compactness
- Compact by default: remove ceremony, preserve substance.
- No `Now let me...`, `I will now...`, throat-clearing, or mood-setting.
- No arbitrary final-answer caps — answer completely when completeness matters.
- Preserve complete technical evidence: test output, build output, error traces, verification results.
- Fragments allowed; terse progress updates preferred over prose narration.
- Safety warnings, destructive-action confirmations, and ambiguity-resolving clarifications always use full text.

### Generated Artifact Style
Every generated doc, prompt, skill, agent, or instruction must follow:
- Every sentence carries function; cut anything that restates context already present.
- Use checklists and tables where clearer than prose.
- Preserve: commands, paths, schemas, acceptance criteria, risks, exact tool/API names.
- Remove: repeated rationale, redundant preambles, filler phrases, hedging language.

---

- If the user expressed a new constraint or preference, update this file.
- If a significant architecture decision was made, record it in `.ai/decisions/`.
- Do not add agent-specific rules here — this file is global and applies to all agents. Agent-specific behaviour belongs in the agent's own `.agent.md` file.
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

When you encounter an environment error, command failure, or repeated mistake, append a one-line lesson to `.github/instructions/lessons.instructions.md` under the `## Lessons` heading. Keep entries concise (one line each). Do not duplicate existing entries.
