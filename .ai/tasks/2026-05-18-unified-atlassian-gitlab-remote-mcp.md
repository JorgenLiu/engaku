---
plan_id: 2026-05-18-unified-atlassian-gitlab-remote-mcp
title: Unify Atlassian recipe and prefer remote GitLab MCP
status: done
created: 2026-05-18
---

## Background
The current MCP recipe catalog has separate `jira` and `confluence` recipes even though the upstream Atlassian MCP server exposes both products through one runtime. That creates duplicate server config and awkward tool routing. Community search found an npx-installable package, `mcp-atlassian@2.1.0`, but it is community-maintained with low adoption compared with `sooperset/mcp-atlassian`; use the upstream `uvx mcp-atlassian` route instead. `@sooperset/mcp-atlassian` is still 404 on npm and must not be used.

GitLab also needs a different default shape. Many organization/self-hosted GitLab setups expose MCP over the GitLab instance URL, e.g. `https://<gitlab.example.com>/api/v4/mcp`, instead of a local stdio npm package. The current `@zereight/mcp-gitlab` stdio recipe should become either a documented fallback or be removed from the default recipe if the hosted/org URL shape is accepted.

## Design
Replace `jira` and `confluence` with one `atlassian` recipe. The recipe should generate one minimal server block named `atlassian`, grant `atlassian/*` to `coder` and `planner` by default, and document that Jira and Confluence env/auth details are user-owned. Use the upstream documented launcher: `command: "uvx"`, `args: ["mcp-atlassian"]`. Do not use the community npm package `mcp-atlassian` as the generated default because adoption is too low, and do not use `@sooperset/mcp-atlassian` because it is not published on npm.

Change GitLab toward a remote organization URL recipe. The minimal generated server should use an HTTP-style URL placeholder for users to edit, matching the requested shape: `https://<gitlab.example.com>/api/v4/mcp`. Implementation must verify VS Code MCP's accepted remote field name for this config (`url` vs `httpUrl`) before editing the recipe. If VS Code `.vscode/mcp.json` requires `url`, use `type: "http"` + `url`; if the GitLab docs/source require `httpUrl`, preserve that field and add tests for it. Keep `@zereight/mcp-gitlab@latest` only as a README fallback, not the primary generated recipe, unless remote GitLab MCP docs cannot be verified.

## File Map
- Create: `src/engaku/templates/mcp-recipes/atlassian.json`
- Modify: `src/engaku/mcp_recipes.py`
- Modify: `src/engaku/templates/mcp-recipes/gitlab.json`
- Modify: `tests/test_add_mcp.py`
- Modify: `tests/test_list_mcp.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.ai/overview.md`
- Delete: `src/engaku/templates/mcp-recipes/jira.json`
- Delete: `src/engaku/templates/mcp-recipes/confluence.json`

## Tasks

- [x] 1. **Verify external MCP config shapes**
  - Files: `src/engaku/templates/mcp-recipes/atlassian.json`, `src/engaku/templates/mcp-recipes/gitlab.json`, `README.md`
  - Steps:
    - Verify upstream `sooperset/mcp-atlassian` docs still show `command: "uvx"`, `args: ["mcp-atlassian"]` for IDE MCP config.
    - Verify `@sooperset/mcp-atlassian` remains unpublished on npm so no scoped npm recipe is reintroduced.
    - Treat community npm package `mcp-atlassian` as a non-default alternative only; do not use it in generated recipe config.
    - Verify GitLab's remote MCP config field for VS Code workspace config: confirm whether the generated recipe should use `httpUrl` exactly or `type: "http"` with `url`.
    - Record the exact evidence as comments in the task implementation notes or PR summary, not in source comments.
  - Verify: `python -c "import urllib.request; text=urllib.request.urlopen('https://raw.githubusercontent.com/sooperset/mcp-atlassian/main/README.md', timeout=20).read().decode('utf-8'); assert '\"command\": \"uvx\"' in text and '\"mcp-atlassian\"' in text" && npm view @sooperset/mcp-atlassian name version bin --json 2>&1 | grep -q '404\|Not Found'`

- [x] 2. **Replace Jira/Confluence recipes with one Atlassian recipe**
  - Files: `src/engaku/mcp_recipes.py`, `src/engaku/templates/mcp-recipes/atlassian.json`, `src/engaku/templates/mcp-recipes/jira.json`, `src/engaku/templates/mcp-recipes/confluence.json`, `tests/test_list_mcp.py`, `tests/test_add_mcp.py`
  - Steps:
    - Change `RECIPE_NAMES` from `("github", "gitlab", "jira", "confluence")` to include `atlassian` and exclude `jira`/`confluence`.
    - Add `atlassian.json` with `name: "atlassian"`, `tool_wildcard: "atlassian/*"`, `default_agents: ["coder", "planner"]`, and server block `command: "uvx"`, `args: ["mcp-atlassian"]`.
    - Delete `jira.json` and `confluence.json`.
    - Update list/add tests so `jira` and `confluence` are unknown recipes and `atlassian` is present.
    - Add a regression test that `engaku add-mcp atlassian` writes exactly one `servers.atlassian` entry and adds only `atlassian/*` to target agents.
  - Verify: `python -m unittest tests.test_list_mcp tests.test_add_mcp`

- [x] 3. **Make GitLab recipe remote-first**
  - Files: `src/engaku/templates/mcp-recipes/gitlab.json`, `tests/test_add_mcp.py`, `tests/test_list_mcp.py`
  - Steps:
    - Replace the local stdio `@zereight/mcp-gitlab@latest` server block with a minimal remote GitLab server block users can edit to their org URL.
    - Use the verified field shape from task 1; expected user-intent target is `https://<gitlab.example.com>/api/v4/mcp`.
    - Keep no `inputs` and no credential env block in the generated recipe.
    - Update tests so GitLab no longer asserts `@zereight/mcp-gitlab@latest` in generated JSON.
    - Add a test that `engaku add-mcp gitlab` writes the placeholder remote URL exactly and does not include `command`, `args`, `env`, or `${input:`.
  - Verify: `python -m unittest tests.test_add_mcp tests.test_list_mcp`

- [x] 4. **Update user-facing docs and release notes**
  - Files: `README.md`, `CHANGELOG.md`, `.ai/overview.md`
  - Steps:
    - Replace all recipe-name lists from `github, gitlab, jira, confluence` to `github, gitlab, atlassian`.
    - Update README MCP examples to show `engaku add-mcp atlassian`, not `jira` or `confluence`.
    - Document Atlassian as one combined Jira+Confluence recipe using upstream `sooperset/mcp-atlassian` via `uvx mcp-atlassian`.
    - Document GitLab as remote-first using `https://<gitlab.example.com>/api/v4/mcp`, with `@zereight/mcp-gitlab@latest` only as an optional local fallback if retained.
    - Add CHANGELOG Unreleased entries for recipe rename/removal, upstream `uvx mcp-atlassian`, and remote-first GitLab.
    - Update `.ai/overview.md` to state optional recipes are `github`, `gitlab`, and `atlassian`.
  - Verify: `grep -n 'jira\|confluence\|atlassian\|@zereight\|api/v4/mcp' README.md CHANGELOG.md .ai/overview.md`

- [x] 5. **Run focused regression suite**
  - Files: `tests/`
  - Steps:
    - Run all MCP-related tests after recipe renames and docs updates.
    - Fix only failures caused by this plan.
  - Verify: `python -m unittest tests.test_add_mcp tests.test_list_mcp tests.test_init tests.test_update`

- [x] 6. **Bump version to 1.2.1**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Change `[project].version` in `pyproject.toml` from `1.2.0` to `1.2.1`.
    - Change `__version__` in `src/engaku/__init__.py` from `"1.2.0"` to `"1.2.1"`.
    - Promote the `## [Unreleased]` section in `CHANGELOG.md` to `## [1.2.1] - 2026-05-18` above `## [1.2.0]`.
  - Verify: `python -c "import ast; t=open('src/engaku/__init__.py').read(); assert '\"1.2.1\"' in t" && grep -n '1.2.1' pyproject.toml CHANGELOG.md`

## Out of Scope
- No default MCP server changes in `engaku init`.
- No credential prompts, `inputs`, or generated token env blocks.
- No automatic migration of users' existing `jira` or `confluence` entries in `.vscode/mcp.json`.
- No new hosted Atlassian service unless verified separately.
- No runtime network checks inside Engaku.