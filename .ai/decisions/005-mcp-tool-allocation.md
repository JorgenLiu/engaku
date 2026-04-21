---
id: 005
title: "MCP tool allocation strategy for agents"
status: accepted
date: 2026-04-20
related_task: 2026-04-20-mcp-tool-allocation
---

## Context

v1.1.0 added `.vscode/mcp.json` with three MCP servers (chrome-devtools,
context7, dbhub) but did not grant any agents permission to invoke them. VS Code
requires explicit `<server>/*` entries in an agent's `tools:` frontmatter for
MCP tool access.

## Decision

MCP tool grants are managed via a `mcp_tools` section in `.ai/engaku.json`
and injected into agent frontmatter by `engaku apply`. This keeps agent
templates MCP-free and makes allocation user-configurable without editing agent
files directly.

Default allocation:
- **coder**: all three servers (builds UI, uses libraries, touches DB)
- **planner**: context7 + dbhub (designs with accurate docs and schema awareness)
- **reviewer**: chrome-devtools + dbhub (visual verification + DB state checks)
- **scanner**: none (codebase-only analysis)

`engaku init` auto-runs `apply` after setup. `engaku update` auto-runs `apply`
after force-copying templates. Users who add custom MCP servers edit `mcp_tools`
manually and run `engaku apply`.

## Consequences

- `engaku.json` becomes the single authority for both model and tool config.
- Agent template files remain static; all per-repo customization lives in config.
- `engaku apply` gains a second responsibility (tools in addition to model).
- Backward compatible: configs without `mcp_tools` key trigger no-op behaviour.
