---
plan_id: 2026-04-29-remove-serena-and-agent-schema-fixes
title: Remove Serena defaults and fix agent schema compatibility
status: done
created: 2026-04-29
---

## Background
Serena currently fails to spawn when VS Code cannot find a `serena` executable, and `serena-agent` is not Python 3.8 compatible. Engaku should not default to a tool that requires a separate Python 3.11+ runtime while the CLI promises Python >=3.8 and stdlib-only operation. Copilot CLI also reports `.github/agents/coder.agent.md` as malformed because Engaku writes `model` as an array, and VS Code reports `selection` as an unknown tool.

## Design
This plan removes Serena from the current generated product surface instead of trying to repair its installer. The removal applies to live dogfood config, bundled templates, CLI wiring, tests, and user docs; historical completed task docs, ADRs, and `build/` artifacts are archival and out of scope.

Agent frontmatter should follow the stricter GitHub custom agents configuration schema for cross-environment compatibility. The GitHub reference says `model` is a string for GitHub.com, Copilot CLI, and supported IDEs, while the VS Code custom agents page allows either a string or array. Use a single YAML string everywhere because it satisfies the stricter Copilot CLI validator and remains acceptable in VS Code.

Related decision: `.ai/decisions/012-remove-default-serena-and-strict-agent-frontmatter.md`.

## File Map
- Delete: `src/engaku/cmd_setup_serena.py`
- Delete: `tests/test_setup_serena.py`
- Delete: `src/engaku/templates/skills/serena/SKILL.md`
- Delete: `.github/skills/serena/SKILL.md`
- Modify: `src/engaku/cli.py`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `src/engaku/cmd_apply.py`
- Modify: `src/engaku/templates/mcp.json`
- Modify: `.vscode/mcp.json`
- Modify: `src/engaku/templates/ai/engaku.json`
- Modify: `.ai/engaku.json`
- Modify: `src/engaku/templates/agents/coder.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/scanner.agent.md`
- Modify: `.github/agents/coder.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `.github/agents/scanner.agent.md`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `tests/test_apply.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Remove Serena setup command path**
  - Files: `src/engaku/cmd_setup_serena.py`, `tests/test_setup_serena.py`, `src/engaku/cli.py`, `src/engaku/cmd_init.py`, `tests/test_init.py`
  - Steps:
    - Delete `src/engaku/cmd_setup_serena.py` and `tests/test_setup_serena.py`.
    - Remove the `setup-serena` subcommand from `src/engaku/cli.py`.
    - Remove `--skip-serena-setup` from `init` argument parsing and from the `cmd_init.run()` signature.
    - Remove the default Serena setup call at the end of `cmd_init.run()`.
    - Update init tests to stop passing or asserting `skip_serena_setup` behavior.
  - Verify: `python -m unittest tests.test_init && ! rg -n "setup-serena|skip_serena_setup|cmd_setup_serena" src tests`

- [x] 2. **Remove Serena generated assets**
  - Files: `src/engaku/templates/skills/serena/SKILL.md`, `.github/skills/serena/SKILL.md`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Delete the live and template Serena skill files.
    - Remove `serena` from the MCP-related skill list copied by `engaku init`.
    - Remove `serena` from the `_SKILLS` inventory used by `engaku update`.
    - Delete or rewrite tests that assert Serena skill creation/restoration.
  - Verify: `python -m unittest tests.test_init tests.test_update && ! test -e src/engaku/templates/skills/serena/SKILL.md && ! test -e .github/skills/serena/SKILL.md`

- [x] 3. **Remove Serena MCP and tool assignments**
  - Files: `src/engaku/templates/mcp.json`, `.vscode/mcp.json`, `src/engaku/templates/ai/engaku.json`, `.ai/engaku.json`, `src/engaku/cmd_init.py`, `tests/test_init.py`, `tests/test_update.py`, `tests/test_apply.py`
  - Steps:
    - Remove the `serena` server block from template and live `.vscode/mcp.json` files.
    - Remove `serena/*` from template and live `.ai/engaku.json` MCP tool assignments.
    - Update `_write_engaku_json()` defaults in `cmd_init.py` so fresh projects do not include `serena/*`.
    - Remove tests that assert Serena MCP server merging or Serena wildcard restoration.
    - Add assertions that generated MCP config and agent tool lists do not include Serena.
  - Verify: `python -m unittest tests.test_init tests.test_update tests.test_apply && python -c 'import json; [json.load(open(p)) for p in ("src/engaku/templates/mcp.json", ".vscode/mcp.json", "src/engaku/templates/ai/engaku.json", ".ai/engaku.json")]' && ! rg -n "serena" src/engaku/templates/mcp.json .vscode/mcp.json src/engaku/templates/ai/engaku.json .ai/engaku.json src/engaku/cmd_init.py tests/test_init.py tests/test_update.py tests/test_apply.py`

- [x] 4. **Render model frontmatter as strings**
  - Files: `src/engaku/cmd_apply.py`, `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`, `tests/test_apply.py`
  - Steps:
    - Change `_update_agent_model()` to render `model` as a single YAML string, for example `model: "Claude Sonnet 4.6 (copilot)"`.
    - Update live `.github/agents/*.agent.md` files so each `model` value is a string, not `['...']`.
    - Update apply tests that currently expect `model: ['...']` so they expect string-valued frontmatter.
    - Add a regression assertion that no live agent file contains `model: [`.
  - Verify: `python -m unittest tests.test_apply && ! rg -n "^model:\s*\[" .github/agents tests/test_apply.py src/engaku/cmd_apply.py`

- [x] 5. **Remove unknown selection tool**
  - Files: `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/scanner.agent.md`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Remove `selection` from coder, planner, and scanner live agent tool lists.
    - Remove `selection` from coder, planner, and scanner template tool lists.
    - Preserve the remaining accepted VS Code/Copilot tools: `read/problems`, `search/changes`, `search/codebase`, `search/usages`, and `vscode/askQuestions`.
    - Update tests that listed `selection` as a required default tool.
    - Add a regression assertion that generated and live agent frontmatter does not contain `selection`.
  - Verify: `python -m unittest tests.test_init tests.test_update && ! rg -n "['\"]selection['\"]" src/engaku/templates/agents .github/agents tests/test_init.py tests/test_update.py`

- [x] 6. **Update coder description**
  - Files: `src/engaku/templates/agents/coder.agent.md`, `.github/agents/coder.agent.md`
  - Steps:
    - Replace `maintains knowledge after each task` with wording that matches current boundaries, for example `executes implementation tasks and updates task checkboxes`.
    - Keep coder ownership limited to implementation work and completed checkbox ticks; do not grant status, plan restructuring, ADR, or docs ownership.
  - Verify: `! rg -n "maintains knowledge|knowledge after each task" src/engaku/templates/agents/coder.agent.md .github/agents/coder.agent.md && rg -n "updates task checkboxes" src/engaku/templates/agents/coder.agent.md .github/agents/coder.agent.md`

- [x] 7. **Refresh docs and overview**
  - Files: `README.md`, `CHANGELOG.md`, `.ai/overview.md`
  - Steps:
    - Remove `setup-serena`, Serena MCP, Serena skill, and Python 3.13/uv Serena installation guidance from `README.md`.
    - Update README MCP text so the default servers are only Chrome DevTools, Context7, and DBHub.
    - Update `CHANGELOG.md` to describe this current-version correction: remove default Serena integration, remove unknown `selection`, and fix custom agent `model` frontmatter to a string.
    - In `.ai/overview.md`, replace any sentence claiming v1.1.10 adds default Serena setup with: `v1.1.10 keeps token budgeting as an always-on generated instruction and removes default Serena setup to preserve Python 3.8 compatibility and avoid MCP spawn failures.`
  - Verify: `! rg -n "Serena|serena|setup-serena|serena-agent|Python 3.13" README.md CHANGELOG.md .ai/overview.md && rg -n "Chrome DevTools|Context7|DBHub|model" README.md CHANGELOG.md .ai/overview.md`

- [x] 8. **Run full compatibility verification**
  - Files: `src/engaku/cli.py`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `src/engaku/cmd_apply.py`, `src/engaku/templates/mcp.json`, `.vscode/mcp.json`, `src/engaku/templates/ai/engaku.json`, `.ai/engaku.json`, `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`, `tests/test_init.py`, `tests/test_update.py`, `tests/test_apply.py`, `README.md`, `CHANGELOG.md`, `.ai/overview.md`
  - Steps:
    - Run the full unittest suite.
    - Parse all touched JSON files.
    - Search current-version source, tests, templates, live config, README, CHANGELOG, and overview for forbidden Serena references.
    - Search live/template agents for `selection` and array-valued `model` frontmatter.
    - Inspect the final diff for accidental edits to historical task docs, ADRs, or `build/` artifacts.
  - Verify: `python -m unittest discover -s tests && python -c 'import json; [json.load(open(p)) for p in ("src/engaku/templates/mcp.json", ".vscode/mcp.json", "src/engaku/templates/ai/engaku.json", ".ai/engaku.json")]' && ! rg -n "serena|Serena|setup-serena|serena-agent" src tests README.md CHANGELOG.md .ai/overview.md .github/agents .github/skills .vscode/mcp.json .ai/engaku.json -g '!src/engaku/templates/skills/token-budget/SKILL.md' && ! rg -n "['\"]selection['\"]|^model:\s*\[" src/engaku/templates/agents .github/agents && git diff --stat`

## Out of Scope
- Rewriting historical `.ai/tasks/*.md`, `.ai/decisions/*.md`, or older analysis docs that mention Serena as past context.
- Editing generated `build/` artifacts.
- Replacing Serena with a different symbol-level MCP server in this task.
- Adding a new optional Serena installer or MCP profile.
- Changing generated model names or introducing model fallback arrays.