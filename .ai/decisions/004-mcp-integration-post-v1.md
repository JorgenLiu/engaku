---
id: 004
title: "MCP server integration deferred to post-v1.0"
status: accepted
date: 2026-04-20
related_task: none
---

## Context

A design session on 2026-04-20 evaluated four MCP servers for integration into
`engaku init`: `chrome-devtools-mcp`, `context7`, `dbhub`, and `server-fetch`.
Three of these (`chrome-devtools-mcp`, `context7`, `dbhub`) were confirmed as
genuinely additive — no VS Code built-in equivalent exists for any of them.
`server-fetch` was excluded as fully redundant with VS Code Copilot's native
`#web/fetch` capability.

The integration requires changes to `cmd_init.py`, `cmd_update.py`, a new
`.vscode/mcp.json` template, and three new bundled skills. This scope is not
appropriate for the v1.0 release, which is intended to be a stable, minimal
milestone.

## Decision

MCP server integration is deferred to the first release **after** v1.0.

v1.0 ships **without** any `.vscode/mcp.json` generation or MCP-related skills.

The detailed design is recorded in `.ai/docs/mcp-integration.md`.

The three servers accepted for future integration are:
- **chrome-devtools-mcp** — browser automation, DevTools, performance profiling
- **context7** — live library documentation (remote HTTP, zero local process)
- **dbhub** — multi-database access (PostgreSQL, MySQL, MariaDB, SQL Server, SQLite)

## Consequences

- v1.0 remains a clean, focused release with no new moving parts.
- The post-v1.0 MCP release will also coincide with the Python 3.11 version bump
  (see decision 003), giving it a natural version boundary.
- Users who want MCP before the official release can follow `.ai/docs/mcp-integration.md`
  to configure `.vscode/mcp.json` manually.
