---
id: 009
title: Mandatory token budget and Serena default
status: superseded
date: 2026-04-29
related_task: 2026-04-29-token-saving-integrations
---

## Context

Copilot's move to token-based billing changes token reduction from an optional optimization into a project constraint. Caveman shows that substantial output-token savings can come from terse, substance-preserving communication, and `caveman-compress` shows that recurring natural-language memory files can be compressed when guarded carefully. Serena provides symbol-level code navigation through MCP and is the strongest candidate for reducing broad code reads in large repositories.

## Decision

Make token-budget behavior mandatory across Engaku agents and skills. Engaku should internalize Caveman's principle as professional brevity: preserve technical substance, code, commands, paths, evidence, and decisions, but remove filler, repeated summaries, hedging, and unnecessary prose. Add Serena to the default generated MCP configuration and default MCP tool assignments for coding/review/planning roles, with documentation that users must install and initialize Serena separately because Engaku must not auto-install third-party runtimes.

## Consequences

Engaku's generated customization files will carry a short always-on token-budget rule, and detailed behavior will live in a bundled `token-budget` skill. The default MCP set grows from Chrome DevTools, Context7, and DBHub to include Serena, so `engaku init`, `engaku update`, `.ai/engaku.json`, tests, and README docs must all be updated. Serena failures must degrade gracefully: if the `serena` command is not installed or the MCP server fails to start, agents continue using VS Code/search tools and report setup guidance instead of blocking work.

Superseded by `010-default-serena-bootstrap-and-english-budget.md` after deciding Engaku should provide a default Serena setup flow and generated agents should answer in English by default.