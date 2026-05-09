---
plan_id: 2026-05-09-minimal-dbhub-config-v116
title: v1.1.16 - Minimal DBHub TOML template
status: done
created: 2026-05-09
---

## Background

Engaku currently generates a real DBHub TOML configuration with `[[sources]]`, `[[tools]]`, `DBHUB_DSN`, `readonly = true`, and `max_rows = 1000`. That makes Engaku responsible for DBHub's evolving TOML schema and has started conflicting with the latest DBHub configuration behavior. Upstream DBHub docs keep TOML as the recommended multi-database and advanced-configuration path, but the actual source/tool content belongs to DBHub users. Engaku should keep only the VS Code MCP wiring that starts DBHub with a TOML file.

The planner MCP allocation also has one stale template mismatch: `cmd_init._write_engaku_json`, README, and `tests/test_init.py` grant planner `chrome-devtools/*`, `context7/*`, and `dbhub/*`, while `src/engaku/templates/ai/engaku.json` and this repo's `.ai/engaku.json` list only `context7/*` and `dbhub/*` for planner.

## Design

Use the smallest DBHub contract Engaku can own:

- Keep `.vscode/mcp.json` responsible only for launching `@bytebase/dbhub@latest` with `--transport stdio --config ${workspaceFolder}/.vscode/dbhub.toml`.
- Remove Engaku-owned DBHub DSN input/env wiring from the generated MCP template. Users put credentials and environment interpolation directly in their TOML according to DBHub docs.
- Replace `src/engaku/templates/dbhub.toml` with comment-only guidance and no active `[[sources]]` or `[[tools]]` entries.
- Keep `engaku init --no-mcp` behavior unchanged: it still skips `.vscode/mcp.json`, `.vscode/dbhub.toml`, and MCP skills.
- Keep `engaku update` behavior unchanged except for the new minimal TOML content: if `.vscode/mcp.json` exists and `.vscode/dbhub.toml` is missing, recreate the minimal template; never overwrite an existing user TOML file.
- Update README and the database skill so they no longer describe generated guardrails or `DBHUB_DSN`; instead, they state that Engaku provides TOML wiring and users fill the TOML from DBHub docs.
- Align the bundled and live `engaku.json` planner MCP allocation with runtime behavior: planner gets `chrome-devtools/*`, `context7/*`, and `dbhub/*`.

Rejected alternatives:

- Keep `readonly` and `max_rows` defaults: still requires Engaku to track DBHub TOML details and conflicts with the request to leave template content to users.
- Return to inline `--dsn`: avoids TOML drift but violates the requirement to preserve DBHub's TOML-template path.
- Copy DBHub's full upstream example: high churn, too much generated content, and still duplicates DBHub documentation.

## File Map

- Create: none
- Modify: `src/engaku/templates/mcp.json`
- Modify: `src/engaku/templates/dbhub.toml`
- Modify: `src/engaku/templates/skills/database/SKILL.md`
- Modify: `src/engaku/templates/ai/engaku.json`
- Modify: `.ai/engaku.json`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `.ai/overview.md`
- Delete: none

## Tasks

- [x] 1. **Update DBHub config tests**
  - Files: `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Change the default DBHub TOML init test to assert that `.vscode/dbhub.toml` is created as comment-only guidance.
    - Assert the generated TOML contains `https://dbhub.ai/config/toml` and does not contain active `[[sources]]`, `[[tools]]`, `DBHUB_DSN`, `readonly = true`, or `max_rows = 1000` entries.
    - Change MCP JSON tests to keep the `dbhub` server on `--config ${workspaceFolder}/.vscode/dbhub.toml`, while asserting there is no `--dsn`, no `env.DBHUB_DSN`, and no `db-dsn` input.
    - Keep existing tests that prove `--no-mcp` skips DBHub files and `engaku update` preserves existing `.vscode/dbhub.toml`.
    - Update the missing-DBHub-TOML update test to expect the recreated minimal template content.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 2. **Minimize DBHub templates and docs**
  - Files: `src/engaku/templates/mcp.json`, `src/engaku/templates/dbhub.toml`, `src/engaku/templates/skills/database/SKILL.md`, `README.md`
  - Steps:
    - Remove the `inputs` block and `env.DBHUB_DSN` from the generated MCP template.
    - Keep the generated `dbhub` MCP args as `['-y', '@bytebase/dbhub@latest', '--transport', 'stdio', '--config', '${workspaceFolder}/.vscode/dbhub.toml']`.
    - Replace the DBHub TOML template with concise comment-only guidance that links to `https://dbhub.ai/config/toml` and tells users to add their own `[[sources]]` and optional `[[tools]]` entries.
    - Update the database skill to describe the generated TOML file as user-filled, not as an Engaku guardrail config.
    - Update README generated-file and DBHub sections to remove generated guardrail claims and show only the TOML-backed MCP launch snippet.
  - Verify: `python -m unittest tests.test_init tests.test_update && ! grep -n "DBHUB_DSN\|guardrail/template config\|generates .*readonly = true\|max_rows = 1000" src/engaku/templates/mcp.json src/engaku/templates/dbhub.toml src/engaku/templates/skills/database/SKILL.md README.md`

- [x] 3. **Align planner MCP allocation**
  - Files: `src/engaku/templates/ai/engaku.json`, `.ai/engaku.json`, `tests/test_init.py`
  - Steps:
    - Add `chrome-devtools/*` to the planner `mcp_tools` list in `src/engaku/templates/ai/engaku.json`.
    - Add `chrome-devtools/*` to the planner `mcp_tools` list in this repo's `.ai/engaku.json` so live config matches generated runtime behavior.
    - Keep `cmd_init._write_engaku_json` unchanged unless the tests reveal another mismatch; it already grants planner all three default MCP servers.
    - Keep scanner's MCP list empty and keep Serena absent from every default list.
  - Verify: `python -c "import json; paths=['src/engaku/templates/ai/engaku.json','.ai/engaku.json']; data=[json.load(open(p)) for p in paths]; assert all(d['mcp_tools']['planner'] == ['chrome-devtools/*','context7/*','dbhub/*'] for d in data); assert all(d['mcp_tools'].get('scanner', []) == [] for d in data); assert all('serena/*' not in str(d) for d in data)" && python -m unittest tests.test_init`

- [x] 4. **Bump v1.1.16 metadata**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Bump `pyproject.toml` version from `1.1.15` to `1.1.16`.
    - Bump `src/engaku/__init__.py` `__version__` from `1.1.15` to `1.1.16`.
    - Add `## [1.1.16] - 2026-05-09` under `## [Unreleased]` in `CHANGELOG.md`.
    - Mention the minimal DBHub TOML template, removal of generated DBHub DSN/env/guardrail defaults, and planner MCP allocation template alignment.
  - Verify: `python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert 'version = \"1.1.16\"' in p; assert '__version__ = \"1.1.16\"' in q" && grep -n "\[1.1.16\]\|DBHub\|planner MCP" CHANGELOG.md`

- [x] 5. **Update project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - Append this exact release note to the overview history paragraph after the v1.1.15 sentence: `v1.1.16 reduces the generated DBHub TOML to comment-only guidance and keeps .vscode/mcp.json responsible only for starting dbhub with --config ${workspaceFolder}/.vscode/dbhub.toml, leaving all DBHub source/tool settings to users. It also aligns the bundled engaku.json template and this repo's .ai/engaku.json so planner receives chrome-devtools/*, context7/*, and dbhub/* consistently with init/runtime behavior.`
  - Verify: `grep -n "v1.1.16 reduces the generated DBHub TOML" .ai/overview.md`

- [x] 6. **Run focused and full verification**
  - Files: `src/engaku/templates/mcp.json`, `src/engaku/templates/dbhub.toml`, `src/engaku/templates/skills/database/SKILL.md`, `src/engaku/templates/ai/engaku.json`, `.ai/engaku.json`, `tests/test_init.py`, `tests/test_update.py`, `README.md`, `CHANGELOG.md`, `pyproject.toml`, `src/engaku/__init__.py`, `.ai/overview.md`
  - Steps:
    - Run the focused init/update tests.
    - Run the full stdlib unittest suite.
    - Re-run the v1.1.16 metadata assertion.
    - Inspect the diff and confirm it is limited to DBHub minimal configuration, planner MCP allocation alignment, documentation, tests, overview, changelog, and version metadata.
  - Verify: `python -m unittest tests.test_init tests.test_update && python -m unittest discover -s tests && python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert 'version = \"1.1.16\"' in p; assert '__version__ = \"1.1.16\"' in q"`

## Out of Scope

- Migrating or overwriting existing users' `.vscode/mcp.json` or `.vscode/dbhub.toml` files during `engaku update`.
- Replacing TOML with inline `--dsn` configuration.
- Copying DBHub's full upstream TOML example into Engaku templates.
- Changing bundled MCP server inventory or adding/removing MCP-related skills.
- Changing agent model defaults.
- Publishing to PyPI, pushing tags, or running release automation.
