# Copilot Instructions
<!-- GLOBAL ONLY. Path-specific conventions belong in .github/instructions/*.instructions.md -->

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
