---
id: 007
title: Bundle a Skill Authoring Skill Before a Dedicated Skill-Creator Agent
status: accepted
date: 2026-04-28
related_task: 2026-04-28-workflow-to-skill-v118
---

## Context

The earlier skill-creator design concluded that turning workflows into skills
should be implemented as a dedicated custom agent. The immediate need is smaller:
the user wants repeated work patterns to be captured as reusable skills in the
v1.1.8 timeframe. VS Code's current customization documentation positions skills
as the right primitive for portable multi-step workflows, while reserving custom
agents for persistent personas with tool restrictions or handoffs.

One motivating example is a reusable planner workflow: inspect selected database
tables, inspect related code modules based on those findings, then write a
module-by-module modification plan. That is a reusable method with intermediate
state, not merely a fixed prompt template.

## Decision

Engaku will add a bundled `skill-authoring` skill for v1.1.8 instead of adding a
new `skill-creator` agent. The skill will guide an implementation-capable agent
through primitive selection, user interview, SKILL.md drafting, validation, and a
small test loop. It will explicitly route fixed single-command templates toward
prompt files and route multi-step adaptive workflows toward skills. A full
skill-creator agent with tester subagents remains a future option if the
lightweight skill proves insufficient.

## Consequences

This keeps v1.1.8 small: one new skill template, registration in `init` and
`update`, focused tests, README/CHANGELOG/version updates, and an overview update.
It avoids new agent boundaries, new model defaults, or dependency changes. The
main limitation is that authoring and testing run inside the active agent rather
than an isolated skill-creator workflow.

Only the `skill-authoring` template itself is Engaku-managed. Skills produced by
using it are user-owned project or personal customizations and must not be added
to Engaku's bundled template list, `_SKILLS`, `cmd_init.py`, or `cmd_update.py`
unless the user explicitly asks to ship that specific skill as part of Engaku.
