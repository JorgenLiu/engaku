---
id: 012
title: Remove default Serena and use strict agent frontmatter
status: accepted
date: 2026-04-29
related_task: 2026-04-29-remove-serena-and-agent-schema-fixes
---

## Context
Serena setup failed in VS Code with `Error spawn serena ENOENT`, and package metadata confirms `serena-agent` requires Python >=3.11 while Engaku supports Python >=3.8. Keeping Serena as a default creates environment setup behavior that is too surprising for the current release. Copilot CLI also rejects Engaku-generated agent frontmatter where `model` is written as a YAML array, even though VS Code documentation allows arrays; GitHub's custom agents configuration reference defines `model` as a string for GitHub.com, Copilot CLI, and supported IDEs.

## Decision
Remove all current-version Serena integration from generated configuration, live repository configuration, CLI commands, tests, and user-facing documentation. Keep Engaku's MCP defaults to Chrome DevTools, Context7, and DBHub only. Generate and maintain custom agent `model` frontmatter as a single string, not an array, because the GitHub/Copilot CLI schema is stricter and this remains valid for VS Code.

## Consequences
Engaku no longer auto-installs or configures Serena, and `engaku setup-serena` is removed from the current command surface. Future symbol-level navigation support can return only behind an explicit opt-in design that does not affect Python 3.8 compatibility or default initialization. Agent templates and `engaku apply` must avoid `selection` and array-valued `model` frontmatter so Copilot diagnostics stay clean.