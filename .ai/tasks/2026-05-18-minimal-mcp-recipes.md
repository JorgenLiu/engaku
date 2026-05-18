---
plan_id: 2026-05-18-minimal-mcp-recipes
title: Simplify MCP recipe configuration
status: done
created: 2026-05-18
---

## Background
`engaku add-mcp` currently copies recipe `server` blocks directly into `.vscode/mcp.json`. GitLab, Jira, and Confluence recipes include `${input:...}` env placeholders, which makes generated MCP config too opinionated and prompts users for details Engaku should not own. Verification also showed two recipe package specs are invalid on npm: `@sooperset/mcp-atlassian@latest` and `@gitlab-org/mcp-server-gitlab@latest` both return 404, while upstream Atlassian docs recommend `uvx mcp-atlassian`.

## Design
Keep generated MCP recipe config minimal: `engaku add-mcp <name>` should add only the smallest server block needed to launch or connect, and leave tokens, URLs, toolsets, and enterprise/self-hosted details for users to fill in manually. Recipe `notes` and README should explain required user edits, but recipes should not inject `${input:...}` variables or credential-shaped env blocks.

For Jira and Confluence, replace the invalid scoped npm package with the upstream documented launcher: `command: "uvx"`, `args: ["mcp-atlassian"]`. Use one shared Atlassian server runtime per recipe for now, but keep separate recipe names and tool wildcards because agent tool routing is per MCP server name. For GitLab, replace the invalid `@gitlab-org/mcp-server-gitlab@latest` package with the verified npm package `@zereight/mcp-gitlab@latest`, but omit env variables from the recipe so users can supply auth details themselves. `%2f` in npm logs is the slash in scoped package registry URLs, not JSON escaping by Engaku; removing invalid scoped Atlassian specs avoids the observed bad path there, while tests should assert Engaku writes exact args strings.

No `add-mcp` merge behavior change is needed unless tests expose serialization drift. The root fix is recipe data and docs.

## File Map
- Modify: `src/engaku/templates/mcp-recipes/gitlab.json`
- Modify: `src/engaku/templates/mcp-recipes/jira.json`
- Modify: `src/engaku/templates/mcp-recipes/confluence.json`
- Modify: `tests/test_add_mcp.py`
- Modify: `tests/test_list_mcp.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Make service recipes minimal**
  - Files: `src/engaku/templates/mcp-recipes/gitlab.json`, `src/engaku/templates/mcp-recipes/jira.json`, `src/engaku/templates/mcp-recipes/confluence.json`
  - Steps:
    - Remove all `server.env` entries containing `${input:...}` from GitLab, Jira, and Confluence recipes.
    - Change GitLab `server.args` to `["-y", "@zereight/mcp-gitlab@latest"]`.
    - Change Jira and Confluence server launchers to `command: "uvx"` and `args: ["mcp-atlassian"]`.
    - Update each recipe `notes` field to say the generated config is intentionally minimal and users must add auth/URL/env details in `.vscode/mcp.json` or their shell environment.
  - Verify: `python -m unittest tests.test_list_mcp`

- [x] 2. **Add recipe regression coverage**
  - Files: `tests/test_add_mcp.py`, `tests/test_list_mcp.py`
  - Steps:
    - Add assertions that GitLab, Jira, and Confluence recipe `server` objects do not contain an `env` key by default.
    - Add assertions that Jira and Confluence use `uvx` with `args == ["mcp-atlassian"]`.
    - Add an `add-mcp gitlab` write test asserting `.vscode/mcp.json` preserves the exact string `@zereight/mcp-gitlab@latest` in `servers.gitlab.args`.
    - Add an `add-mcp jira` or `add-mcp confluence` write test asserting no `%2f` or invalid `@sooperset/mcp-atlassian@latest` string appears in generated JSON.
  - Verify: `python -m unittest tests.test_add_mcp tests.test_list_mcp`

- [x] 3. **Update README MCP recipe guidance**
  - Files: `README.md`
  - Steps:
    - Rewrite the `## MCP Recipes` examples so GitLab/Jira/Confluence are described as minimal starter configs, not complete credential-aware installs.
    - State that Engaku does not generate `inputs` or credential env blocks for optional recipes; users add tokens, URLs, enterprise hosts, and toolsets themselves.
    - Update the GitLab package mention to `@zereight/mcp-gitlab@latest` if the package name is documented.
    - Update Jira/Confluence docs to mention upstream `mcp-atlassian` via `uvx` and required user-provided Atlassian auth variables.
  - Verify: `grep -n 'input\|@sooperset\|@gitlab-org\|@zereight\|mcp-atlassian\|minimal' README.md`

- [x] 4. **Record release notes and overview update**
  - Files: `CHANGELOG.md`, `.ai/overview.md`
  - Steps:
    - Add an `## [Unreleased]` entry under `### Changed`: `Optional MCP recipes now generate minimal server blocks without credential input placeholders; users own tokens, URLs, and service-specific env details.`
    - Add an `## [Unreleased]` entry under `### Fixed`: `Jira and Confluence recipes now use upstream `uvx mcp-atlassian` instead of the invalid npm package `@sooperset/mcp-atlassian@latest`; GitLab now uses the verified npm package `@zereight/mcp-gitlab@latest` instead of `@gitlab-org/mcp-server-gitlab@latest`.`
    - Replace the `.ai/overview.md` sentence `GitHub, GitLab, Jira, and Confluence are opt-in curated MCP recipes installed via `engaku add-mcp <name>`; `engaku list-mcp` lists available recipes.` with: `GitHub, GitLab, Jira, and Confluence are opt-in curated MCP recipes installed via `engaku add-mcp <name>`; optional service recipes intentionally generate minimal server blocks and leave credentials, URLs, and enterprise details for users to fill in.`
  - Verify: `grep -n 'minimal server blocks\|@sooperset\|@gitlab-org\|@zereight\|uvx mcp-atlassian' CHANGELOG.md .ai/overview.md`

- [x] 5. **Run focused regression suite**
  - Files: `tests/`
  - Steps:
    - Run the MCP and init tests after recipe/doc updates.
    - Fix only failures caused by this plan.
  - Verify: `python -m unittest tests.test_add_mcp tests.test_list_mcp tests.test_init`

## Out of Scope
- No new MCP recipe names.
- No automatic prompting for service credentials.
- No `.vscode/mcp.json` `inputs` generation for optional recipes.
- No online recipe refresh or registry lookup inside Engaku runtime.
- No change to default `engaku init` MCP servers beyond recipe documentation.