---
plan_id: 2026-04-28-workflow-to-skill-v118
title: Add Skill Authoring Skill for v1.1.8
status: done
created: 2026-04-28
---

## Background

Repeated agent workflows are becoming common enough that users should be able to
capture them as reusable skills instead of re-explaining the process in every
session. The old `skill-creator-agent-design.md` recommended a dedicated custom
agent, but that is larger than needed for v1.1.8. A smaller bundled
`skill-authoring` skill gives Engaku a practical workflow-to-skill path while
leaving the full skill-creator agent for later.

The concrete motivating case is a planner workflow that reads selected database
tables, uses those findings to inspect code modules, then produces per-module
modification plans. Because the reusable value is the multi-step method rather
than a single fixed prompt, this should be represented as a skill unless the
workflow requires a dedicated role, tool restrictions, or handoffs.

## Design

Add one unconditional bundled skill, `skill-authoring`, copied by both
`engaku init` and `engaku update`. The skill teaches agents to choose the right
customization primitive first, then draft and validate a `SKILL.md` only when a
skill is actually the right fit. See `.ai/docs/2026-04-28-workflow-to-skill-v118.md`
and `.ai/decisions/007-bundle-skill-authoring-skill.md` for the design rationale.

This release should also add `chrome-devtools/*` to planner's default MCP tool
allocation in newly generated `.ai/engaku.json`. Planner increasingly performs
research and design work that may require browser verification, screenshots, or
DevTools-backed inspection before writing plans. Existing projects should remain
user-owned: `engaku update` must not rewrite an existing `.ai/engaku.json` just
to add this default.

The skill must also state an ownership boundary: Engaku manages only its bundled
templates. Skills created by using `skill-authoring` are user-owned workspace or
personal customizations and must not be added to Engaku's template inventory,
`_SKILLS`, `cmd_init.py`, or `cmd_update.py` unless a task explicitly says the
new skill is being shipped as part of Engaku.

## File Map

- Create: `src/engaku/templates/skills/skill-authoring/SKILL.md`
- Create: `.github/skills/skill-authoring/SKILL.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Author skill template**
  - Files: `src/engaku/templates/skills/skill-authoring/SKILL.md`, `.github/skills/skill-authoring/SKILL.md`
  - Steps:
    - Create `SKILL.md` with frontmatter: `name: skill-authoring`, a specific description that mentions turning repeatable workflows into Copilot skills, `argument-hint`, `user-invocable: true`, and `disable-model-invocation: false`.
    - Body sections: Primitive Selection Gate, Prompt File vs Skill Boundary, Interview Checklist, Ownership Boundary, Generated Skill Usage Model, SKILL.md Drafting Rules, Validation Checklist, Test Loop, Escalation to Custom Agent.
    - In Prompt File vs Skill Boundary, say prompt files fit fixed single-command templates; skills fit reusable multi-step methods where later steps depend on earlier findings, such as database-table inspection followed by code-module planning.
    - In Ownership Boundary, say skills authored with this workflow are user-owned and not Engaku-managed by default; do not register them in Engaku's bundled template list unless explicitly shipping an Engaku skill.
    - In Generated Skill Usage Model, say users still provide task-specific inputs each run; the generated skill removes the need to restate phases, safeguards, output format, and stopping rules; durable multi-session run state should be written to user-owned `.ai/docs/` or `.ai/tasks/` files when needed.
    - Include VS Code skill constraints: lowercase hyphenated name, parent directory/name match, description says what and when, referenced resources must use relative links.
    - Keep the live and template copies identical.
  - Verify: `diff src/engaku/templates/skills/skill-authoring/SKILL.md .github/skills/skill-authoring/SKILL.md && head -12 src/engaku/templates/skills/skill-authoring/SKILL.md`

- [x] 2. **Register skill in init**
  - Files: `src/engaku/cmd_init.py`, `tests/test_init.py`
  - Steps:
    - Add `skill-authoring/SKILL.md` to the `cmd_init.py` docstring skill listing.
    - Add `skill-authoring` to the unconditional skill copy loop, not the MCP-only block.
    - Add `.github/skills/skill-authoring/SKILL.md` to `EXPECTED_FILES`.
    - In the `--no-mcp` test, assert `skill-authoring` still exists.
  - Verify: `python -m unittest tests.test_init -v`

- [x] 3. **Add planner chrome-devtools default**
  - Files: `src/engaku/cmd_init.py`, `tests/test_init.py`
  - Steps:
    - In `_write_engaku_json`, add `chrome-devtools/*` to default `mcp_tools.planner` alongside `context7/*` and `dbhub/*` when `no_mcp` is false.
    - Add or update a test that runs default `engaku init`, reads generated `.ai/engaku.json`, and asserts planner has `chrome-devtools/*`, `context7/*`, and `dbhub/*`.
    - Confirm `engaku init --no-mcp` still omits the `mcp_tools` key entirely.
    - Do not add logic to `engaku update` that mutates existing `.ai/engaku.json`; existing user config stays user-owned.
  - Verify: `python -m unittest tests.test_init -v`

- [x] 4. **Register skill in update**
  - Files: `src/engaku/cmd_update.py`, `tests/test_update.py`
  - Steps:
    - Add `skill-authoring` to `_SKILLS`.
    - Add a test asserting `_SKILLS` contains `skill-authoring`.
    - Add a fresh-repo creation test for `.github/skills/skill-authoring/SKILL.md`, following the existing karpathy/brainstorming pattern.
  - Verify: `python -m unittest tests.test_update -v`

- [x] 5. **Update docs and bump 1.1.8**
  - Files: `README.md`, `CHANGELOG.md`, `pyproject.toml`, `src/engaku/__init__.py`
  - Steps:
    - Add a README section or bullet explaining `skill-authoring` as the workflow-to-skill helper and how it differs from VS Code `/create-skill`.
    - Add a README note that new `engaku init` installs `chrome-devtools/*` for planner by default when MCP support is enabled.
    - Add a `## [1.1.8] - 2026-04-28` CHANGELOG entry under Unreleased with the new bundled skill.
    - In the same CHANGELOG entry, note that newly generated planner MCP tool defaults now include `chrome-devtools/*`.
    - Bump `pyproject.toml` and `src/engaku/__init__.py` from `1.1.7` to `1.1.8`.
  - Verify: `python -c "import pathlib; assert '1.1.8' in pathlib.Path('pyproject.toml').read_text(); assert '__version__ = \"1.1.8\"' in pathlib.Path('src/engaku/__init__.py').read_text(); print('OK')"`

- [x] 6. **Update project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - In the overview paragraph, append: `v1.1.8 adds a bundled skill-authoring skill that helps turn repeated workflows into reusable Copilot skills while routing simpler cases to prompts or instructions and larger cases to custom agents. It also gives planner chrome-devtools MCP access by default in newly initialized projects.`
    - In Directory Structure, replace the bundled skills list with: `systematic-debugging, verification-before-completion, frontend-design, proactive-initiative, mcp-builder, doc-coauthoring, brainstorming, karpathy-guidelines, skill-authoring, chrome-devtools, context7, database`.
  - Verify: `grep -q "skill-authoring" .ai/overview.md && echo PASS`

- [x] 7. **Run full verification**
  - Files: none
  - Steps:
    - Run the full unittest suite.
    - Smoke-test `engaku init` in a temporary git repo and confirm `.github/skills/skill-authoring/SKILL.md` exists.
    - In the same `engaku init` smoke test, confirm generated `.ai/engaku.json` gives planner `chrome-devtools/*` when MCP support is enabled.
    - Smoke-test `engaku update` in a temporary git repo and confirm it creates the same skill without rewriting existing `.ai/engaku.json`.
  - Verify: `python -m unittest discover -s tests -v`

## Out of Scope

- Adding `skill-creator.agent.md` or `skill-tester.agent.md`.
- Subagent-based qualitative or quantitative skill evaluation.
- Generating prompt files, hooks, or agents automatically.
- Registering user-authored skills as Engaku-managed bundled skills.
- Adding third-party dependencies or changing hook behavior.
- Shipping PDF, Excel, or document-processing skills.
