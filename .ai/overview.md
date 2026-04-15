# Project Overview

## Overview
Engaku is a Python CLI tool (stdlib only, >=3.8) that gives VS Code Copilot persistent memory via `.ai/` files and VS Code Agent Hooks. Five subcommands: `init`, `inject`, `prompt-check`, `task-review`, `apply`. Agent hooks cover `SessionStart`, `PreCompact`, `UserPromptSubmit`, and `Stop`. Distributed via `pip install engaku` (PyPI) or `pip install git+https://...`. V4 removed the module-knowledge system and replaced it with VS Code native `.instructions.md` files; `engaku init` now generates `.github/instructions/` stubs and `.github/skills/` from bundled templates. The planner agent owns task/decision/docs lifecycle; dev executes tasks and ticks progress checkboxes.

## Directory Structure
    src/engaku/                CLI source — one cmd_*.py per subcommand
    src/engaku/templates/      Files copied by `engaku init` into target repos
    src/engaku/templates/instructions/  Stub .instructions.md files (3 stubs)
    src/engaku/templates/skills/        Bundled skills (systematic-debugging, verification-before-completion, frontend-design)
    tests/                     stdlib unittest tests, one file per command
    docs/                      Design docs and implementation plan
    .ai/                       This project's own knowledge (bootstrapped by engaku init)
    .github/                   Agent definitions, instructions, and skills for this repo
