# Project Rules

## Code Style
- Python >=3.8. No 3.9+ syntax: no `str.removeprefix()`, no `dict | dict`, no `match/case`, no `X | Y` type annotations.
- Zero third-party dependencies. stdlib only.
- All user-facing strings (CLI output, error messages, hook messages, prompts) in English.

## Project Constraints
- `REQUIRED_HEADING` in `cmd_validate.py` is `"## Overview"` — module knowledge files must use this heading.
- Knowledge files must be ≤1500 characters (body only; frontmatter excluded), overwrite (not append), no vague filler.
- Module knowledge files must have `paths:` frontmatter listing covered source paths.
- Distribution: `pip install git+https://...` for MVP, PyPI later.
- `cmd_*.py` modules each have a `run()` + `main()` entry point; `cli.py` routes subcommands via lazy import.
- Test files use stdlib `unittest`; `sys.path.insert` for src layout; no pytest fixtures.

## Agent Configuration
- Model assignments per agent: see `.ai/engaku.json`. Run `engaku apply` to push changes into agent frontmatter.
- When updating any agent or hook file, always update BOTH the live version (`.github/`) AND the template version (`src/engaku/templates/`) in the same operation.
- MAX_CHARS for module knowledge body: 1600 (frontmatter excluded). Canonical value set in `.ai/engaku.json`; run `engaku apply` to sync into `rules.md`. Enforced by `cmd_validate.py`.
- check-update Stop hook is agent-scoped to `dev` only — brainstorming/planner agents must not trigger it.

## Forbidden
- Do not add third-party dependencies to `pyproject.toml`.
- Do not use Python 3.9+ syntax.
- Do not overwrite existing `.ai/` or `.github/` files during `engaku init`.
- Do not let any hook command exit non-zero unless it is intentionally blocking.
- Do not add agent-specific rules (knowledge-keeper, scanner-update, Stop hook) to `.github/copilot-instructions.md` — that file is global and applies to all agents including brainstorming/planner. Agent-specific behaviour belongs in the agent's own `.agent.md` file.
