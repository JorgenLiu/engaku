---
plan_id: 2026-05-18-add-mcp-command
title: Add curated MCP install commands
status: done
created: 2026-05-18
---

## Background
Engaku currently initializes four MCP servers by default and includes a bundled GitHub skill. GitHub should move out of the default set into explicit MCP onboarding, while the default init should keep only the low-friction core MCPs: chrome-devtools, context7, and dbhub. Users also need a single command that adds supported MCP server recipes, grants selected agents access, and syncs agent frontmatter without hand-editing three files.

## Design
Add two ordinary CLI commands: `engaku list-mcp` and `engaku add-mcp <name>`. The first version supports exactly `github`, `gitlab`, `confluence`, and `jira`; other useful candidates such as Linear, Slack, Notion, Sentry, and Azure DevOps stay out of scope until their MCP server configs and auth conventions are verified. Built-in recipes are Engaku-maintained convenience templates, not authoritative upstream configs; each recipe records `upstream`, `last_verified`, `server`, `tool_wildcard`, `default_agents`, and required env/input hints.

`engaku add-mcp <name>` modifies `.vscode/mcp.json`, `.ai/engaku.json`, and `.github/agents/*.agent.md` in one operation. It merges the recipe into `mcp.json`, appends the recipe `tool_wildcard` to `mcp_tools` for selected agents, then calls `cmd_apply.run(cwd)` to sync each agent `tools:` frontmatter. Default agents: `github` and `gitlab` go to `coder`, `planner`, and `reviewer`; `jira` and `confluence` go to `coder` and `planner`; `scanner` remains empty unless explicitly requested with `--agents scanner`.

Do not create skills by default. The GitHub skill is removed from live and template skills because GitHub becomes an add-on MCP recipe, and Jira/Confluence/GitLab workflows are too organization-specific for bundled generic skills. Keep `context: fork` disabled and do not enable `github.copilot.chat.skillTool.enabled`.

Fix `engaku apply` so it only removes stale Engaku-managed MCP wildcard entries, not every tool ending in `/*`. Today `_update_agent_tools` treats all `/*` entries as MCP entries, which can remove VS Code/default wildcard tools and can fail to append new configured MCP tools consistently. The fix should derive managed MCP server names from `.vscode/mcp.json` plus built-in recipe names and preserve non-MCP slash tools such as `vscode/askQuestions`.

## File Map
- Create: `src/engaku/cmd_add_mcp.py`
- Create: `src/engaku/cmd_list_mcp.py`
- Create: `src/engaku/mcp_recipes.py`
- Create: `src/engaku/templates/mcp-recipes/github.json`
- Create: `src/engaku/templates/mcp-recipes/gitlab.json`
- Create: `src/engaku/templates/mcp-recipes/jira.json`
- Create: `src/engaku/templates/mcp-recipes/confluence.json`
- Create: `tests/test_add_mcp.py`
- Create: `tests/test_list_mcp.py`
- Modify: `src/engaku/cli.py`
- Modify: `src/engaku/cmd_apply.py`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `src/engaku/templates/ai/engaku.json`
- Modify: `src/engaku/templates/mcp.json`
- Modify: `pyproject.toml`
- Modify: `tests/test_apply.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `.ai/overview.md`
- Delete: `src/engaku/templates/skills/github/`
- Delete: `.github/skills/github/`

## Tasks

- [x] 1. **Remove bundled GitHub skill from init/update**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `src/engaku/templates/skills/github/`, `.github/skills/github/`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Delete the GitHub skill template directory and this repo's live generated GitHub skill directory.
    - Remove `github` from the MCP-related skill copy list in `cmd_init.py`.
    - Remove `github` from `_SKILLS` in `cmd_update.py`.
    - Update init/update tests so `github/SKILL.md` is no longer expected or copied.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 2. **Reduce default MCP config to the core three servers**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/templates/ai/engaku.json`, `src/engaku/templates/mcp.json`, `tests/test_init.py`
  - Steps:
    - Remove `github` from the default generated `.vscode/mcp.json` template.
    - Remove `github/*` from default `mcp_tools` in `cmd_init.py` and `templates/ai/engaku.json`.
    - Keep `chrome-devtools/*`, `context7/*`, and `dbhub/*` defaults unchanged for `coder` and `planner`; keep `chrome-devtools/*` and `dbhub/*` for `reviewer`; keep `scanner` empty.
    - Update tests to assert the default MCP list excludes GitHub but keeps the core three.
  - Verify: `python -m unittest tests.test_init`

- [x] 3. **Add MCP recipe catalog**
  - Files: `src/engaku/mcp_recipes.py`, `src/engaku/templates/mcp-recipes/github.json`, `src/engaku/templates/mcp-recipes/gitlab.json`, `src/engaku/templates/mcp-recipes/jira.json`, `src/engaku/templates/mcp-recipes/confluence.json`, `pyproject.toml`
  - Steps:
    - Add a stdlib-only recipe loader that reads bundled JSON recipes from `templates/mcp-recipes/`.
    - Include each recipe's `name`, `description`, `upstream`, `last_verified`, `server`, `tool_wildcard`, `default_agents`, and `notes` fields.
    - Package `templates/mcp-recipes/*.json` in `pyproject.toml` package data.
    - Use env/input placeholders for secrets; do not hardcode tokens.
  - Verify: `python -m unittest tests.test_add_mcp tests.test_list_mcp`

- [x] 4. **Implement `engaku list-mcp`**
  - Files: `src/engaku/cmd_list_mcp.py`, `src/engaku/cli.py`, `tests/test_list_mcp.py`
  - Steps:
    - Register a `list-mcp` subcommand in `cli.py` with lazy import.
    - Print a compact table containing recipe name, default agents, tool wildcard, and description.
    - Return exit code 0 without requiring a git repository.
  - Verify: `python -m unittest tests.test_list_mcp`

- [x] 5. **Implement `engaku add-mcp` merge behavior**
  - Files: `src/engaku/cmd_add_mcp.py`, `src/engaku/cli.py`, `tests/test_add_mcp.py`
  - Steps:
    - Register `add-mcp <name>` in `cli.py` with options `--agents`, `--dry-run`, and `--no-apply`.
    - Validate that the current directory has `.ai/engaku.json`; create `.vscode/mcp.json` if missing.
    - Merge `recipe.server` into `.vscode/mcp.json["servers"]` without overwriting existing same-name server config.
    - Merge `recipe.tool_wildcard` into `.ai/engaku.json["mcp_tools"]` for default or requested agents, preserving order and avoiding duplicates.
    - Unless `--no-apply` is passed, call `cmd_apply.run(cwd)` after writing JSON so `.github/agents/*.agent.md` `tools:` fields are synced.
    - `--dry-run` must print planned changes and leave files unchanged.
  - Verify: `python -m unittest tests.test_add_mcp`

- [x] 6. **Fix `engaku apply` MCP wildcard replacement**
  - Files: `src/engaku/cmd_apply.py`, `tests/test_apply.py`
  - Steps:
    - Change `_update_agent_tools` to remove only stale Engaku-managed MCP wildcard entries, not every `/*` entry.
    - Derive managed server names from configured `.vscode/mcp.json` server keys plus bundled recipe names and existing/default Engaku MCP names.
    - Preserve non-MCP slash tools and unrelated custom tools exactly.
    - Add regression tests showing `github/*` from `.ai/engaku.json` is appended, stale managed MCP wildcards are replaced, and `vscode/askQuestions` or another non-MCP slash tool is preserved.
  - Verify: `python -m unittest tests.test_apply`

- [x] 7. **Cover end-to-end command flow**
  - Files: `tests/test_add_mcp.py`, `tests/test_apply.py`
  - Steps:
    - Add a temp-repo test with `.ai/engaku.json`, `.github/agents/coder.agent.md`, and no `.vscode/mcp.json`.
    - Run `cmd_add_mcp.run(cwd, name="github")` or equivalent test helper.
    - Assert `.vscode/mcp.json` contains `servers.github`, `.ai/engaku.json` contains `github/*`, and the coder/reviewer/planner agent frontmatter contains `github/*` after auto-apply.
  - Verify: `python -m unittest tests.test_add_mcp tests.test_apply`

- [x] 8. **Update overview text**
  - Files: `.ai/overview.md`
  - Steps:
    - Replace the sentence in `## Overview` that says `engaku init` generates four preconfigured MCP servers plus four matching skills with:
      `engaku init now generates .vscode/mcp.json with three low-friction default MCP servers (chrome-devtools, context7, dbhub) and matching bundled skills for chrome-devtools, context7, and database. GitHub, GitLab, Jira, and Confluence are opt-in curated MCP recipes added with engaku add-mcp, while engaku list-mcp lists available recipes.`
    - Replace the `src/engaku/templates/skills/` directory structure bullet so it excludes `github` and says optional service MCP recipes live under `src/engaku/templates/mcp-recipes/`.
    - Remove the separate `src/engaku/templates/skills/github/` bullet.
    - Add a directory structure bullet:
      `src/engaku/templates/mcp-recipes/  Curated add-mcp recipes for optional service MCP servers (github, gitlab, jira, confluence)`
  - Verify: `grep -n "github skill\|four preconfigured\|mcp-recipes\|add-mcp" .ai/overview.md`

- [x] 9. **Bump version to 1.2.0**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Change `[project].version` in `pyproject.toml` from `1.1.18` to `1.2.0`.
    - Change `__version__` in `src/engaku/__init__.py` from `1.1.18` to `1.2.0`.
    - Add a `## [1.2.0] - 2026-05-18` section above `## [1.1.18]` in `CHANGELOG.md` with the following entries:
      - `### Added`: `engaku add-mcp <name> command to install curated MCP server recipes (github, gitlab, jira, confluence) into .vscode/mcp.json, .ai/engaku.json, and agent tool frontmatter.`
      - `### Added`: `engaku list-mcp command to list available built-in MCP recipes.`
      - `### Changed`: `GitHub MCP server removed from default init; now available via engaku add-mcp github. Default init configures chrome-devtools, context7, and dbhub only.`
      - `### Removed`: `Bundled github skill removed; GitHub context is now provided through the GitHub MCP recipe.`
      - `### Fixed`: `engaku apply no longer removes non-MCP slash tools (e.g. vscode/askQuestions) when updating MCP wildcard entries.`
  - Verify: `python -c "import ast; t=open('src/engaku/__init__.py').read(); assert '\"1.2.0\"' in t, t" && grep -n '1.2.0' pyproject.toml CHANGELOG.md`

- [x] 10. **Update README**
  - Files: `README.md`
  - Steps:
    - Replace the MCP server list in the default-init section: remove `github`, keep only `chrome-devtools`, `context7`, `dbhub`.
    - Add a new `## MCP Recipes` section (or equivalent heading that fits the existing README structure) documenting `engaku add-mcp` and `engaku list-mcp`:
      - Usage: `engaku add-mcp <name>` where `<name>` is one of `github`, `gitlab`, `jira`, `confluence`.
      - What it does: merges the recipe server into `.vscode/mcp.json`, appends `tool_wildcard` to `.ai/engaku.json`, and calls `engaku apply` to sync agent frontmatter.
      - Usage: `engaku list-mcp` lists all available built-in recipes with upstream URL and supported agents.
    - Remove any mention of the bundled GitHub skill; update the bundled skills list to reflect the current skill set (no `github` skill).
    - Remove any mention of `setup-serena` or Serena if still present.
  - Verify: `grep -n 'add-mcp\|list-mcp' README.md && ! grep -n 'github.*skill\|skills/github\|setup-serena\|serena' README.md`

- [x] 11. **Run full regression suite**
  - Files: `tests/`
  - Steps:
    - Run the full stdlib unittest suite from repo root.
    - Fix only failures caused by this task's changes.
  - Verify: `python -m unittest`

## Out of Scope
- No bundled Jira, Confluence, or GitLab skills in this version.
- No `context: fork` or `github.copilot.chat.skillTool.enabled` changes.
- No automatic online refresh from upstream MCP docs.
- No write-capable service recipes unless a recipe is explicitly designed and reviewed later.
- No new default MCP servers beyond chrome-devtools, context7, and dbhub.
- No release version bump, changelog entry, or PyPI publishing in this plan.
