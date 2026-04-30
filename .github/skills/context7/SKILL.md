---
name: context7
description: Live, version-specific library documentation via context7 MCP. Invoke resolve-library-id + query-docs for accurate, up-to-date API references.
user-invocable: true
disable-model-invocation: false
---

# Context7 MCP

Live, version-specific library docs. Eliminates hallucinated or stale API usage.

## When to use

- Library/API questions where training data may be outdated (React 19, Next.js 15, etc.).
- Unsure of the exact API signature, options, or breaking changes.
- User says "use context7" or asks for up-to-date docs.
- Before writing code against a specific library version's API.

## Tools

| Tool | Purpose |
|------|---------|
| `resolve-library-id` | Search by name → context7 ID |
| `query-docs` | Fetch version-specific docs for a resolved ID |

## Workflow

1. `resolve-library-id("react")` → `/facebook/react`.
2. `query-docs("/facebook/react", "useOptimistic hook API")`.
3. Use the returned docs in your response or code.

## Tips

- Always resolve first — never guess or hardcode IDs.
- Be specific in `query-docs` topics for focused results.
- Remote HTTP mode — needs network, no local process.
- Higher rate limits via `CONTEXT7_API_KEY` env var.
- Prefer context7 over training data for libraries with recent major releases.
