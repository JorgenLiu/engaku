# engaku

AI persistent memory layer for VS Code Copilot — keeps project context, rules, and active tasks in front of the agent at every turn through VS Code Agent Hooks.

## What it does

`engaku` gives VS Code Copilot durable project memory stored in `.ai/` Markdown files. Agent Hooks automatically inject current context into every conversation, surface active-task steps on each prompt, and remind the agent when a task plan is complete and ready for review.

## Installation

```bash
pip install engaku
```

Or install directly from source:

```bash
pip install git+https://github.com/JorgenLiu/engaku.git
```

## Quick Start

```bash
# Bootstrap .ai/ and .github/ structure in your repo
engaku init
```

After running `init`, VS Code Agent Hooks are active. The `@coder`, `@planner`, `@reviewer`, and `@scanner` agents are available via `.github/agents/`. No further manual steps are needed — hooks fire automatically on SessionStart, UserPromptSubmit, Stop, and PreCompact.

## What `engaku init` creates

```
.ai/
  overview.md       — project description, constraints, tech stack
  tasks/            — planner-managed task plans
  decisions/        — architecture decision records
.github/
  copilot-instructions.md   — global agent rules
  agents/           — coder, planner, reviewer, scanner agent definitions
  instructions/     — .instructions.md stubs for hooks, templates, tests
  skills/           — bundled skills (systematic-debugging, verification-before-completion, etc.)
.vscode/
  mcp.json          — MCP server configuration (chrome-devtools, context7, dbhub)
```

## Subcommands

| Command | Purpose |
|---------|---------|
| `init` | Bootstrap `.ai/`, `.github/` structure and install VS Code Agent Hooks |
| `inject` | Inject `.ai/overview.md` + active-task context (SessionStart / PreCompact hook) |
| `prompt-check` | Detect rule/constraint in user prompt and inject active-task steps (UserPromptSubmit hook) |
| `task-review` | Detect completed task plans and emit handoff reminder (Stop hook) |
| `apply` | Apply `.ai/engaku.json` model config to `.github/agents/` frontmatter |

## How it works

After `engaku init`, four Agent Hooks fire automatically:

- **`SessionStart`** → `engaku inject`: injects `overview.md` and the active-task's remaining unchecked steps at the start of every session.
- **`PreCompact`** → `engaku inject`: injects the full task body (Background, Design, File Map, and all checkbox lines) before conversation compaction so the compact model retains full task context.
- **`UserPromptSubmit`** → `engaku prompt-check`: scans each user prompt for new rules or constraints and injects all remaining unchecked task steps as a system message so the agent always knows what to do next.
- **`Stop`** → `engaku task-review`: after each agent turn, checks whether all steps in an in-progress task plan are ticked and emits a handoff reminder if so.

## Requirements

- Python ≥ 3.8 (stdlib only, no third-party dependencies)
- VS Code with GitHub Copilot

> **Python 3.8 baseline:** v1.0.x is the final release supporting Python 3.8. Users on constrained environments can pin with `pip install "engaku<1.1"`. Later releases require Python 3.11+.

## MCP Servers

`engaku init` creates `.vscode/mcp.json` with three preconfigured MCP servers that give VS Code Copilot structured tool access to browser automation, live library documentation, and databases. Use `engaku init --no-mcp` to skip this entirely.

`engaku update` adds any missing server entries to an existing `.vscode/mcp.json` without overwriting your customizations.

### chrome-devtools-mcp

[github.com/ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) — Browser automation and DevTools via Puppeteer. Provides screenshot capture, page navigation, element interaction, JavaScript evaluation, Lighthouse performance audits, and network request inspection.

**Prerequisites:** Node.js + Chrome

```json
{
  "chrome-devtools": {
    "command": "npx",
    "args": ["-y", "chrome-devtools-mcp@latest", "--headless"]
  }
}
```

### context7

[github.com/upstash/context7](https://github.com/upstash/context7) — Live, version-specific library documentation. Two tools: `resolve-library-id` (search by name) and `query-docs` (fetch current docs). HTTP remote mode — no local process needed.

**Prerequisites:** None (network access only). Set `CONTEXT7_API_KEY` env var for higher rate limits.

```json
{
  "context7": {
    "type": "http",
    "url": "https://mcp.context7.com/mcp"
  }
}
```

### dbhub

[github.com/bytebase/dbhub](https://github.com/bytebase/dbhub) — Multi-database access supporting PostgreSQL, MySQL, MariaDB, SQL Server, and SQLite. Two tools: `search_objects` (schema exploration) and `execute_sql` (query execution).

**Prerequisites:** Node.js. Requires a DSN connection string (VS Code prompts on first use).

```json
{
  "dbhub": {
    "command": "npx",
    "args": ["@bytebase/dbhub@latest", "--dsn", "${input:dbDsn}"]
  }
}
```

**DSN formats:**

| Database | Format |
|----------|--------|
| PostgreSQL | `postgres://user:pass@host:5432/db?sslmode=disable` |
| MySQL | `mysql://user:pass@host:3306/db` |
| MariaDB | `mariadb://user:pass@host:3306/db` |
| SQL Server | `sqlserver://user:pass@host:1433/db` |
| SQLite | `sqlite:///absolute/path/to/file.db` |

For passwords with special characters (`:`, `@`, `#`), use environment variables (`DB_TYPE`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) in the server's `env` block instead of encoding them in the DSN.
