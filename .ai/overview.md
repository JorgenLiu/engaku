# Project Overview

## Overview
Engaku is a Python CLI tool (stdlib only, >=3.8) that gives VS Code Copilot persistent memory via `.ai/` files and VS Code Agent Hooks. Six subcommands: `init`, `inject`, `prompt-check`, `task-review`, `apply`, `update`. Agent hooks cover `SessionStart`, `SubagentStart`, `PreCompact`, `UserPromptSubmit`, and `Stop`. Distributed via `pip install engaku` (PyPI) or `pip install git+https://github.com/JorgenLiu/engaku.git` (from source). V4 removed the module-knowledge system and replaced it with VS Code native `.instructions.md` files; `engaku init` now generates `.github/instructions/` stubs, `.github/skills/` from bundled templates, and `.vscode/mcp.json` with three preconfigured MCP servers (chrome-devtools, context7, dbhub) plus three matching skills. The planner agent owns task/decision/docs lifecycle; coder executes tasks and ticks progress checkboxes. `PreCompact` injects full task body (Background + Design + File Map + all checkboxes). `UserPromptSubmit` injects all remaining unchecked steps (no cap). Reviewer sets `status: done` after all Tasks PASS, then runs `git add -A && git commit`. v0.8.0 adds a failure-memory system (`lessons.instructions.md`, `applyTo: "**"`) and `SessionStart`/`PreCompact` hooks to all agents. v1.1.0 adds MCP server integration (`--no-mcp` flag to opt out). v1.1.4 adds a generated DBHub TOML template referenced from .vscode/mcp.json, plus a configurable hook Python interpreter via .ai/engaku.json: when python is set, engaku apply rewrites Engaku hook commands to use that interpreter with -m engaku. Engaku now generates an always-on agent boundary instruction to reinforce coder/planner/reviewer/scanner ownership.

## Directory Structure
    src/engaku/                CLI source — one cmd_*.py per subcommand
    src/engaku/templates/      Files copied by `engaku init` into target repos
    src/engaku/templates/instructions/  Stub .instructions.md files — lessons.instructions.md and agent-boundaries.instructions.md (applyTo: **)
    src/engaku/templates/skills/        Bundled skills (systematic-debugging, verification-before-completion, frontend-design, proactive-initiative, mcp-builder, doc-coauthoring, brainstorming, chrome-devtools, context7, database)
    src/engaku/templates/mcp.json       MCP server config template (.vscode/mcp.json)
    tests/                     stdlib unittest tests, one file per command
    docs/                      Design docs and implementation plan
    .ai/                       This project's own knowledge (bootstrapped by engaku init)
    .github/                   Agent definitions, instructions, and skills for this repo
