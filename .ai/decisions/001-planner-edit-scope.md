---
id: 001
title: Planner edit scope limited to .ai document files only
status: accepted
date: 2026-04-10
related_task: 2026-04-10-planner-boundary-fix
---

## Context

During task execution the planner agent directly edited source files
(cmd_init.py, test files, agent template files) instead of writing a plan for
@dev to execute. The planner prompt's `tools` list includes `edit`, which is
needed for writing `.ai/tasks/`, `.ai/decisions/`, and `.ai/docs/` files. But the
"You do NOT" prohibition was too narrow, leaving all other files implicitly editable.
A second violation occurred immediately after when planner again edited agent files
in response to a boundary-clarification request.

## Decision

The planner prompt's "You do NOT" section gains an explicit allowlist rule:
`edit` is only permitted for `.ai/tasks/`, `.ai/decisions/`, `.ai/docs/`, and
`.ai/overview.md`. All other files are effectively read-only for planner.
The dev prompt's step 3 removes `.ai/tasks/` and `.ai/decisions/` from its update
list, adding an explicit "owned by @planner" prohibition to eliminate ambiguity.

## Consequences

- Planner will never directly modify source, test, or template files.
- Dev will never write to task or decision files; it reads them for context only.
- The two agents have non-overlapping write domains going forward.
- Any future addition of `edit` capabilities to planner must explicitly name the
  allowed target paths.
