> Related task: post-v1.0 (no assigned plan_id yet)

# MCP Integration Design

## Background

Engaku's `engaku init` command currently writes `.github/` agent definitions,
`.github/instructions/`, and `.github/skills/`. Adding a `.vscode/mcp.json`
entry is a natural extension: it lets VS Code Copilot automatically discover and
launch MCP servers, giving agents structured tool access to browser automation,
live library documentation, and databases — all without the user running any
extra install commands.

This document records the research findings and design decisions from the
2026-04-20 design session. Implementation is deferred to the first release after
v1.0.

---

## Selected MCP Servers

### 1. chrome-devtools-mcp — Browser / DevTools

- **Repo**: https://github.com/ChromeDevTools/chrome-devtools-mcp
- **Maintained by**: Google Chrome DevTools team
- **License**: Apache-2.0
- **Stars**: ~36k
- **What it provides**: Puppeteer-backed browser control exposed as MCP tools —
  `take_screenshot`, `navigate_page`, `click`, `fill`, `evaluate_script`,
  `lighthouse_audit`, `performance_start_trace` / `stop_trace`,
  `list_network_requests`, and more (~25 tools total).
- **VS Code built-in substitute**: None. VS Code Copilot can fetch static URLs
  (`#web/fetch`) but cannot screenshot, click, run JS, or profile.
- **Configuration**: Zero. `npx -y chrome-devtools-mcp@latest --headless` — VS
  Code spawns and manages the process automatically.
- **Prerequisites**: Node.js (standard for frontend developers) + Chrome (standard).

```json
{
  "servers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--headless"]
    }
  }
}
```

**Skill**: `src/engaku/templates/skills/headless-browser/SKILL.md` — teaches
agents when to use each tool (screenshot for visual verification, lighthouse for
performance audits, navigate + snapshot for UI automation).

---

### 2. context7 — Live Library Documentation

- **Repo**: https://github.com/upstash/context7
- **Maintained by**: Upstash
- **License**: MIT
- **Stars**: ~53k
- **What it provides**: Two MCP tools — `resolve-library-id` (search by library
  name) and `query-docs` (fetch version-specific documentation snippets).
  Eliminates hallucinated or stale API usage; agent writes `use context7` in its
  prompt and gets accurate, current docs injected.
- **VS Code built-in substitute**: None. Copilot relies on training data which
  quickly becomes outdated for fast-moving libraries (React 19, Next.js 15, etc.).
- **Configuration**: Zero (free tier). Uses remote HTTP endpoint — no local
  process at all. Optional `CONTEXT7_API_KEY` header for higher rate limits.
- **Prerequisites**: None (HTTP remote mode).

```json
{
  "servers": {
    "context7": {
      "type": "http",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

For higher rate limits, users set `CONTEXT7_API_KEY` in their environment and
add the `headers` field.

**Skill**: `src/engaku/templates/skills/context7/SKILL.md` — teaches agents to
invoke context7 for any library/API question, providing the `use context7`
invocation pattern and example prompts.

---

### 3. dbhub — Multi-Database Access

- **Repo**: https://github.com/bytebase/dbhub
- **Maintained by**: Bytebase
- **License**: MIT
- **Stars**: ~2.6k
- **What it provides**: Two MCP tools — `execute_sql` and `search_objects` (schema
  exploration). Supports PostgreSQL, MySQL, MariaDB, SQL Server, and SQLite
  through a single interface. Read-only mode, row limits, and query timeout
  available as guardrails.
- **VS Code built-in substitute**: None. SQLTools extension exists but VS Code
  Copilot agent cannot call it.
- **Configuration**: **Required** — user must supply a `--dsn` connection string.
  This is the only server that cannot be shipped zero-config.
- **Prerequisites**: Node.js only.

```json
{
  "servers": {
    "dbhub": {
      "command": "npx",
      "args": ["@bytebase/dbhub@latest", "--dsn", "${input:dbDsn}"]
    }
  }
}
```

Because DSN is required, dbhub is written to `.vscode/mcp.json` as a disabled /
commented-out template entry with instructions, rather than being active by
default.

**Skill**: `src/engaku/templates/skills/database/SKILL.md` — teaches agents to
use `search_objects` before `execute_sql`, use read-only mode for exploration,
and format connection strings for each supported database.

---

## Servers Evaluated but Excluded

| Server | Reason excluded |
|--------|----------------|
| `server-fetch` (MCP official) | VS Code Copilot already has `#web/fetch` built-in; fully redundant |
| `server-git` (MCP official) | VS Code Copilot has complete native git integration |
| `server-filesystem` (MCP official) | VS Code already provides file read/edit/search to agents |
| `@modelcontextprotocol/server-memory` | Engaku's `.ai/` system already serves this purpose |
| GitHub MCP | Requires PAT token; not zero-config |
| `agent-browser` (Vercel Labs) | CLI-based, not MCP-native; better suited for non-VS Code agent environments |
| `webapp-testing` (Composio) | Generates Playwright scripts — good for E2E test authoring, but too heavy for general browser interaction |

---

## Implementation Plan (post-v1.0)

### Phase 1 — `.vscode/mcp.json` generation

`engaku init` writes `.vscode/mcp.json` with:
- `chrome-devtools` and `context7` **enabled by default**
- `dbhub` entry **present but commented/disabled**, with a `// Configure DSN to enable` note

If `.vscode/mcp.json` already exists, `engaku init` merges entries rather than
overwriting.

`engaku update` must also be able to add new server entries to an existing
`.vscode/mcp.json`.

### Phase 2 — Bundled skills

Three new skill directories under `src/engaku/templates/skills/`:
- `headless-browser/SKILL.md`
- `context7/SKILL.md`
- `database/SKILL.md`

Each is copied to `.github/skills/` by `engaku init` / `engaku update`.

### Phase 3 — CLI flag (opt-out)

`engaku init --no-mcp` skips `.vscode/mcp.json` generation for environments
where MCP is unwanted or already separately managed.

---

## Open Questions

1. Should `engaku init` prompt interactively for the dbhub DSN, or always write
   it as a disabled template?
2. Should context7 default to HTTP remote mode or stdio (`npx`) mode? Remote
   is simpler but adds a network dependency; stdio works offline.
3. Does VS Code `.vscode/mcp.json` support JSON comments (`//`) for the dbhub
   template, or do we need a separate readme note?
