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
- When updating any agent or hook file, always update BOTH the live version (`.github/`) AND the template version (`src/engaku/templates/`) in the same operation.
- Model assignments per agent: see `.ai/engaku.json`. Run `engaku apply` to push changes into agent frontmatter.
- After pushing a new version tag, reinstall engaku in this repo: `pip install -e .`
- Do not let any hook command exit non-zero unless it is intentionally blocking.
- Do not add agent-specific rules here — this file is global and applies to all agents. Agent-specific behaviour belongs in the agent's own `.agent.md` file.
- When a design decision depends on external tool, platform, library, GitHub, or VS Code behaviour, verify with documentation or source code before asserting.

## Lessons

When you encounter an environment error, command failure, or repeated mistake, append a one-line lesson to `.github/instructions/lessons.instructions.md` under the `## Lessons` heading. Keep entries concise (one line each). Do not duplicate existing entries.

## Code Style
- Python >=3.8. No 3.9+ syntax: no `str.removeprefix()`, no `dict | dict`, no `match/case`, no `X | Y` type annotations.
- Zero third-party dependencies. stdlib only.
- All user-facing strings in English.

## Project Constraints
- Distribution: `pip install engaku` (PyPI) or `pip install git+https://github.com/JorgenLiu/engaku.git` (from source).
- `cmd_*.py` modules each have a `run()` + `main()` entry point; `cli.py` routes subcommands via lazy import.
- Test files use stdlib `unittest`; `sys.path.insert` for src layout; no pytest fixtures.

## Forbidden
- Do not add third-party dependencies to `pyproject.toml`.
- Do not use Python 3.9+ syntax.
- Do not overwrite existing `.ai/` or `.github/` files during `engaku init`.
- Do not run `twine upload` or push build artefacts to PyPI manually. PyPI publishing is handled automatically by GitHub Actions on `v*.*.*` tag push.

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
