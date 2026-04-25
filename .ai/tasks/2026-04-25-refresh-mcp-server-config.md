---
plan_id: 2026-04-25-refresh-mcp-server-config
title: Refresh MCP server configuration and hook runtime
status: done
created: 2026-04-25
---

## Background

Engaku's default MCP integration is structurally sound, but current DBHub upstream documentation has moved beyond the template shipped in v1.1.0. The DBHub VS Code examples now explicitly use `type: stdio`, `--transport stdio`, password-protected input variables, and TOML for advanced guardrails such as read-only mode and max rows. v1.1.4 should make that TOML path first-class by generating a `dbhub.toml` template and having `.vscode/mcp.json` reference it directly, while still preserving a password-protected DSN prompt through environment interpolation. A GitHub search also found useful optional MCP servers, especially GitHub MCP and Firecrawl, but they are not good default additions because they require authentication, introduce broad permissions, or overlap with existing VS Code/Engaku capabilities. v1.1.4 should also fix hook portability for machines where `engaku` only works through a virtual environment Python: today generated hooks call the default `engaku` executable, so permission or PATH issues in the system Python can break every hook.

## Design

Keep Engaku's default MCP set to Chrome DevTools, Context7, and DBHub. DBHub should be TOML-first: `engaku init` generates `.vscode/dbhub.toml`, and the DBHub server in `.vscode/mcp.json` uses `--config ${workspaceFolder}/.vscode/dbhub.toml` instead of passing `--dsn` directly. The MCP input `db-dsn` remains password-protected, and `.vscode/mcp.json` passes it as `DBHUB_DSN` so the TOML template can use `dsn = "${DBHUB_DSN}"`. The template should be conservative: one `default` source, `lazy = true`, and `execute_sql` configured with `readonly = true` and `max_rows = 1000`. Update the database skill/README to present this generated TOML template as the default path and reserve inline DSN configuration for advanced manual overrides.

Tasks 1-7 were completed against the earlier `--dsn` design. Tasks 8-11 supersede the DBHub default shape with the TOML-first design before the remaining hook runtime work continues. Add optional MCP server recipes to the README, with GitHub MCP as the primary recommendation and Firecrawl as a secondary web-research recipe, without adding them to generated `.vscode/mcp.json`.

Add a top-level `python` option to `.ai/engaku.json`. When `python` is missing, `null`, or empty, generated hook commands keep the current default form (`engaku inject`, `engaku prompt-check`, `engaku task-review`), which preserves the default system/PATH behavior. When `python` is set, `engaku apply` rewrites Engaku hook commands in `.github/agents/*.agent.md` to call the configured interpreter with `-m engaku`, for example `.venv/bin/python -m engaku inject`. Relative interpreter paths are resolved by the shell from the workspace directory; absolute paths are also allowed. The implementation should only rewrite Engaku-managed hook commands and should leave unrelated custom hook commands alone.

Longer analysis is recorded in `.ai/docs/2026-04-25-mcp-server-research.md`.

## File Map

- Create: `src/engaku/templates/dbhub.toml`
- Modify: `src/engaku/templates/mcp.json`
- Modify: `src/engaku/templates/ai/engaku.json`
- Modify: `src/engaku/templates/skills/database/SKILL.md`
- Modify: `.github/skills/database/SKILL.md`
- Modify: `.ai/engaku.json`
- Modify: `.ai/overview.md`
- Modify: `README.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `src/engaku/cmd_apply.py`
- Modify: `src/engaku/utils.py`
- Modify: `tests/test_apply.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `CHANGELOG.md`

## Tasks

- [x] 1. **Update DBHub MCP template**
  - Files: `src/engaku/templates/mcp.json`
  - Steps:
    - Change the DBHub input id from `dbDsn` to `db-dsn`.
    - Add `"password": true` to the DBHub input.
    - Add `"type": "stdio"` to the DBHub server entry.
    - Change DBHub args to include `"-y"`, `"--transport"`, `"stdio"`, `"--dsn"`, and `"${input:db-dsn}"`.
    - Remove wording that says an empty DSN skips DBHub.
  - Verify: `python -c 'import json; data=json.load(open("src/engaku/templates/mcp.json")); db=data["servers"]["dbhub"]; assert db["type"]=="stdio"; assert "-y" in db["args"]; assert "--transport" in db["args"]; assert "${input:db-dsn}" in db["args"]; assert data["inputs"][0]["password"] is True'`

- [x] 2. **Refresh database skill**
  - Files: `src/engaku/templates/skills/database/SKILL.md`, `.github/skills/database/SKILL.md`
  - Steps:
    - Update both live and template skill files identically.
    - Replace `--row-limit` with the upstream TOML `max_rows` setting.
    - Explain that command-line `--readonly` / `--max-rows` are deprecated in upstream docs and TOML is preferred for guardrails.
    - Add a short `dbhub.toml` example with `[[sources]]`, `[[tools]]`, `readonly = true`, and `max_rows = 1000`.
    - Keep the existing `search_objects` before `execute_sql` workflow.
  - Verify: `cmp src/engaku/templates/skills/database/SKILL.md .github/skills/database/SKILL.md && grep -n "max_rows\|dbhub.toml\|search_objects" src/engaku/templates/skills/database/SKILL.md`

- [x] 3. **Update README DBHub docs**
  - Files: `README.md`
  - Steps:
    - Update the DBHub JSON snippet to include `type: stdio`, `-y`, `--transport stdio`, `--dsn`, and `${input:db-dsn}`.
    - Update the input-variable description to say the DSN prompt is password protected.
    - Add a short note that `dbhub.toml` is recommended for multi-database setups, read-only mode, max row limits, timeouts, SSL, SSH, and custom tools.
    - Remove or correct any `--row-limit` wording if present.
  - Verify: `grep -n "db-dsn\|--transport\|dbhub.toml\|max_rows" README.md`

- [x] 4. **Document optional MCP recipes**
  - Files: `README.md`
  - Steps:
    - Add a subsection after default MCP servers named `Optional MCP Servers`.
    - Add GitHub MCP as the primary optional recipe with remote HTTP config `https://api.githubcopilot.com/mcp/` and a note about OAuth/PAT, toolsets, and read-only mode.
    - Add Firecrawl MCP as a secondary optional recipe with `npx -y firecrawl-mcp`, `FIRECRAWL_API_KEY` input, and a note that it is for structured web search/scraping, not a default dependency.
    - State that these optional recipes are not generated by `engaku init`.
  - Verify: `grep -n "Optional MCP Servers\|api.githubcopilot.com/mcp\|firecrawl-mcp" README.md`

- [x] 5. **Strengthen init tests**
  - Files: `tests/test_init.py`
  - Steps:
    - Extend `test_mcp_json_is_valid` to assert DBHub has `type == "stdio"`.
    - Assert the DBHub args include `-y`, `--transport`, `stdio`, and `${input:db-dsn}`.
    - Assert the DBHub input has `id == "db-dsn"` and `password is True`.
  - Verify: `python -m unittest tests.test_init`

- [x] 6. **Strengthen update tests**
  - Files: `tests/test_update.py`
  - Steps:
    - Update any expected DBHub input id from `dbDsn` to `db-dsn`.
    - Extend the MCP merge test to ensure missing inputs are merged by id and the DBHub server shape is preserved.
  - Verify: `python -m unittest tests.test_update`

- [x] 7. **Add hook Python config defaults**
  - Files: `src/engaku/templates/ai/engaku.json`, `.ai/engaku.json`, `src/engaku/cmd_init.py`, `src/engaku/utils.py`, `tests/test_init.py`
  - Steps:
    - Add a top-level `python` key with value `null` to the bundled `engaku.json` template.
    - Update `_write_engaku_json()` so fresh `engaku init` output includes `python: null` in both default and `--no-mcp` modes.
    - Update `load_config()` so returned config includes a `python` default of `None` when the key is absent, invalid, or empty.
    - Update this repo's `.ai/engaku.json` to include `python: null` without changing model or MCP tool choices.
    - Extend init tests to assert the key is present and `None` for both default init and `--no-mcp` init.
  - Verify: `python -m unittest tests.test_init && python -c "from engaku.utils import load_config; c=load_config('.'); assert 'python' in c"`

- [x] 8. **Add DBHub TOML template**
  - Files: `src/engaku/templates/dbhub.toml`
  - Steps:
    - Create a bundled TOML template for the generated DBHub MCP server.
    - Add one `[[sources]]` entry with `id = "default"`, `dsn = "${DBHUB_DSN}"`, and `lazy = true`.
    - Add one `[[tools]]` entry for `name = "execute_sql"`, `source = "default"`, `readonly = true`, and `max_rows = 1000`.
    - Keep the template credential-free; users provide the DSN through the password-protected MCP input.
  - Verify: `grep -n "DBHUB_DSN\|readonly = true\|max_rows = 1000" src/engaku/templates/dbhub.toml`

- [x] 9. **Reference DBHub TOML from MCP template**
  - Files: `src/engaku/templates/mcp.json`
  - Steps:
    - Keep the password-protected `db-dsn` input.
    - Change DBHub args to use `"--config"` and `"${workspaceFolder}/.vscode/dbhub.toml"` instead of `"--dsn"` and `"${input:db-dsn}"`.
    - Add an `env` entry mapping `DBHUB_DSN` to `${input:db-dsn}` so the TOML template can interpolate it.
    - Keep `"type": "stdio"`, `"-y"`, and `"--transport", "stdio"` in the server entry.
  - Verify: `python -c 'import json; data=json.load(open("src/engaku/templates/mcp.json")); db=data["servers"]["dbhub"]; assert db["type"]=="stdio"; assert "--config" in db["args"]; assert "${workspaceFolder}/.vscode/dbhub.toml" in db["args"]; assert "--dsn" not in db["args"]; assert db["env"]["DBHUB_DSN"]=="${input:db-dsn}"; assert data["inputs"][0]["password"] is True'`

- [x] 10. **Copy DBHub TOML during init and update**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Update `engaku init` so default MCP setup creates `.vscode/dbhub.toml` from `src/engaku/templates/dbhub.toml`.
    - Ensure `engaku init --no-mcp` skips `.vscode/dbhub.toml` just as it skips `.vscode/mcp.json` and MCP skills.
    - Update `engaku update` so repositories that already have `.vscode/mcp.json` also receive `.vscode/dbhub.toml` if it is missing.
    - Preserve an existing `.vscode/dbhub.toml`; do not overwrite user-edited TOML.
    - Add init and update tests for created, skipped, and preserved TOML behavior.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 11. **Update DBHub docs and tests for TOML default**
  - Files: `README.md`, `src/engaku/templates/skills/database/SKILL.md`, `.github/skills/database/SKILL.md`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Update the README DBHub JSON snippet to show `--config ${workspaceFolder}/.vscode/dbhub.toml` plus `env.DBHUB_DSN = ${input:db-dsn}`.
    - Explain that generated Engaku projects use `.vscode/dbhub.toml` as the editable DBHub template and keep secrets in the password-protected MCP input.
    - Update both database skill files identically so the default workflow points to `.vscode/dbhub.toml`, with inline `--dsn` documented only as a manual override.
    - Update MCP-related init/update tests so they assert the final DBHub default is TOML-backed rather than direct `--dsn`.
  - Verify: `cmp src/engaku/templates/skills/database/SKILL.md .github/skills/database/SKILL.md && grep -n "dbhub.toml\|DBHUB_DSN\|--config" README.md src/engaku/templates/skills/database/SKILL.md && python -m unittest tests.test_init tests.test_update`

- [x] 12. **Render hook commands from config**
  - Files: `src/engaku/cmd_apply.py`, `tests/test_apply.py`
  - Steps:
    - Add a helper that renders `engaku <subcommand>` when `config['python']` is unset and renders `<quoted-python> -m engaku <subcommand>` when it is set.
    - Quote configured interpreter paths with standard-library shell quoting so paths containing spaces are safe.
    - Add a helper that updates Engaku-managed `command:` lines under `hooks:` for `inject`, `prompt-check`, and `task-review`.
    - Rewrite matching commands in every existing `.github/agents/*.agent.md`, not only agents listed under `agents`, so runtime-only config still works.
    - Leave custom non-Engaku hook commands unchanged.
  - Verify: `python -m unittest tests.test_apply`

- [x] 13. **Test hook runtime overrides**
  - Files: `tests/test_apply.py`
  - Steps:
    - Add a test that missing or `null` `python` keeps commands such as `command: engaku inject` unchanged.
    - Add a test that `python: .venv/bin/python` rewrites Engaku hook commands to `.venv/bin/python -m engaku <subcommand>`.
    - Add a test that an absolute interpreter path with spaces is quoted and still uses `-m engaku`.
    - Add a test that a custom hook command, such as `npm run custom-hook`, is preserved.
  - Verify: `python -m unittest tests.test_apply`

- [x] 14. **Reapply hook runtime after update**
  - Files: `tests/test_update.py`
  - Steps:
    - Add a test where `engaku update` overwrites agent templates, then auto-applies an `.ai/engaku.json` with `python: .venv/bin/python`.
    - Assert the restored coder agent contains `.venv/bin/python -m engaku inject` and `.venv/bin/python -m engaku prompt-check` after update.
    - Keep existing update behavior unchanged for repos without `.ai/engaku.json`.
  - Verify: `python -m unittest tests.test_update`

- [x] 15. **Document hook Python option**
  - Files: `README.md`
  - Steps:
    - Add a short configuration example showing `python` in `.ai/engaku.json`.
    - Explain that unset or `null` uses the default `engaku` command on PATH.
    - Explain that setting a virtual environment interpreter makes hooks run as `.venv/bin/python -m engaku <subcommand>`.
    - Tell users to run `.venv/bin/python -m engaku apply` after changing this setting if the default `engaku` command is already broken.
  - Verify: `grep -n '"python"\|venv/bin/python\|engaku apply' README.md`

- [x] 16. **Update project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - Add this exact sentence to the end of the Overview paragraph: `v1.1.4 adds a generated DBHub TOML template referenced from .vscode/mcp.json, plus a configurable hook Python interpreter via .ai/engaku.json: when python is set, engaku apply rewrites Engaku hook commands to use that interpreter with -m engaku.`
  - Verify: `grep -n "configurable hook Python interpreter" .ai/overview.md`

- [x] 17. **Bump version to 1.1.4**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Change `pyproject.toml` version from `1.1.3` to `1.1.4`.
    - Change `src/engaku/__init__.py` `__version__` from `1.1.3` to `1.1.4`.
    - Add `## [1.1.4] - 2026-04-25` to `CHANGELOG.md` with `Added` for configurable hook Python and generated DBHub TOML, and `Changed` for TOML-backed DBHub MCP defaults/docs.
  - Verify: `python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert 'version = \"1.1.4\"' in p; assert '__version__ = \"1.1.4\"' in q" && grep -n "\[1.1.4\]" CHANGELOG.md`

- [x] 18. **Run full verification**
  - Files: `src/engaku/templates/dbhub.toml`, `src/engaku/templates/mcp.json`, `src/engaku/templates/ai/engaku.json`, `src/engaku/templates/skills/database/SKILL.md`, `.github/skills/database/SKILL.md`, `.ai/engaku.json`, `.ai/overview.md`, `README.md`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `src/engaku/cmd_apply.py`, `src/engaku/utils.py`, `tests/test_apply.py`, `tests/test_init.py`, `tests/test_update.py`, `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Run the full stdlib unittest suite.
    - Run the JSON template parse check and grep the TOML template for the expected guardrails.
    - Inspect the diff and confirm only v1.1.4 MCP/runtime/version files changed.
  - Verify: `python -m unittest discover -s tests && python -c "import json; json.load(open('src/engaku/templates/mcp.json')); json.load(open('src/engaku/templates/ai/engaku.json'))" && grep -n "DBHUB_DSN\|readonly = true\|max_rows = 1000" src/engaku/templates/dbhub.toml && git diff -- src/engaku/templates/dbhub.toml src/engaku/templates/mcp.json src/engaku/templates/ai/engaku.json src/engaku/templates/skills/database/SKILL.md .github/skills/database/SKILL.md .ai/engaku.json .ai/overview.md README.md src/engaku/cmd_init.py src/engaku/cmd_update.py src/engaku/cmd_apply.py src/engaku/utils.py tests/test_apply.py tests/test_init.py tests/test_update.py pyproject.toml src/engaku/__init__.py CHANGELOG.md`

## Out of Scope

- Adding GitHub MCP, Firecrawl, Sentry, AWS, Slack, Linear, Notion, Playwright MCP, or Serena to Engaku's default generated `.vscode/mcp.json`.
- Adding a new `engaku init --mcp-profile` flag.
- Adding a new `engaku init --python` flag.
- Auto-detecting virtual environments or guessing `.venv/bin/python`.
- Validating that the configured Python interpreter exists during `init` or `apply`.
- Implementing DBHub health checks or interactive DSN validation.
- Auto-populating real database credentials or production DSNs in the generated `dbhub.toml` file.
