---
name: mcp-builder
description: "Guide building MCP servers in Python (FastMCP) or TypeScript. Use when the user asks to build an MCP server or integrate an external API/service via MCP."
context: fork
argument-hint: "Describe the MCP server to build: what API or service it wraps, which language (Python/TypeScript), and any constraints."
user-invocable: true
disable-model-invocation: false
---

# MCP Server Builder

Build Model Context Protocol servers exposing tools, resources, and prompts to AI assistants.

## Workflow

Three phases, in order. Don't skip.

---

### Phase 1 — Research

Before writing code:

1. **MCP spec** — fetch sitemap `https://modelcontextprotocol.io/sitemap.xml`. Focus: transport types, tool/resource/prompt schemas, error conventions.
2. **SDK README** for chosen language:
   - TypeScript: `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
   - Python: `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`
3. **Target API/service** — read its docs/SDK; identify operations, auth, rate limits, data shapes.
4. **Design note** listing:
   - Tools (name, description, input schema)
   - Resources, if any
   - Transport (stdio for CLI, SSE for networked)
   - Auth strategy (env var, OAuth, API key)

Don't proceed until the design note is reviewed.

---

### Phase 2 — Implement

#### Python (FastMCP)

```
pip install mcp         # installs FastMCP
```

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(param: str) -> str:
    """One-line description shown to the model."""
    return result
```

- One `@mcp.tool()` per operation. Many small tools > few large ones.
- Type hints → FastMCP derives JSON Schema.
- Raise `McpError` for user-visible errors; let unexpected exceptions propagate.
- `@mcp.resource("protocol://path")` for read-only data.
- `@mcp.prompt()` for reusable templates.

#### TypeScript (MCP SDK)

```
npm install @modelcontextprotocol/sdk
```

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "my-server", version: "1.0.0" });

server.tool("my_tool", { param: z.string() }, async ({ param }) => ({
  content: [{ type: "text", text: result }],
}));

const transport = new StdioServerTransport();
await server.connect(transport);
```

- Zod schemas for input validation.
- Return `content` arrays with typed blocks (`text`, `image`, `resource`).
- `server.resource()` for read-only data; `server.prompt()` for templates.

#### Design Principles

- **Naming**: `snake_case`, verb-noun (`get_issue`, `create_branch`, `search_docs`).
- **Descriptions**: model uses them to choose tools — write as if explaining to a colleague.
- **Idempotency**: prefer idempotent ops; document side effects clearly.
- **Errors**: structured messages with context for retry/clarification.
- **Auth**: secrets from env vars. Never hardcode. Document required vars in README.
- **Rate limiting**: client-side limiting if upstream enforces.

---

### Phase 3 — Review

Before declaring complete:

1. Each tool has a clear, accurate description (model uses it for selection).
2. Input schemas correct and complete.
3. Errors handled gracefully (test invalid inputs, missing auth, network failures).
4. README covers install, env vars, example usage, exposed tools/resources.
5. Server starts and responds — test locally with MCP Inspector or a simple client.

---

## Quick Reference

| Concept | Python (FastMCP) | TypeScript (SDK) |
|---------|-------------------|-------------------|
| Tool | `@mcp.tool()` | `server.tool(name, schema, handler)` |
| Resource | `@mcp.resource(uri)` | `server.resource(name, template, handler)` |
| Prompt | `@mcp.prompt()` | `server.prompt(name, args, handler)` |
| Start | `mcp.run()` | `server.connect(transport)` |
| Error | `McpError` | throw in handler |
