---
plan_id: 2026-04-27-planner-askquestions-v117
title: Planner askQuestions support and v1.1.7 release prep
status: done
created: 2026-04-27
---

## Background

Planner should be able to use VS Code Copilot's interactive questions UI when a planning or troubleshooting discussion needs clarification, without forcing every planner turn through a rigid question flow. VS Code documentation exposes this capability as the `#vscode/askQuestions` tool, so the planner agent should receive that tool and guidance to prefer it when useful. The current `engaku apply` tool updater strips every tool containing `/`, which would accidentally remove `vscode/askQuestions`; reviewer also needs an explicit English-only commit message rule before the next release.

## Design

Fix the tool-preservation bug before adding the planner tool. In `cmd_apply.py`, only MCP wildcard entries such as `context7/*` and `dbhub/*` should be stripped and replaced from `.ai/engaku.json`; non-MCP slash tools such as `vscode/askQuestions` must remain in the agent's inline `tools:` list. Then add `vscode/askQuestions` to both planner agent files and add soft guidance to use `#tool:vscode/askQuestions` when clarification would benefit from fixed options plus free-form input, falling back to normal chat questions when the tool is unavailable.

Reviewer commit behavior remains reviewer-owned. Update both reviewer agent files so the default commit command uses a concise English commit message based on the task title, and add a rule requiring English-only commit messages even when the task title is not English. Prepare v1.1.7 with version metadata and a changelog entry covering planner interactive clarification support, apply slash-tool preservation, and reviewer English commit guidance.

## File Map

- Modify: `src/engaku/cmd_apply.py`
- Modify: `tests/test_apply.py`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `CHANGELOG.md`

## Tasks

- [x] 1. **Preserve non-MCP slash tools in apply**
  - Files: `src/engaku/cmd_apply.py`, `tests/test_apply.py`
  - Steps:
    - Update `_update_agent_tools()` so it removes only MCP wildcard tools that end with `/*` instead of removing every tool containing `/`.
    - Keep replacement behavior for stale MCP wildcard entries such as `old-server/*`.
    - Add a regression test proving `vscode/askQuestions` survives `engaku apply` while MCP wildcard entries are still replaced from `mcp_tools`.
  - Verify: `python -m unittest tests.test_apply`

- [x] 2. **Give planner soft interactive clarification support**
  - Files: `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`
  - Steps:
    - Add `vscode/askQuestions` to the planner `tools:` list in both template and live agent files.
    - Preserve the live planner's existing `model:` and MCP tools.
    - Add non-mandatory guidance under planner workflow: when clarification is needed, prefer `#tool:vscode/askQuestions` for concise multiple-choice questions with an optional free-form answer; if the tool is unavailable or unnecessary, ask normally in chat.
    - Do not add a separate `.prompt.md` file or make interactive questioning a hard gate.
  - Verify: `grep -n "vscode/askQuestions\|#tool:vscode/askQuestions" src/engaku/templates/agents/planner.agent.md .github/agents/planner.agent.md`

- [x] 3. **Require English reviewer commit messages**
  - Files: `src/engaku/templates/agents/reviewer.agent.md`, `.github/agents/reviewer.agent.md`
  - Steps:
    - Change the all-tasks-pass commit instruction so the commit uses a concise English message based on the task title instead of blindly copying the frontmatter title.
    - Add a reviewer rule requiring English-only commit messages; if the task title is not English, reviewer must translate or summarize it before committing.
    - Keep reviewer edit scope limited to `.ai/tasks/*.md` and do not change verification ownership.
  - Verify: `grep -n "English commit messages only\|concise English commit message" src/engaku/templates/agents/reviewer.agent.md .github/agents/reviewer.agent.md`

- [x] 4. **Prepare v1.1.7 metadata**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Bump `pyproject.toml` version from `1.1.6` to `1.1.7`.
    - Bump `src/engaku/__init__.py` `__version__` from `1.1.6` to `1.1.7`.
    - Add `## [1.1.7] - 2026-04-27` to `CHANGELOG.md`.
    - Mention planner `vscode/askQuestions` support, `engaku apply` non-MCP slash-tool preservation, and reviewer English commit message guidance in the changelog entry.
  - Verify: `python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert 'version = \"1.1.7\"' in p; assert '__version__ = \"1.1.7\"' in q" && grep -n "\[1.1.7\]\|askQuestions\|English commit" CHANGELOG.md`

- [x] 5. **Run focused and full verification**
  - Files: `src/engaku/cmd_apply.py`, `tests/test_apply.py`, `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `.github/agents/reviewer.agent.md`, `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Run the focused apply test module.
    - Run the full unittest suite.
    - Run the v1.1.7 metadata assertion.
    - Inspect the diff and confirm only planner askQuestions support, apply slash-tool preservation, reviewer commit guidance, tests, changelog, and version metadata changed.
  - Verify: `python -m unittest tests.test_apply && python -m unittest discover -s tests && python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert 'version = \"1.1.7\"' in p; assert '__version__ = \"1.1.7\"' in q"`

## Out of Scope

- Creating `.github/prompts/*.prompt.md` or `src/engaku/templates/prompts/` files.
- Making interactive clarification mandatory for every planner conversation.
- Implementing a deterministic pause-and-resume dialogue protocol beyond the available VS Code `vscode/askQuestions` tool.
- Changing coder, scanner, or global Copilot instructions.
- Publishing to PyPI, pushing tags, or running release automation.
