---
plan_id: 2026-04-20-v110-mcp-integration
title: "v1.1.0 — MCP server integration"
status: done
created: 2026-04-20
---

## Background

Decision 004 deferred MCP server integration to post-v1.0. The detailed design
is in `.ai/docs/mcp-integration.md`. This plan implements it as v1.1.0, still
on Python 3.8 (the 3.11 bump is deferred further).

Three MCP servers are integrated:
- **chrome-devtools-mcp** — browser automation, DevTools, performance profiling
- **context7** — live library documentation (HTTP remote, zero local process)
- **dbhub** — multi-database access (requires user-supplied DSN via input variable)

`engaku init` gains `.vscode/mcp.json` generation and three new bundled skills.
`engaku update` gains mcp.json merge logic. A `--no-mcp` flag lets users skip
MCP setup entirely.

## Design

### `.vscode/mcp.json` template

A new template file at `src/engaku/templates/mcp.json` contains the three server
entries. Key decisions (resolving the open questions from the design doc):

- **context7**: HTTP remote mode (`"type": "http"`) — zero prerequisites, no
  local process.
- **dbhub DSN**: Uses `${input:dbDsn}` input variable. VS Code prompts the user
  when the server first starts. No engaku-side interactive prompt needed.
- **No JSON comments**: `.vscode/mcp.json` is standard JSON. VS Code manages
  enable/disable state separately in its own storage, so there is no `disabled`
  field. All three servers are included; users disable dbhub via VS Code UI if
  they don't need it.

Template content:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "dbDsn",
      "description": "Database connection string for dbhub (e.g. postgresql://user:pass@host:5432/db). Leave empty to skip."
    }
  ],
  "servers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--headless"]
    },
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp"
    },
    "dbhub": {
      "command": "npx",
      "args": ["@bytebase/dbhub@latest", "--dsn", "${input:dbDsn}"]
    }
  }
}
```

### `engaku init` behavior

- Writes `.vscode/mcp.json` from the template using the existing `_copy_template`
  helper (skip-if-exists, consistent with all other files).
- Three new skills added to the skills loop: `headless-browser`, `context7`,
  `database`.
- New `--no-mcp` CLI flag: when set, skips both `.vscode/mcp.json` creation and
  the three MCP-related skills.

### `engaku update` behavior

- If `.vscode/mcp.json` exists, merges in any missing server entries from the
  template (preserves user customizations, adds new servers). If it does not
  exist, does **not** create it (respects the user's init-time decision).
- Three new skills added to the `_SKILLS` tuple.

### Skills

Three new skill files, each under `src/engaku/templates/skills/`:

| Skill directory | Teaches agents to… |
|-|-|
| `chrome-devtools/SKILL.md` | Use chrome-devtools-mcp tools: `take_screenshot`, `navigate_page`, `click`, `fill`, `evaluate_script`, `lighthouse_audit` |
| `context7/SKILL.md` | Invoke `resolve-library-id` + `query-docs` for accurate, version-specific library documentation |
| `database/SKILL.md` | Use `search_objects` before `execute_sql`, format DSN strings, prefer read-only exploration |

### CLI argument threading

`cli.py` adds `--no-mcp` to the `init` subparser. The parsed flag is passed to
`cmd_init.run(cwd=None, no_mcp=False)` as a keyword argument.

## File Map

- Create: `src/engaku/templates/mcp.json`
- Create: `src/engaku/templates/mcp.json`
- Create: `src/engaku/templates/skills/chrome-devtools/SKILL.md`
- Create: `src/engaku/templates/skills/context7/SKILL.md`
- Create: `src/engaku/templates/skills/database/SKILL.md`
- Create: `.github/skills/chrome-devtools/SKILL.md`
- Create: `.github/skills/context7/SKILL.md`
- Create: `.github/skills/database/SKILL.md`
- Rename: `src/engaku/templates/agents/dev.agent.md` → `coder.agent.md`
- Rename: `.github/agents/dev.agent.md` → `coder.agent.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `src/engaku/cli.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `src/engaku/__init__.py`
- Modify: `pyproject.toml`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Create mcp.json template**
  - Files: `src/engaku/templates/mcp.json`
  - Steps:
    - Create `src/engaku/templates/mcp.json` with the three server entries and `inputs` array as shown in the Design section
  - Verify: `python -c "import json; json.load(open('src/engaku/templates/mcp.json'))"` exits 0

- [x] 2. **Create chrome-devtools skill**
  - Files: `src/engaku/templates/skills/chrome-devtools/SKILL.md`, `.github/skills/chrome-devtools/SKILL.md`
  - Steps:
    - Write `src/engaku/templates/skills/chrome-devtools/SKILL.md` with frontmatter (`name: chrome-devtools`, description, `user-invocable: true`, `disable-model-invocation: false`) and a workflow guide covering: when to use each chrome-devtools-mcp tool, screenshot for visual verification, lighthouse for performance audits, navigate + snapshot for UI automation
    - Copy the identical file to `.github/skills/chrome-devtools/SKILL.md`
  - Verify: `head -5 src/engaku/templates/skills/chrome-devtools/SKILL.md` shows frontmatter

- [x] 3. **Create context7 skill**
  - Files: `src/engaku/templates/skills/context7/SKILL.md`, `.github/skills/context7/SKILL.md`
  - Steps:
    - Write `src/engaku/templates/skills/context7/SKILL.md` with frontmatter (`name: context7`) and a workflow guide covering: `resolve-library-id` → `query-docs` pattern, when to invoke context7 (any library/API question where training data may be stale), example invocation patterns
    - Copy the identical file to `.github/skills/context7/SKILL.md`
  - Verify: `head -5 src/engaku/templates/skills/context7/SKILL.md` shows frontmatter

- [x] 4. **Create database skill**
  - Files: `src/engaku/templates/skills/database/SKILL.md`, `.github/skills/database/SKILL.md`
  - Steps:
    - Write `src/engaku/templates/skills/database/SKILL.md` with frontmatter (`name: database`) and a workflow guide covering:
      - **Workflow**: always call `search_objects` first to explore schema before writing any SQL; use `execute_sql` only after understanding the table structure
      - **DSN formats** (for the mcp.json `${input:dbDsn}` prompt):
        - PostgreSQL: `postgres://user:pass@host:5432/db?sslmode=disable` (add `?sslmode=require` for production)
        - MySQL: `mysql://user:pass@host:3306/db`
        - MariaDB: `mariadb://user:pass@host:3306/db`
        - SQL Server: `sqlserver://user:pass@host:1433/db`
        - SQLite: `sqlite:///absolute/path/to/file.db` or `sqlite://relative/path.db`
      - **Env var alternative**: passwords with special characters (`:`, `@`, `#`) break URL encoding — use `DB_TYPE`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` env vars instead and leave DSN empty; these go in the `env` block of `.vscode/mcp.json`
      - **SSL/TLS**: `sslmode=require` for remote servers; `verify-ca`/`verify-full` + `sslrootcert=` for RDS/cloud
      - **SSH tunneling**: for databases behind a bastion, add `--ssh-host`, `--ssh-user`, `--ssh-key` args to the server config
      - **Multi-database**: create multiple server entries in `.vscode/mcp.json` with different `--id` values (e.g. `dbhub-prod`, `dbhub-staging`) so tools are named `execute_sql_prod` vs `execute_sql_staging`
      - **Guardrails**: mention `--readonly` flag and `--row-limit` for safe exploration
    - Copy the identical file to `.github/skills/database/SKILL.md`
  - Verify: `head -5 src/engaku/templates/skills/database/SKILL.md` shows frontmatter

- [x] 5. **Add --no-mcp flag to CLI and update cmd_init.py**
  - Files: `src/engaku/cli.py`, `src/engaku/cmd_init.py`
  - Steps:
    - In `cli.py`, add `--no-mcp` argument to the `init` subparser: `init_parser.add_argument("--no-mcp", action="store_true", help="Skip .vscode/mcp.json and MCP-related skills")`
    - Change `init` subparser from `subparsers.add_parser(...)` to `init_parser = subparsers.add_parser(...)`
    - In the `args.command == "init"` branch, pass `no_mcp=args.no_mcp` to `run()`
    - In `cmd_init.py`, update `run()` signature to `run(cwd=None, no_mcp=False)`
    - In `cmd_init.py`, add three new skills (`chrome-devtools`, `context7`, `database`) to the skills loop, guarded by `if not no_mcp`
    - In `cmd_init.py`, add a new section after the `.vscode/settings.json` block that writes `.vscode/mcp.json` using `_copy_template` — guarded by `if not no_mcp`
    - The seven existing skills remain unconditional
    - Update the module docstring to list `.vscode/mcp.json` and the three new skills
  - Verify: `python -m engaku init --help` shows `--no-mcp` flag

- [x] 6. **Rename dev agent to coder (live + template)**
  - Files: `src/engaku/templates/agents/dev.agent.md`, `.github/agents/dev.agent.md`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`
  - Steps:
    - Rename `src/engaku/templates/agents/dev.agent.md` → `src/engaku/templates/agents/coder.agent.md` (use `git mv`)
    - Rename `.github/agents/dev.agent.md` → `.github/agents/coder.agent.md` (use `git mv`)
    - In both renamed files, update `name: dev` → `name: coder` in the frontmatter
    - In `src/engaku/cmd_init.py`, replace `"dev.agent.md"` with `"coder.agent.md"` in the agents loop
    - In `src/engaku/cmd_update.py`, replace `"dev.agent.md"` with `"coder.agent.md"` in `_AGENTS`
  - Verify: `ls src/engaku/templates/agents/` lists `coder.agent.md` and no `dev.agent.md`

- [x] 7. **Update cmd_update.py with mcp.json merge and new skills**
  - Files: `src/engaku/cmd_update.py`
  - Steps:
    - Add `chrome-devtools`, `context7`, `database` to the `_SKILLS` tuple
    - Add a new section after the `.vscode/settings.json` block: if `.vscode/mcp.json` exists, load it, load the template, merge any server keys from template that are missing in the existing file (also merge missing `inputs` entries by `id`), write back; report `[update]` if changed, `[skip]` if no new entries. If `.vscode/mcp.json` does not exist, skip silently
    - Use `json.load` / `json.dump` with `indent=2` (stdlib only, 3.8-compatible)
  - Verify: `python -c "from engaku.cmd_update import _SKILLS; assert 'context7' in _SKILLS"`

- [x] 8. **Write tests for mcp.json in init**
  - Files: `tests/test_init.py`
  - Steps:
    - Replace `dev.agent.md` with `coder.agent.md` in `EXPECTED_FILES`
    - Add `.vscode/mcp.json` to `EXPECTED_FILES`
    - Add new skills to `EXPECTED_FILES`: `chrome-devtools`, `context7`, `database`
    - Add test `test_no_mcp_flag_skips_mcp_files`: call `run(cwd=tmpdir, no_mcp=True)`, assert `.vscode/mcp.json` does NOT exist, assert `chrome-devtools/SKILL.md` does NOT exist, assert non-MCP skills (e.g. `systematic-debugging`) DO exist
    - Add test `test_mcp_json_is_valid`: call `run(cwd=tmpdir)`, load `.vscode/mcp.json` with `json.load`, assert `servers` key contains `chrome-devtools`, `context7`, `dbhub`
  - Verify: `python -m pytest tests/test_init.py -v`

- [x] 9. **Write tests for mcp.json merge in update**
  - Files: `tests/test_update.py`
  - Steps:
    - Replace `dev.agent.md` with `coder.agent.md` in update test assertions
    - Add test `test_update_merges_mcp_servers`: run init, remove one server from `.vscode/mcp.json`, run update, assert the removed server is restored while other customizations are preserved
    - Add test `test_update_skips_mcp_when_no_mcp_json`: run init with `no_mcp=True`, run update, assert `.vscode/mcp.json` still does not exist
  - Verify: `python -m pytest tests/test_update.py -v`

- [x] 10. **Bump version to 1.1.0**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`
  - Steps:
    - Set `version = "1.1.0"` in `pyproject.toml`
    - Set `__version__ = "1.1.0"` in `src/engaku/__init__.py`
    - Confirm `requires-python = ">=3.8"` is unchanged
  - Verify: `python -c "import engaku; print(engaku.__version__)"` prints `1.1.0`

- [x] 11. **Add CHANGELOG entry for v1.1.0**
  - Files: `CHANGELOG.md`
  - Steps:
    - Prepend a new `## [1.1.0] — 2026-04-20` section with:
      - Added: `.vscode/mcp.json` generation with three MCP servers (chrome-devtools-mcp, context7, dbhub)
      - Added: `--no-mcp` flag for `engaku init` to skip MCP setup
      - Added: three new bundled skills: `chrome-devtools`, `context7`, `database`
      - Added: `engaku update` merges new MCP server entries into existing `.vscode/mcp.json`
      - Changed: dev agent renamed to `coder` across templates and live `.github/agents/`
    - Update the v1.0.0 note: change "next release targets Python 3.11+" to "Python 3.11 migration deferred; v1.1.x continues on Python 3.8"
  - Verify: `head -15 CHANGELOG.md` shows the 1.1.0 header

- [x] 12. **Update .ai/overview.md**
  - Files: `.ai/overview.md`
  - Steps:
    - Add mention of MCP server integration to the Overview paragraph: `engaku init` now also writes `.vscode/mcp.json` with three preconfigured MCP servers (chrome-devtools, context7, dbhub) and three matching skills
    - Replace `dev` with `coder` in any agent references in the overview
    - Add `.vscode/mcp.json` note to the Directory Structure section under templates
  - Verify: `grep "mcp" .ai/overview.md` returns matches

- [x] 13. **Document MCP servers in README**
  - Files: `README.md`
  - Steps:
    - Add a new `## MCP Servers` section (place after the existing feature list, before any Contributing/License sections)
    - For each server, include: repo link, what it provides, and the minimal configuration snippet that ends up in `.vscode/mcp.json`
    - **chrome-devtools-mcp** — [github.com/ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) — browser automation and DevTools via Puppeteer; requires Node.js + Chrome; zero-config (`npx -y chrome-devtools-mcp@latest --headless`)
    - **context7** — [github.com/upstash/context7](https://github.com/upstash/context7) — live, version-specific library documentation; HTTP remote, no local process; add `CONTEXT7_API_KEY` env var for higher rate limits
    - **dbhub** — [github.com/bytebase/dbhub](https://github.com/bytebase/dbhub) — multi-database access (PostgreSQL, MySQL, MariaDB, SQL Server, SQLite); requires a DSN connection string (VS Code prompts on first use); document the DSN format table (one line per DB type) and the env var alternative for passwords with special characters
    - Add a note that `engaku init --no-mcp` skips this section entirely
    - Add a note that `engaku update` adds any missing server entries to an existing `.vscode/mcp.json`
  - Verify: `grep "dbhub\|context7\|chrome-devtools" README.md` returns matches for all three

- [x] 14. **Run full test suite**
  - Files: all test files
  - Steps:
    - Run `python -m pytest tests/ -v` and confirm all tests pass
    - Run `python -m engaku init --help` and confirm `--no-mcp` is listed
  - Verify: `python -m pytest tests/ -v` exits 0

## Out of Scope

- Python 3.11 version bump (deferred further per user request)
- Learnings / transcript intelligence system (see decision 003)
- Interactive DSN prompt in `engaku init` (VS Code input variables handle this)
- `--no-mcp` flag for `engaku update` (update only touches mcp.json if it already exists)
- MCP server health checks or connectivity tests
- Multi-database TOML config generation (users configure `dbhub.toml` manually; skill documents the pattern)
