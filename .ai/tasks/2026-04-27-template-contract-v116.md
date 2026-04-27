---
plan_id: 2026-04-27-template-contract-v116
title: Template contract cleanup and v1.1.6 release prep
status: done
created: 2026-04-27
---

## Background

Engaku's runtime and generated files have matured beyond the original placeholder templates. The generated `overview.md` template is still mostly fill-in scaffolding, while the live project overview has revealed several reusable categories that should be available to every initialized repo without leaking Engaku-specific release history. The global Copilot instructions template should keep only cross-agent rules that truly apply to every agent; `.ai/overview.md` updates remain planner-owned and should be planned as explicit implementation tasks. `prompt-check` should also match the multi-active-task behavior already implemented by `inject`.

## Design

Keep the template cleanup conservative and generic. Do not copy this repository's `.ai/overview.md` content into the distributed template; instead, turn the template into a high-signal project memory outline with sections for overview, directory structure, Engaku-managed files, constraints, tech stack, and verification commands. Add only one cross-agent rule to `copilot-instructions.md`: verify external platform/library/tool facts with documentation or source before making design claims. Do not add a global rule telling every agent to modify `.ai/overview.md`; instead, clarify in the planner agent templates that planner preserves overview ownership by adding a concrete overview update task when completed work will materially change project purpose, architecture, directory structure, major commands, or hard constraints.

For `prompt-check`, align behavior with `cmd_inject.py` by scanning all `status: in-progress` task files and emitting every remaining unchecked step, grouped by task title. Preserve current rule-detection behavior and always exit zero. Prepare v1.1.6 by updating version metadata and CHANGELOG after the template and hook behavior changes are covered by tests.

## File Map

- Modify: `src/engaku/templates/ai/overview.md`
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `.github/copilot-instructions.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `src/engaku/cmd_prompt_check.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_prompt_check.py`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `CHANGELOG.md`

## Tasks

- [x] 1. **Strengthen the overview template**
  - Files: `src/engaku/templates/ai/overview.md`, `tests/test_init.py`
  - Steps:
    - Replace the generic placeholder-only overview template with a concise project-memory template.
    - Include sections for project overview, directory structure, Engaku-managed files, constraints, tech stack, and verification commands.
    - Keep all content project-agnostic; do not mention Engaku release history, this repository's Python package layout, or repository-specific commands as defaults.
    - Add or update an init/template assertion that verifies the generated overview contains the Engaku-managed files and verification command sections.
  - Verify: `python -m unittest tests.test_init`

- [x] 2. **Keep overview updates planner-owned**
  - Files: `src/engaku/templates/copilot-instructions.md`, `.github/copilot-instructions.md`, `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`
  - Steps:
    - Remove any global Copilot instruction that tells every agent to update `.ai/overview.md`.
    - Keep or add only the concise global rule telling agents to verify external tool, platform, library, GitHub, or VS Code behavior with documentation or source before relying on it for design decisions.
    - Update both planner agent files so planner does not directly edit overview content as a default behavior; when completed work will materially change project purpose, architecture, directory structure, major commands, or hard constraints, planner must include a concrete overview update task with the exact new text.
    - Do not move planner task formats, reviewer verification protocol, scanner workflow, or coder handoff behavior into global instructions.
    - Keep existing Engaku-specific live instructions in `.github/copilot-instructions.md` intact.
  - Verify: `! grep -n "materially change.*overview.md\|update .ai/overview.md" src/engaku/templates/copilot-instructions.md .github/copilot-instructions.md && grep -n "documentation or source\|overview update task" src/engaku/templates/copilot-instructions.md .github/copilot-instructions.md src/engaku/templates/agents/planner.agent.md .github/agents/planner.agent.md`

- [x] 3. **Align prompt-check with multiple active tasks**
  - Files: `src/engaku/cmd_prompt_check.py`, `tests/test_prompt_check.py`
  - Steps:
    - Replace the single-task lookup with a helper that returns all `status: in-progress` task files in deterministic filename order.
    - Emit unchecked steps for every active task, grouped under each task title.
    - Preserve existing behavior for rule prompts, plain prompts, missing stdin, completed tasks, and the always-zero hook contract.
    - Add a regression test with two in-progress task files proving both task titles and both unchecked steps appear in the `systemMessage`.
  - Verify: `python -m unittest tests.test_prompt_check`

- [x] 4. **Prepare v1.1.6 metadata**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Bump `pyproject.toml` version from `1.1.5` to `1.1.6`.
    - Bump `src/engaku/__init__.py` `__version__` from `1.1.5` to `1.1.6`.
    - Add `## [1.1.6] - 2026-04-27` to `CHANGELOG.md`.
    - Mention the overview template cleanup, planner-owned overview update clarification, external-fact Copilot instruction addition, and multi-active-task `prompt-check` alignment in the changelog entry.
  - Verify: `python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert 'version = \"1.1.6\"' in p; assert '__version__ = \"1.1.6\"' in q" && grep -n "\[1.1.6\]\|overview template\|prompt-check" CHANGELOG.md`

- [x] 5. **Run focused and full verification**
  - Files: `src/engaku/templates/ai/overview.md`, `src/engaku/templates/copilot-instructions.md`, `.github/copilot-instructions.md`, `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`, `src/engaku/cmd_prompt_check.py`, `tests/test_init.py`, `tests/test_prompt_check.py`, `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Run the focused init and prompt-check test modules.
    - Run the full unittest suite.
    - Run the v1.1.6 metadata assertion.
    - Inspect the diff and confirm only template contract cleanup, planner overview ownership clarification, prompt-check behavior, tests, changelog, and version metadata changed.
  - Verify: `python -m unittest tests.test_init tests.test_prompt_check && python -m unittest discover -s tests && python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert 'version = \"1.1.6\"' in p; assert '__version__ = \"1.1.6\"' in q"`

## Out of Scope

- Cleaning the current working tree or generated egg-info files.
- Adding a global rule that tells all agents to edit `.ai/overview.md`.
- Implementing same-turn interactive planner Q&A; current VS Code docs show prompt-file `vscode/askQuestion` and hook/tool approval prompts, but not a general custom-agent pause-and-resume dialogue primitive.
- Changing MCP server defaults, `.vscode/dbhub.toml`, or bundled skill inventory.
- Moving agent-specific protocols into global Copilot instructions.
- Changing reviewer commit behavior or planner/reviewer/scanner ownership boundaries.
- Publishing to PyPI, pushing tags, or running release automation.
