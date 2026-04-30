---
id: 014
title: Targeted Caveman rewrite with deferred hook cleanup
status: accepted
date: 2026-04-30
related_task: 2026-04-30-planner-caveman-rewrite-audit
---

## Context
The planner agent still contains stale artifact wording, and the user requested a Caveman-style rewrite of the planner prompt plus the selected global-policy surfaces: `copilot-instructions`, `lessons.instructions`, `agent-boundaries.instructions`, and `.ai/overview.md`. GitHub's custom agent configuration reference for GitHub.com, Copilot CLI, and supported IDEs lists supported YAML frontmatter properties and does not include `hooks:`, which makes the current hook frontmatter a compatibility concern. The user explicitly chose to keep that third issue as a recorded risk rather than fold schema cleanup into this pass.

## Decision
Use a targeted rewrite scope for this round: planner live/template, `copilot-instructions` live/template, `lessons.instructions` live/template, `agent-boundaries.instructions` live/template, and `.ai/overview.md`. Rewrite those files around the existing Caveman-inspired compactness model and remove the stale planner sentence `Not every conversation needs all three.` Do not change `hooks:` frontmatter in this round; keep it documented as a separate compatibility issue for a follow-up plan.

## Consequences
The resulting implementation plan stays small and reviewable, and it only touches the files the user named. The stale planner wording and the selected global-policy drift can be fixed now without reopening all agent files. `hooks:` compatibility with Copilot CLI remains unresolved after this work and should be handled in a separate plan that can decide whether to remove, relocate, or gate hook-related configuration.
