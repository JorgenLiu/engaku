---
id: 013
title: Global Engaku kernel in Copilot instructions
status: accepted
date: 2026-04-30
related_task: 2026-04-30-global-kernel-caveman-compactness
---

## Context
Engaku needs policy that loads for every Copilot turn: agent boundaries, lossless compactness, and generated-artifact writing style. The prior design put token-budget behavior in `.github/instructions/token-budget.instructions.md`, but live sessions showed that broad `.instructions.md` policy is weaker than expected when competing with agent, tool, and review instructions. Caveman demonstrates an effective always-on compression protocol, and its Copilot guidance points users toward custom instructions for auto-activation rather than relying on skill loading.

## Decision
Engaku's global kernel will live in `.github/copilot-instructions.md` and its template. The kernel will contain compact agent boundaries, Caveman-inspired lossless compactness, and generated-artifact style rules for docs, prompts, skills, agents, and instructions. Engaku will not copy Caveman's skill body into each agent prompt and will not install Caveman by default; it will use Engaku-authored rules inspired by Caveman's principles and keep Caveman as an optional user tool.

`.github/instructions/*.instructions.md` remains for path-specific conventions. Agent files remain role workflows. Hooks remain dynamic state injection: overview, active tasks, and compact/PreCompact context.

## Consequences
The generated token-budget instruction is retired, and decision 011 is superseded. Global behavior becomes easier to reason about because one unconditional file owns universal policy. Existing agent, skill, and instruction templates must be rewritten for lossless compactness so future generated artifacts stop carrying filler, repeated rationale, and soft style guidance.