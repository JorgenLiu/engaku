---
plan_id: 2026-04-27-align-docs-and-agent-boundaries
title: Align documentation with runtime and add agent boundary instructions
status: done
created: 2026-04-27
---

## Background

The current README and packaging metadata have drifted from the v1.1.4 runtime, and the next release is planned as v1.1.5. `engaku init` now creates `.ai/engaku.json`, `.vscode/settings.json`, and `.vscode/dbhub.toml`, but the README file tree does not mention all of them. The DBHub TOML template is also used by `cmd_init.py` and documented in README, but `pyproject.toml` does not include `templates/*.toml` in package data, so a built distribution may omit it. Separately, the four generated agents already define strict ownership boundaries in their own `.agent.md` files, but those boundaries are important enough that Engaku should also inject a short always-on instruction file to reduce role drift during normal conversations.

## Design

Fix the runtime/documentation conflicts directly and keep the agent-boundary reinforcement small. Add `templates/*.toml` to package data and add a regression test that fails if the DBHub TOML template is not included in the packaging manifest inputs. Update README to match the current runtime: Python 3.8 support, generated files, `SubagentStart`, `apply` responsibilities, `.vscode/settings.json`, and `.vscode/dbhub.toml`.

Add a new generated instruction template, `.github/instructions/agent-boundaries.instructions.md`, with `applyTo: "**"`. The file should be concise and only capture hard role boundaries for coder, planner, reviewer, and scanner; do not duplicate each agent's full workflow. `engaku init` should create it without overwriting user edits, and `engaku update` should create it if missing without overwriting user edits, matching the existing lessons instruction behavior. Since this work is intended for the v1.1.5 release, bump package metadata and record the release in CHANGELOG as part of the same task.

## File Map

- Create: `src/engaku/templates/instructions/agent-boundaries.instructions.md`
- Create: `.github/instructions/agent-boundaries.instructions.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Package the DBHub TOML template**
  - Files: `pyproject.toml`, `tests/test_init.py`
  - Steps:
    - Add `templates/*.toml` to the `engaku` package-data list in `pyproject.toml`.
    - Add a focused unittest assertion that the package-data list includes `templates/*.toml`.
    - Keep the test stdlib-only and compatible with Python 3.8.
  - Verify: `python -m unittest tests.test_init && python -c "p=open('pyproject.toml').read(); assert '\"templates/*.toml\"' in p"`

- [x] 2. **Create the agent boundary instruction template**
  - Files: `src/engaku/templates/instructions/agent-boundaries.instructions.md`, `.github/instructions/agent-boundaries.instructions.md`
  - Steps:
    - Create identical template and live instruction files.
    - Use YAML frontmatter with `applyTo: "**"`.
    - Keep the body under 30 lines and include only hard ownership boundaries for coder, planner, reviewer, and scanner.
    - State that agent-specific workflows remain in the corresponding `.agent.md` files.
  - Verify: `cmp src/engaku/templates/instructions/agent-boundaries.instructions.md .github/instructions/agent-boundaries.instructions.md && grep -n "applyTo: \"\*\*\"\|planner\|reviewer\|scanner\|coder" src/engaku/templates/instructions/agent-boundaries.instructions.md`

- [x] 3. **Install the boundary instruction on init**
  - Files: `src/engaku/cmd_init.py`, `tests/test_init.py`
  - Steps:
    - Update `engaku init` so it copies `agent-boundaries.instructions.md` into `.github/instructions/` next to `lessons.instructions.md`.
    - Preserve an existing `.github/instructions/agent-boundaries.instructions.md` without overwriting it.
    - Update expected init files and add a preservation test.
  - Verify: `python -m unittest tests.test_init`

- [x] 4. **Install the boundary instruction on update**
  - Files: `src/engaku/cmd_update.py`, `tests/test_update.py`
  - Steps:
    - Update `engaku update` so it creates `.github/instructions/agent-boundaries.instructions.md` if missing.
    - Preserve an existing boundary instruction file without overwriting it.
    - Add update tests for created and preserved behavior.
  - Verify: `python -m unittest tests.test_update`

- [x] 5. **Align README generated-file docs**
  - Files: `README.md`
  - Steps:
    - Add `.ai/engaku.json` to the generated `.ai/` tree.
    - Add `.vscode/settings.json` and `.vscode/dbhub.toml` to the generated `.vscode/` tree.
    - Add `agent-boundaries.instructions.md` to the generated `.github/instructions/` description.
    - Mention that `engaku init --no-mcp` skips both `.vscode/mcp.json` and `.vscode/dbhub.toml`.
  - Verify: `grep -n "engaku.json\|settings.json\|dbhub.toml\|agent-boundaries.instructions.md\|--no-mcp" README.md`

- [x] 6. **Align README behavior docs**
  - Files: `README.md`
  - Steps:
    - Correct the Python baseline wording so it matches `requires-python = \">=3.8\"` and the current v1.1.x policy.
    - Update the `apply` subcommand description to mention model, MCP tool, and hook Python runtime config.
    - Add the reviewer `SubagentStart` hook to the hook behavior section.
    - Keep wording concise and avoid re-documenting every agent file.
  - Verify: `grep -n "Python 3.8\|MCP tool\|hook Python\|SubagentStart" README.md`

- [x] 7. **Update project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - Update the directory structure text so generated instruction stubs mention both `lessons.instructions.md` and `agent-boundaries.instructions.md`.
    - Add a short sentence to the overview noting that Engaku now generates an always-on agent boundary instruction to reinforce coder/planner/reviewer/scanner ownership.
  - Verify: `grep -n "agent-boundaries.instructions.md\|agent boundary" .ai/overview.md`

- [x] 8. **Bump version for v1.1.5**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Change `pyproject.toml` version from `1.1.4` to `1.1.5`.
    - Change `src/engaku/__init__.py` `__version__` from `1.1.4` to `1.1.5`.
    - Add `## [1.1.5] - 2026-04-27` to `CHANGELOG.md`.
    - Mention the packaged DBHub TOML template fix, the generated agent boundary instruction, and README/runtime documentation alignment in the changelog entry.
  - Verify: `python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert 'version = \"1.1.5\"' in p; assert '__version__ = \"1.1.5\"' in q" && grep -n "\[1.1.5\]" CHANGELOG.md`

- [x] 9. **Run focused regression verification**
  - Files: `src/engaku/templates/instructions/agent-boundaries.instructions.md`, `.github/instructions/agent-boundaries.instructions.md`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `tests/test_init.py`, `tests/test_update.py`, `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`, `README.md`, `.ai/overview.md`
  - Steps:
    - Run init and update unittest modules.
    - Run the full unittest suite if the focused modules pass.
    - Run the v1.1.5 version assertion.
    - Inspect the diff and confirm only documentation, package data, init/update instruction installation, version metadata, and related tests changed.
  - Verify: `python -m unittest tests.test_init tests.test_update && python -m unittest discover -s tests && python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert 'version = \"1.1.5\"' in p; assert '__version__ = \"1.1.5\"' in q"`

## Out of Scope

- Rewriting historical design documents under `docs/` or old `.ai/docs/` files.
- Changing agent workflow prompts beyond the new concise boundary instruction.
- Changing hook semantics or adding deterministic PreToolUse enforcement.
- Publishing a package or pushing release tags.