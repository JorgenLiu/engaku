---
name: mcp-builder
description: "Guide building MCP servers in Python (FastMCP) or TypeScript. Use when the user asks to build an MCP server or integrate an external API/service via MCP."
argument-hint: "Describe the MCP server to build: what API or service it wraps, which language (Python/TypeScript), and any constraints."
user-invocable: true
disable-model-invocation: false
---

# MCP Server Builder

Build Model Context Protocol (MCP) servers that expose tools, resources, and prompts to AI assistants.

## Workflow

Follow these four phases in order. Do not skip phases.

---

### Phase 1 — Research

Before writing any code, gather the information needed to build the server.

1. **Understand the MCP specification.** Fetch the MCP docs sitemap for reference:
   - URL: `https://modelcontextprotocol.io/sitemap.xml`
   - Focus on: transport types, tool/resource/prompt schemas, error handling conventions.

2. **Read the SDK README for the chosen language.**
   - TypeScript SDK: fetch `https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md`
   - Python SDK: fetch `https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md`

3. **Study the target API or service.**
   - Read the API documentation or SDK for the service the MCP server will wrap.
   - Identify the key operations, authentication method, rate limits, and data shapes.

4. **Produce a brief design note** listing:
   - Tools to expose (name, description, input schema).
   - Resources to expose, if any.
   - Transport choice (stdio for CLI, SSE for networked).
   - Auth strategy (env var, OAuth, API key).

Do not proceed to Phase 2 until the design note is reviewed.

---

### Phase 2 — Implement

#### Python (FastMCP)

```
pip install mcp         # installs FastMCP
```

Skeleton:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(param: str) -> str:
    """One-line description shown to the model."""
    # Implementation here
    return result
```

Key conventions:
- One `@mcp.tool()` per operation. Keep tools focused — prefer many small tools over few large ones.
- Use Python type hints for parameters; FastMCP derives the JSON Schema automatically.
- Raise `McpError` for user-visible errors; let unexpected exceptions propagate.
- Use `@mcp.resource("protocol://path")` for read-only data the model can pull.
- Use `@mcp.prompt()` for reusable prompt templates.

#### TypeScript (MCP SDK)

```
npm install @modelcontextprotocol/sdk
```

Skeleton:

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

Key conventions:
- Use Zod schemas for input validation.
- Return `content` arrays with typed blocks (`text`, `image`, `resource`).
- Use `server.resource()` for read-only data.
- Use `server.prompt()` for reusable templates.

#### General Design Principles

- **Naming**: Use `snake_case` for tool names. Names should be verb-noun: `get_issue`, `create_branch`, `search_docs`.
- **Descriptions**: Write descriptions as if explaining the tool to a colleague. The model reads them to decide when to call the tool.
- **Idempotency**: Prefer idempotent operations. Document side effects clearly.
- **Error handling**: Return structured error messages. Include enough context for the model to retry or ask the user for clarification.
- **Authentication**: Read secrets from environment variables. Never hardcode credentials. Document required env vars in the README.
- **Rate limiting**: Implement client-side rate limiting if the upstream API enforces limits.

---

### Phase 3 — Review

Before declaring the server complete, verify:

1. **Does each tool have a clear, accurate description?** The model relies on descriptions to select the right tool.
2. **Are input schemas correct and complete?** Missing or wrong types cause silent failures.
3. **Are errors handled gracefully?** Test with invalid inputs, missing auth, network failures.
4. **Is the README complete?** It should include: install instructions, required env vars, example usage, and a list of exposed tools/resources.
5. **Does the server start and respond?** Run it locally and test with the MCP Inspector or a simple client.

---

## Quick Reference

| Concept | Python (FastMCP) | TypeScript (SDK) |
|---------|-------------------|-------------------|
| Define tool | `@mcp.tool()` | `server.tool(name, schema, handler)` |
| Define resource | `@mcp.resource(uri)` | `server.resource(name, template, handler)` |
| Define prompt | `@mcp.prompt()` | `server.prompt(name, args, handler)` |
| Start server | `mcp.run()` | `server.connect(transport)` |
| Error type | `McpError` | throw in handler |

## Token Budget

- Answer in English by default; switch language only when explicitly requested.
- Read only the SDK pieces needed for the capability in scope.
- Do not summarize the entire MCP spec when one tool, prompt, or transport is the actual subject.
