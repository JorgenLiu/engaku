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

After running `init`, VS Code Agent Hooks are active. The `@coder`, `@planner`, `@reviewer`, and `@scanner` agents are available via `.github/agents/`. No further manual steps are needed — hooks fire automatically on SessionStart, SubagentStart, UserPromptSubmit, Stop, and PreCompact.

## What `engaku init` creates

```
.ai/
  overview.md       — project description, constraints, tech stack
  engaku.json       — model, MCP tool, and hook Python runtime config
  tasks/            — planner-managed task plans
  decisions/        — architecture decision records
.github/
  copilot-instructions.md   — global agent rules
  agents/           — coder, planner, reviewer, scanner agent definitions
  instructions/     — lessons and agent-boundaries.instructions.md stubs
  skills/           — bundled skills (systematic-debugging, verification-before-completion, etc.)
.vscode/
  settings.json     — enables VS Code terminal/tool output compression
  mcp.json          — MCP server configuration (chrome-devtools, context7, dbhub)
  dbhub.toml        — DBHub MCP TOML config (fill in your database sources)
```

`engaku init --no-mcp` skips both `.vscode/mcp.json` and `.vscode/dbhub.toml`, along with the MCP-related skills.

When MCP support is enabled, `engaku init` grants `chrome-devtools/*` to the planner agent by default (alongside `context7/*` and `dbhub/*`), so planner can run browser-backed research and verification before producing plans. `engaku update` does not modify an existing `.ai/engaku.json` — once written, your MCP tool allocations stay user-owned.

## Subcommands

| Command | Purpose |
|---------|---------|
| `init` | Bootstrap `.ai/`, `.github/` structure and install VS Code Agent Hooks |
| `inject` | Inject `.ai/overview.md` + active-task context (SessionStart / PreCompact hook) |
| `prompt-check` | Detect rule/constraint in user prompt and inject active-task steps (UserPromptSubmit hook) |
| `task-review` | Detect completed task plans and emit handoff reminder (Stop hook) |
| `apply` | Apply `.ai/engaku.json` model, MCP tool, and hook Python runtime config to `.github/agents/` frontmatter |
| `update` | Sync generated agents and skills from bundled templates, merge MCP server additions, and apply `.ai/engaku.json` config |
| `list-mcp` | List available built-in MCP recipes |
| `add-mcp` | Install a curated MCP recipe into `.vscode/mcp.json`, `.ai/engaku.json`, and agent frontmatter |

## How it works

After `engaku init`, five Agent Hooks fire automatically:

- **`SessionStart`** → `engaku inject`: injects `overview.md` and the active-task's remaining unchecked steps at the start of every session.
- **`PreCompact`** → `engaku inject`: injects the full task body (Background, Design, File Map, and all checkbox lines) before conversation compaction so the compact model retains full task context.
- **`SubagentStart`** → `engaku inject`: gives reviewer subagent sessions the same project and active-task context before verification begins.
- **`UserPromptSubmit`** → `engaku prompt-check`: scans each user prompt for new rules or constraints and injects all remaining unchecked task steps as a system message so the agent always knows what to do next.
- **`Stop`** → `engaku task-review`: after each agent turn, checks whether all steps in an in-progress task plan are ticked and emits a handoff reminder if so.

## Requirements

- Python 3.8 or newer (stdlib only, no third-party dependencies)
- VS Code with GitHub Copilot

> **Python 3.8 baseline:** v1.1.x continues to support Python 3.8. The future Python 3.11 migration remains deferred.

## Bundled Office skills

`engaku init` and `engaku update` deploy two optional Office read/analysis skills into `.github/skills/`. Each ships a `requirements-py38.txt` with pinned Python 3.8.4-compatible dependencies and helper scripts. Engaku itself still has **no third-party runtime dependencies**.

### xlsx-analyze

Inspect Excel workbooks and delimited files, profile column data, and map formula relationships.

```bash
python -m pip install -r .github/skills/xlsx-analyze/requirements-py38.txt
# inspect workbook structure
python .github/skills/xlsx-analyze/scripts/inspect_workbook.py file.xlsx --format json
# profile a sheet's columns
python .github/skills/xlsx-analyze/scripts/profile_sheet.py file.xlsx --sheet Sheet1 --format json
# build a formula dependency graph (no formula evaluation)
python .github/skills/xlsx-analyze/scripts/formula_graph.py file.xlsx --sheet Sheet1 --format json
```

Supports `.xlsx`, `.xlsm`, `.csv`, and `.tsv`. Formula relationships are inferred via `openpyxl.formula.Tokenizer` without evaluating any formula.

### docx-read

Read and inspect DOCX files, extract paragraphs/headings/tables, and optionally convert to HTML or plain text.

```bash
python -m pip install -r .github/skills/docx-read/requirements-py38.txt
# inspect document structure
python .github/skills/docx-read/scripts/inspect_docx.py report.docx --format json
# extract text content
python .github/skills/docx-read/scripts/extract_text.py report.docx --include-tables --format markdown
# convert to HTML (Mammoth; output is NOT sanitized — review before rendering)
python .github/skills/docx-read/scripts/docx_to_html.py report.docx --output out.html
```


## Configuration

### Hook Python interpreter

By default, generated Agent Hooks call `engaku <subcommand>` directly, relying on `engaku` being on the system `PATH`. If `engaku` is only available inside a virtual environment, set the `python` key in `.ai/engaku.json` and run `engaku apply` (or `engaku update`) to rewrite all hook commands:

```json
{
  "python": ".venv/bin/python"
}
```

With this set, `engaku apply` rewrites every Engaku-managed hook command to `.venv/bin/python -m engaku <subcommand>`. Relative and absolute interpreter paths are both accepted. Set to `null` (the default) to restore the plain `engaku <subcommand>` form.

If the default `engaku` command is already broken, run the interpreter directly to apply the change:

```sh
.venv/bin/python -m engaku apply
```



## Global kernel and lossless compactness

Engaku policy lives in `.github/copilot-instructions.md` as an **Engaku Global Kernel**: agent ownership boundaries, Caveman-inspired lossless compactness rules, and generated artifact style in one unconditional file. `.github/instructions/` remains path-specific; hooks inject dynamic state only.

Lossless compactness: preserve complete technical substance (code, paths, commands, exact error text, decisions, verification results) while removing ceremony — no `Now let me…` filler, no repeated summaries, no arbitrary answer caps.

Teams that want Caveman's exact compression modes can install it separately: `npx skills add JuliusBrussee/caveman -a github-copilot`. Engaku uses its own Caveman-inspired rules and does not copy upstream skill text.

## User-level compact instruction

A user-level `compact.instructions.md` suppresses affirmations, intent narration, and pre-tool status updates across all workspaces. Copilot reads it automatically from:

| Platform | Path |
|----------|------|
| macOS / Linux | `~/.copilot/instructions/compact.instructions.md` |
| Windows | `%USERPROFILE%\.copilot\instructions\compact.instructions.md` |

**Linux / macOS:**

```sh
mkdir -p ~/.copilot/instructions
cat > ~/.copilot/instructions/compact.instructions.md << 'EOF'
---
applyTo: "**"
---
NEVER output warmth, curiosity, playfulness, or personality. NEVER say "Great!", "Sure!", "Happy to help!", or any affirmation.
NEVER narrate what you are about to do ("I will now...", "Let me...", "I'll start by..."). Report actions and findings only.
NEVER send intermediary status updates before using tools. Use tools immediately; narrate nothing.
ALWAYS respond in the most compact, information-dense form. Fragments are preferred over prose sentences.
ALWAYS use bullets or tables when listing multiple items. NEVER default to flowing prose paragraphs.
EOF
```

**Windows (PowerShell):**

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.copilot\instructions" | Out-Null
@'
---
applyTo: "**"
---
NEVER output warmth, curiosity, playfulness, or personality. NEVER say "Great!", "Sure!", "Happy to help!", or any affirmation.
NEVER narrate what you are about to do ("I will now...", "Let me...", "I'll start by..."). Report actions and findings only.
NEVER send intermediary status updates before using tools. Use tools immediately; narrate nothing.
ALWAYS respond in the most compact, information-dense form. Fragments are preferred over prose sentences.
ALWAYS use bullets or tables when listing multiple items. NEVER default to flowing prose paragraphs.
'@ | Set-Content "$env:USERPROFILE\.copilot\instructions\compact.instructions.md" -Encoding UTF8
```

The `applyTo: "**"` pattern makes this instruction active in every workspace without any per-project configuration.

## MCP Servers

`engaku init` creates `.vscode/mcp.json` with three default MCP servers that give VS Code Copilot structured tool access to browser automation, live library documentation, and databases. Use `engaku init --no-mcp` to skip this entirely.

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

**Prerequisites:** Node.js. `engaku init` generates `.vscode/dbhub.toml` as a comment-only stub wired to `--config`. Fill it in with your own `[[sources]]` and optional `[[tools]]` entries; see [dbhub.ai/config/toml](https://dbhub.ai/config/toml) for the full schema.

```json
{
  "dbhub": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@bytebase/dbhub@latest", "--transport", "stdio", "--config", "${workspaceFolder}/.vscode/dbhub.toml"]
  }
}
```

The generated `.vscode/dbhub.toml` is a comment-only template — fill in your databases:

```toml
# See full config reference: https://dbhub.ai/config/toml
#
# [[sources]]
# id   = "default"
# dsn  = "postgres://user:pass@localhost:5432/mydb"
# lazy = true
#
# [[tools]]
# name     = "execute_sql"
# source   = "default"
# readonly = true
```

### VS Code 1.120 tool settings

`engaku init` enables `chat.tools.compressOutput.enabled` by default in `.vscode/settings.json`. This VS Code 1.120 preview setting compresses large terminal/tool output (`git diff`, `ls -l`, test/build/lint output, package install progress, and repeated identical outputs) before it enters model context. To disable it, set `"chat.tools.compressOutput.enabled": false` in `.vscode/settings.json`.

One additional optional flag:

| Setting | Effect |
|---------|--------|
| `chat.tools.riskAssessment.enabled` | Shows a risk badge on terminal commands before execution. Useful when write-capable tools are enabled. |

## MCP Recipes

Engaku ships curated recipes for popular services. A recipe installs a minimal MCP server block into `.vscode/mcp.json`, registers its wildcard in `.ai/engaku.json`, and (unless `--no-apply` is passed) rewrites all target agent frontmatter in one step. Engaku does **not** inject credentials, input prompts, or service-specific env variables — add those directly to `.vscode/mcp.json` after install.

```sh
engaku list-mcp            # show available recipes
engaku add-mcp github      # install GitHub MCP (OAuth, no PAT required)
engaku add-mcp gitlab      # install GitLab MCP (remote org endpoint — edit URL to your instance)
engaku add-mcp atlassian   # install Atlassian MCP for Jira + Confluence (add auth env vars yourself)
```

**Options:**

| Flag | Effect |
|------|--------|
| `--agents coder planner` | Override which agents receive the MCP wildcard (default: recipe's `default_agents`) |
| `--dry-run` | Print planned changes without writing any files |
| `--no-apply` | Write `.vscode/mcp.json` and `.ai/engaku.json` but skip `engaku apply` |

Existing server entries in `.vscode/mcp.json` are never overwritten; the recipe is silently skipped for that server if it already exists.

### GitHub MCP recipe

```sh
engaku add-mcp github
```

Uses the official hosted read-only endpoint — no local process, no PAT. OAuth via VS Code's GitHub Copilot connection. Grants `github/*` to `coder`, `planner`, and `reviewer` by default.

To enable write tools (create issues, open PRs), edit `.vscode/mcp.json` manually and change the URL to `https://api.githubcopilot.com/mcp/`. See [GitHub MCP docs](https://docs.github.com/en/copilot/customizing-copilot/using-model-context-protocol/using-the-github-mcp-server) for available toolsets.

### GitLab MCP recipe

```sh
engaku add-mcp gitlab
```

Generates a remote HTTP server block pointing to your GitLab instance's built-in MCP endpoint. Edit the placeholder URL in `.vscode/mcp.json` to your actual instance:

```json
"gitlab": {
  "type": "http",
  "url": "https://gitlab.example.com/api/v4/mcp"
}
```

Authenticate via a GitLab personal access token in VS Code. For local stdio fallback (e.g. gitlab.com without remote MCP enabled), use `npx -y @zereight/mcp-gitlab@latest` instead.

### Atlassian MCP recipe (Jira + Confluence)

```sh
engaku add-mcp atlassian
```

Uses upstream [`mcp-atlassian`](https://github.com/sooperset/mcp-atlassian) via `uvx`. Requires [uv](https://docs.astral.sh/uv/). One server covers both Jira and Confluence; grants `atlassian/*` to `coder` and `planner`. After install, add auth details to `.vscode/mcp.json`:

```json
"atlassian": {
  "command": "uvx",
  "args": ["mcp-atlassian"],
  "env": {
    "JIRA_URL": "https://your-company.atlassian.net",
    "JIRA_USERNAME": "your.email@company.com",
    "JIRA_API_TOKEN": "<your-api-token>",
    "CONFLUENCE_URL": "https://your-company.atlassian.net",
    "CONFLUENCE_USERNAME": "your.email@company.com",
    "CONFLUENCE_API_TOKEN": "<your-api-token>"
  }
}
```

API tokens: [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens).

## Optional MCP Servers

These servers are not generated by `engaku init`. Add them manually to `.vscode/mcp.json` when needed.

### Firecrawl MCP

Structured web scraping and search via [Firecrawl](https://firecrawl.dev). Useful for extracting content from web pages that Context7 does not index.

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "firecrawl-key",
      "description": "Firecrawl API key",
      "password": true
    }
  ],
  "servers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "${input:firecrawl-key}"
      }
    }
  }
}
```

Requires a Firecrawl API key. Not a default dependency — add only when structured web research is needed.

## Bundled Skills

### skill-authoring

Helper workflow for turning a repeated multi-step method into a reusable Copilot skill. Different from VS Code's `/create-skill` command: this skill enforces an explicit primitive-selection gate (instruction file vs prompt file vs skill vs custom agent), draws a hard prompt-file-vs-skill boundary, and locks in an ownership rule — skills authored with this workflow stay user-owned and are not registered in Engaku's bundled template inventory unless an Engaku task explicitly ships them.

Use it when you notice the same phases, safeguards, and output format being re-explained across sessions and a one-shot prompt would not capture the adaptive logic between phases.

## Credits

### karpathy-guidelines skill

Adapted from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT, Copyright © Forrest Chang), itself derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876).

### MCP Servers

- [chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) — browser automation and DevTools (Chrome DevTools team)
- [context7](https://github.com/upstash/context7) — live library documentation (Upstash)
- [dbhub](https://github.com/bytebase/dbhub) — multi-database access (Bytebase)
