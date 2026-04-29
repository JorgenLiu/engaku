---
id: 010
title: Default Serena bootstrap and English token budget
status: accepted
date: 2026-04-29
related_task: 2026-04-29-token-saving-integrations
---

## Context

Token-based Copilot billing makes the token-saving setup path part of Engaku's default experience. Official uv documentation confirms `pip install uv` is supported, though isolated installs such as `pipx` or the standalone installer are preferred. Serena documentation recommends installing with `uv tool install -p 3.13 serena-agent@latest --prerelease=allow`, then running `serena init`, and configuring VS Code workspace MCP with `serena start-mcp-server --context=vscode --project ${workspaceFolder}`. Caveman full mode is an English compression rule set that drops filler, articles, pleasantries, and hedging while preserving technical terms, code, and exact error text.

## Decision

Engaku should make Serena setup an idempotent first-class workflow instead of only documenting manual steps. Add an `engaku setup-serena` command and have `engaku init` run it by default when MCP is enabled, with a skip flag for offline/no-network environments. The setup flow should detect `serena`, detect or install `uv` using `python -m pip install uv` as a fallback, run `uv tool install -p 3.13 serena-agent@latest --prerelease=allow`, run `serena init`, discover the concrete `serena` executable path, and write that path into `.vscode/mcp.json` so VS Code does not depend on shell PATH discovery. The implementation must not assume `pip install uv` updates PATH; it must locate executables through `shutil.which`, Python script directories, and uv tool directories, and every external command must run with a timeout.

Generated agents and skills should answer in English by default using a professional Caveman-full-inspired style: short fragments are acceptable, filler and pleasantries are removed, technical terms/code/commands/errors stay exact, and normal clear English is used for security warnings, irreversible actions, ordered multi-step instructions, or when the user explicitly asks for detail. Chinese can remain available only when the user explicitly requests Chinese-language output; Engaku defaults should be English to match existing project constraints and Caveman's strongest compression mode. The bundled `skill-authoring` workflow must also require every newly authored skill to include this token-budget style, so future user-authored skills do not drift back into verbose defaults.

## Consequences

`engaku init` gains network and environment-touching behavior by default, so failures must never break project initialization. The setup flow must be idempotent, visible, and non-destructive: if installation or initialization fails, Engaku still writes MCP config and prints exact recovery commands. Tests should mock subprocess calls rather than installing uv or Serena. The English default must be stated compactly across generated instructions, agents, skills, and skill-authoring output rules so the rule saves tokens instead of adding more always-on context.