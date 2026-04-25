# MCP Server Research - 2026-04-25

Related task: `2026-04-25-refresh-mcp-server-config`

## Scope

This note reviews Engaku's current bundled MCP server configuration against current upstream documentation, with special attention to `dbhub`. It also records a GitHub search pass for additional MCP servers that may be worth adding to Engaku.

Current Engaku default MCP servers:

- `chrome-devtools` via `npx -y chrome-devtools-mcp@latest --headless`
- `context7` via remote HTTP `https://mcp.context7.com/mcp`
- `dbhub` via `npx @bytebase/dbhub@latest --dsn ${input:dbDsn}`

## DBHub Findings

Sources checked:

- Context7 library `/bytebase/dbhub`
- `bytebase/dbhub` upstream README
- `docs/installation.mdx`
- `docs/config/command-line.mdx`
- `docs/config/toml.mdx`
- `docs/tools/custom-tools.mdx`

### Problems In Current Template

Engaku currently ships this dbhub entry:

```json
{
  "dbhub": {
    "command": "npx",
    "args": ["@bytebase/dbhub@latest", "--dsn", "${input:dbDsn}"]
  }
}
```

Issues:

- Missing `"type": "stdio"`. Upstream VS Code examples now include it explicitly.
- Missing `--transport stdio`. DBHub defaults to `stdio`, but upstream VS Code examples specify it, and explicit transport is safer for generated client config.
- Missing `-y` before the package name. Several MCP server examples use `npx -y` to avoid an interactive npm install confirmation during MCP startup. DBHub docs often omit `-y`, but Codex and LibreChat examples include it; Engaku already uses `-y` for Chrome DevTools.
- The input is not marked as secret. Upstream VS Code input-variable example uses `"password": true` for the DSN prompt.
- The prompt says "Leave empty to skip", but DBHub docs say `--dsn` is required unless using `--demo`, `--config`, environment variables, or an auto-loaded `./dbhub.toml`. Passing an empty `--dsn` is not documented as a skip mechanism.
- The bundled database skill still recommends `--readonly` and `--row-limit`. Upstream docs now show command-line `--readonly` and `--max-rows` as deprecated in favor of TOML `[[tools]]` settings. `--row-limit` does not match the current documented flag name.

### Recommended DBHub Template

Use the current upstream VS Code input-variable pattern, with `npx -y` for non-interactive startup:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "db-dsn",
      "description": "Database connection string for DBHub",
      "password": true
    }
  ],
  "servers": {
    "dbhub": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@bytebase/dbhub@latest",
        "--transport",
        "stdio",
        "--dsn",
        "${input:db-dsn}"
      ]
    }
  }
}
```

Alternative for advanced teams:

```json
{
  "servers": {
    "dbhub": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@bytebase/dbhub@latest",
        "--transport",
        "stdio",
        "--config",
        "${workspaceFolder}/dbhub.toml"
      ]
    }
  }
}
```

Do not combine `--config` with `--dsn` or `--id`; upstream documents those flags as mutually exclusive.

### Recommended Skill And README Changes

Update DBHub docs to say:

- Use `search_objects` before `execute_sql`.
- Prefer TOML for multi-database, read-only mode, max rows, timeouts, SSL, SSH, custom tools, and environment interpolation.
- For simple one-database setup, `--dsn` is acceptable.
- For passwords with special characters, use either DBHub environment variables (`DB_TYPE`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) or TOML with `${VAR}` interpolation.
- Read-only and max rows are now TOML tool settings:

```toml
[[sources]]
id = "production"
dsn = "postgres://user:${DB_PASSWORD}@db.example.com:5432/app?sslmode=require"
lazy = true
query_timeout = 30

[[tools]]
name = "execute_sql"
source = "production"
readonly = true
max_rows = 1000
```

## Additional MCP Server Search

Searches run:

- GitHub topic search: `topic:mcp-server`, sorted by stars
- Official org search: `org:modelcontextprotocol server`
- Focused searches for GitHub, browser automation, docs, Sentry, Linear, Notion, Slack, AWS, Firecrawl, Serena
- Upstream README fetches for GitHub MCP, Playwright MCP, AWS Labs MCP, Firecrawl MCP, Sentry MCP, and Serena

### High-Signal Candidates

#### GitHub MCP Server

- Repo: `github/github-mcp-server`
- Stars at search time: about 29k
- Maintainer: GitHub
- VS Code config: remote HTTP server at `https://api.githubcopilot.com/mcp/`
- Strengths: issues, PRs, Actions, releases, repo search, code security, Dependabot, notifications, GitHub support docs, Copilot-related tools.
- Cost: requires VS Code 1.101+ remote MCP/OAuth support or PAT fallback. Adds a broad write-capable tool surface unless constrained by toolsets/read-only configuration.

Recommendation: strongest candidate, but do not add to default template yet. Add it as an optional recipe or opt-in server because it overlaps with VS Code's native Git integration and introduces auth and permission scope decisions. If shipped, prefer remote HTTP plus a conservative skill that warns about toolsets and read-only mode.

Candidate optional config:

```json
{
  "servers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

#### Firecrawl MCP Server

- Repo: `firecrawl/firecrawl-mcp-server`
- Stars at search time: about 6.1k
- Maintainer: Firecrawl
- VS Code config: `npx -y firecrawl-mcp` with `FIRECRAWL_API_KEY` input.
- Strengths: web search, scraping, crawling, extraction, site mapping, structured JSON extraction.
- Cost: requires API key or self-hosted endpoint; overlaps partly with VS Code web fetch and Chrome/Playwright browser tools, but is much better for structured web extraction.

Recommendation: optional recipe, not default. Useful for research-heavy users, but API-key cost and potential token-heavy crawls make it too opinionated for Engaku's default setup.

#### Sentry MCP Server

- Repo: `getsentry/sentry-mcp`
- Stars at search time: about 667
- Maintainer: Sentry
- Strengths: issue/error/trace/performance workflows for projects already using Sentry.
- Cost: Sentry token required; AI-powered search tools require OpenAI or Anthropic provider configuration; domain-specific.

Recommendation: optional ecosystem recipe only.

#### AWS Labs MCP Servers

- Repo: `awslabs/mcp`
- Stars at search time: about 8.8k
- Maintainer: AWS Labs
- Strengths: large suite of AWS documentation, IaC, API, pricing, CloudWatch, DynamoDB, EKS/ECS, serverless, etc.
- Cost: requires `uvx`, Python/AWS credentials, and service-specific configuration; many servers can mutate cloud resources.

Recommendation: optional recipes by use case. Do not add a default AWS server to Engaku.

#### Serena

- Repo: `oraios/serena`
- Stars at search time: about 23k
- Strengths: semantic code navigation, editing, refactoring via LSP/JetBrains backend.
- Cost: significant overlap with VS Code/Copilot language-server tools already available in this environment; requires `uv` and project initialization.

Recommendation: do not add by default. Mention as an advanced optional integration for clients that lack VS Code's symbol/refactor tools.

### Candidates To Avoid For Defaults

- `modelcontextprotocol/servers`: useful registry/reference, but many servers duplicate VS Code built-ins: filesystem, git, fetch, memory.
- Playwright MCP (`microsoft/playwright-mcp`): high quality, but Engaku already bundles `chrome-devtools-mcp`. Playwright itself says coding agents may benefit more from CLI+skills than MCP in many cases. Add only if Engaku decides browser automation should be Playwright-first rather than Chrome DevTools-first.
- Notion, Slack, Linear: useful for some teams, but all require workspace tokens and are collaboration-system specific.
- n8n / Activepieces / Klavis: integration platforms, not small zero-config MCP servers to bundle.
- Security/offensive tooling MCPs: inappropriate for Engaku defaults.

## Recommendation

Short term:

1. Fix the DBHub template and docs now.
2. Keep the default MCP set at three servers: Chrome DevTools, Context7, DBHub.
3. Add README optional recipes for GitHub MCP and maybe Firecrawl MCP, clearly separated from default setup.

Longer term:

1. Consider an `engaku init --mcp-profile` design if optional server families grow.
2. Possible profiles: `default`, `github`, `web-research`, `cloud-aws`, `observability`.
3. Avoid adding token-requiring servers to default output unless they are disabled or opt-in.
