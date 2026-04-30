---
id: 011
title: Token budget as always-on instruction
status: superseded
date: 2026-04-29
related_task: 2026-04-29-token-budget-instruction-redesign
---

## Context

The prior token-budget implementation placed the full workflow in a `token-budget` skill and repeated short token-budget sections in generated agents and bundled skills. Session debug logs showed that skills are only discovered as metadata until the model chooses to read their `SKILL.md`, and newly created skills may not be present in the active session until rediscovery. Upstream Caveman succeeds because it defines an always-active compact response mode with concrete style operations and explicit clarity exceptions.

## Decision

Engaku will move default token-budget behavior out of skills and into a generated always-on instruction file: `.github/instructions/token-budget.instructions.md`, copied from `src/engaku/templates/instructions/token-budget.instructions.md` with `applyTo: "**"`. This instruction will contain Engaku-authored compact-mode rules inspired by Caveman's mechanics: terse technical prose, fragments allowed, filler and hedging removed, exact technical content preserved, and normal clear English used for safety-critical or ambiguity-prone cases.

The bundled `token-budget` skill will be removed because it suggests an automatic trigger that skills cannot guarantee. Token-budget sections will also be removed from all domain skills and agent bodies. The Serena skill and MCP setup remain because Serena is domain-specific code-navigation guidance rather than a universal communication policy.

## Consequences

Token discipline becomes reliably loaded in every generated workspace instead of depending on skill invocation. Skills become smaller and return to domain-specific workflows. The default prompt gains one always-on instruction file, so the instruction must be compact and avoid duplicating the same policy in agents, skills, and copilot instructions. The prior decision's Serena setup remains accepted, while its approach of distributing token-budget policy through skills is superseded.