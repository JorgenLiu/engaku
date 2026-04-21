---
plan_id: 2026-04-20-mcp-tool-allocation
title: "MCP tool allocation for agents"
status: done
created: 2026-04-20
---

## Background

`engaku init` creates `.vscode/mcp.json` with three MCP servers (chrome-devtools,
context7, dbhub) and corresponding skill files, but agents lack `<server>/*`
entries in their `tools:` frontmatter, preventing them from invoking MCP tools.
This plan extends `engaku.json` with a `mcp_tools` config section and makes
`engaku apply` inject the appropriate MCP tool grants into each agent.

## Design

### Tool allocation matrix

| Agent    | chrome-devtools | context7 | dbhub |
|----------|-----------------|----------|-------|
| coder    | ✅              | ✅       | ✅    |
| planner  | ❌              | ✅       | ✅    |
| reviewer | ✅              | ❌       | ✅    |
| scanner  | ❌              | ❌       | ❌    |

### `engaku.json` gains `mcp_tools`

```json
{
  "agents": { ... },
  "mcp_tools": {
    "coder": ["chrome-devtools/*", "context7/*", "dbhub/*"],
    "planner": ["context7/*", "dbhub/*"],
    "reviewer": ["chrome-devtools/*", "dbhub/*"]
  }
}
```

Agents not listed (or with an empty array) receive no MCP tool grants.

### `engaku apply` behaviour

1. Read `mcp_tools` from config (default `{}`).
2. For each agent file in `.github/agents/`:
   - Parse `tools:` line from YAML frontmatter.
   - Strip any existing `*/` entries (MCP server wildcards).
   - Append entries from `mcp_tools[agent_name]` if present.
   - Write back the updated `tools:` line.
3. This is idempotent — safe to run repeatedly.

### `cmd_init.py` changes

- Generate `engaku.json` programmatically instead of copying a static template.
  Include `mcp_tools` section when MCP is enabled (default); omit it when
  `--no-mcp`.
- Call `apply` logic at the end of `run()` so freshly created agents have
  model + MCP tools injected immediately.

### `cmd_update.py` changes

- Call `apply` logic at the end of `run()` so force-copied agents get model +
  MCP tools re-injected.

### User workflow for custom MCP servers

Users who add their own servers to `.vscode/mcp.json` manually edit `mcp_tools`
in `.ai/engaku.json` to grant them to agents, then run `engaku apply`.

## File Map

- Modify: `src/engaku/templates/ai/engaku.json`
- Modify: `src/engaku/cmd_apply.py`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `tests/test_apply.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `.ai/engaku.json` (this repo's own config)

## Tasks

- [x] 1. **Update `engaku.json` template with `mcp_tools`**
  - Files: `src/engaku/templates/ai/engaku.json`
  - Steps:
    - Add `"mcp_tools"` key with coder/planner/reviewer allocations per design matrix.
  - Verify: `python -c "import json; d=json.load(open('src/engaku/templates/ai/engaku.json')); assert 'mcp_tools' in d; assert len(d['mcp_tools']['coder'])==3"`

- [x] 2. **Add MCP tool injection to `cmd_apply.py`**
  - Files: `src/engaku/cmd_apply.py`
  - Steps:
    - Add `_update_agent_tools(agent_path, mcp_tools_list)` function that:
      - Reads frontmatter
      - Finds the `tools:` line
      - Strips existing entries matching `*/` pattern (MCP wildcards)
      - Appends new MCP entries from config
      - Writes back
    - In `run()`, after the model loop, add a second loop reading `mcp_tools` from config and calling `_update_agent_tools` for each agent.
  - Verify: `python -m pytest tests/test_apply.py -v`

- [x] 3. **Write unit tests for MCP tool injection in `cmd_apply.py`**
  - Files: `tests/test_apply.py`
  - Steps:
    - Test: agent with no prior MCP entries gets them added.
    - Test: agent with stale MCP entries gets them replaced.
    - Test: agent not in `mcp_tools` config keeps tools unchanged.
    - Test: config without `mcp_tools` key → no-op (backward compat).
  - Verify: `python -m pytest tests/test_apply.py -v`

- [x] 4. **Make `cmd_init.py` generate `engaku.json` conditionally**
  - Files: `src/engaku/cmd_init.py`
  - Steps:
    - Replace the `_copy_template` call for `engaku.json` with a `_write_engaku_json(cwd, no_mcp, out)` helper that:
      - Skips if `.ai/engaku.json` already exists (preserve user edits)
      - Generates JSON with `agents` dict (same defaults)
      - Conditionally includes `mcp_tools` section (omit if `no_mcp`)
      - Writes the file
    - At the end of `run()`, import and call `cmd_apply.run(cwd)` (silently).
  - Verify: `python -m pytest tests/test_init.py -v`

- [x] 5. **Make `cmd_update.py` call `apply` at end**
  - Files: `src/engaku/cmd_update.py`
  - Steps:
    - At the end of `run()`, after printing summary, call `cmd_apply.run(cwd)`.
  - Verify: `python -m pytest tests/test_update.py -v`

- [x] 6. **Update `test_init.py` for MCP tool injection**
  - Files: `tests/test_init.py`
  - Steps:
    - Add test: default init → agents have MCP tools in frontmatter.
    - Add test: `--no-mcp` init → agents have no MCP tools in frontmatter.
    - Add test: `engaku.json` content matches expected shape for both modes.
  - Verify: `python -m pytest tests/test_init.py -v`

- [x] 7. **Update `test_update.py` for post-apply**
  - Files: `tests/test_update.py`
  - Steps:
    - Add test: after `update`, agents have model + MCP tools re-injected.
  - Verify: `python -m pytest tests/test_update.py -v`

- [x] 8. **Apply config to this repo**
  - Files: `.ai/engaku.json`
  - Steps:
    - Add `mcp_tools` section matching the design matrix.
    - Run `engaku apply` to inject MCP tools into `.github/agents/`.
  - Verify: `grep 'chrome-devtools' .github/agents/coder.agent.md && grep 'context7' .github/agents/planner.agent.md && ! grep '/' .github/agents/scanner.agent.md | grep -v '//'`

## Out of Scope

- Auto-detection of MCP servers from `mcp.json` (users manually edit `mcp_tools`)
- Per-tool granularity (we use `<server>/*` wildcard only)
- Modifying the agent template files themselves (they stay MCP-free; injection is config-driven)
- Adding new MCP servers beyond the current three
