---
name: serena
description: "Symbol-level code navigation via Serena MCP. Use for semantic code navigation, symbol lookup, finding references, renames, large codebase exploration, and token-saving code reads instead of broad file reads."
argument-hint: "Describe the symbol, reference, or refactor you need (file is optional — Serena indexes the workspace)."
user-invocable: true
disable-model-invocation: false
---

# Serena

Serena is a language-server-backed MCP server that exposes symbol-level
operations (definitions, references, renames, symbol search) so the agent does
not have to read whole files just to locate one function or type.

Engaku registers Serena as a default MCP server because symbol-level reads are
the largest single source of input-token savings on real projects.

---

## 1. Default MCP command

Engaku's `.vscode/mcp.json` ships Serena as a `stdio` server with:

```
serena start-mcp-server --context=vscode --project ${workspaceFolder}
```

VS Code must be able to find the `serena` executable. `engaku setup-serena`
patches the absolute path when possible so PATH issues do not break the server.

## 2. Setup

Recommended:

```
engaku setup-serena
```

This is also run automatically by `engaku init` unless `--skip-serena-setup`
or `--no-mcp` is passed.

Manual fallback:

```
pip install uv          # or:  python -m pip install uv
uv tool install -p 3.13 serena-agent@latest --prerelease=allow
serena init
```

After installation, restart VS Code so the MCP client picks up Serena.

## 3. When to use Serena

Prefer Serena over broad file reads when you need to:

- locate a symbol's definition
- enumerate references / call sites
- inspect a class, function, or type signature
- rename a symbol across the workspace
- explore an unfamiliar large codebase

For raw file content (READMEs, configs, build output), continue with the
normal read tools.

## 4. Fallback behavior

If Serena tools are unavailable in this session:

1. Continue the task with VS Code's built-in search and read tools.
2. Tell the user how to finish setup:
   - run `engaku setup-serena`, or
   - install manually per section 2 and restart VS Code.
3. Do not block the task on Serena availability.

## 5. Token-budget alignment

Serena exists to support the rules in the `token-budget` skill:

- context map first → use Serena to confirm the right symbol before reading
- bounded reads → fetch the symbol, not the whole file
- English-by-default professional brevity in any summary the agent emits
