---
name: context7
description: Live, version-specific library documentation via context7 MCP. Invoke resolve-library-id + query-docs for accurate, up-to-date API references.
user-invocable: true
disable-model-invocation: false
---

# Context7 MCP

Use the context7 MCP server to fetch live, version-specific library documentation. This eliminates hallucinated or stale API usage by providing accurate, current docs directly from the source.

## When to use

- Any library or API question where training data may be outdated (React 19, Next.js 15, new framework releases, etc.).
- When you are unsure about the exact API signature, available options, or breaking changes in a recent version.
- When the user asks to "use context7" or requests up-to-date documentation.
- Before writing code that depends on a specific library version's API.

## Tools

| Tool | Purpose |
|------|---------|
| `resolve-library-id` | Search for a library by name and get its context7 ID |
| `query-docs` | Fetch version-specific documentation snippets for a resolved library |

## Workflow

1. **Resolve the library**: call `resolve-library-id` with the library name (e.g. "react", "nextjs", "express").
2. **Query documentation**: call `query-docs` with the resolved library ID and your specific question or topic.
3. **Use the result**: incorporate the returned documentation into your response or code.

## Example patterns

```
# Find the library ID for React
resolve-library-id("react")
# → returns library ID, e.g. "/facebook/react"

# Query specific API docs
query-docs("/facebook/react", "useOptimistic hook API")
# → returns current documentation for useOptimistic
```

## Tips

- Always resolve the library ID first — do not guess or hardcode IDs.
- Be specific in your `query-docs` topic to get focused, relevant results.
- Context7 uses HTTP remote mode — no local process needed, but requires network access.
- For higher rate limits, users can set `CONTEXT7_API_KEY` in their environment.
- Prefer context7 over training data whenever a library has had recent major releases.

## Token Budget

- Answer in English by default; switch language only when explicitly requested.
- Resolve the exact library and version first, then query one specific topic.
- Do not pull general overviews when a specific API question is the goal; bound queries to the symbol or feature in scope.
