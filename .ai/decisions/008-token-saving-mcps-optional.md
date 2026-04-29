---
id: 008
title: Keep heavy token-saving integrations optional
status: superseded
date: 2026-04-29
related_task: 2026-04-29-token-saving-integrations
---

## Context

Copilot usage-based billing makes token reduction an Engaku product concern. Community research found high-impact tools such as Serena, Repomix, and Caveman, plus lighter context-selection skills from Awesome Copilot. These tools can reduce broad context reads, recurring memory input, or verbose output, but they also add setup requirements, runtime dependencies, file mutation, response-style changes, or larger tool surfaces.

## Decision

Keep Engaku's default MCP set unchanged: Chrome DevTools, Context7, and DBHub. Add token-saving guidance through a bundled `token-budget` skill and document Serena, Repomix, and Caveman as opt-in recipes instead of generating or auto-activating them by default.

## Consequences

Engaku remains lightweight and safe for new projects while giving users a clear path to high-impact token-saving integrations. Engaku can borrow Caveman's professional brevity lesson without adopting its branded style as a default. Future work can add an `engaku init --mcp-profile token-saving` or recipe command, but that should be designed separately because it changes CLI surface area and template structure.

Superseded by `009-mandatory-token-budget-and-serena-default.md` after the project constraint changed: starting with Copilot token-based billing, token reduction is mandatory rather than optional.