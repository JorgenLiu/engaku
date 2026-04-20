# Multi-Task Injection Design

Related task: `2026-04-20-v110-bugfixes`

## Problem

`_find_active_task` returns only the first `status: in-progress` task
(alphabetically by filename). If two tasks are active simultaneously, the
second is silently ignored. This causes:

- **Coder** loses awareness of a second active task, potentially
  duplicating or conflicting work.
- **Reviewer** cannot discover tasks ready for verification unless they
  happen to be alphabetically first.
- **Planner** has an incomplete picture of in-flight work.

## Classification

A task with `status: in-progress` can be in one of two states:

| State | Condition | Meaning |
|-------|-----------|---------|
| `needs-work` | At least one `- [ ]` checkbox | Implementation incomplete |
| `needs-review` | All checkboxes are `[x]` (or none exist) | Coder finished; awaiting reviewer |

This distinction is important because:
- Coder should focus on `needs-work` tasks and avoid touching `needs-review`.
- Reviewer should focus on `needs-review` tasks.
- Planner needs to see both for awareness and re-planning.

## Why agent-agnostic injection

VS Code hook inputs vary by event:
- `SessionStart`: no agent identifier
- `PreCompact`: no agent identifier
- `SubagentStart`: includes `agent_type` (the agent name)
- `UserPromptSubmit`: no agent identifier

Since most hook events don't include agent identity, agent-aware filtering
would require either (a) only working for SubagentStart, or (b) passing
agent name via environment variables from the agent frontmatter (fragile,
not supported).

Instead, we inject all active tasks with clear state labels. Each agent's
system prompt already defines what it cares about:
- Coder: "You MAY tick completed task checkboxes" → works on `needs-work`
- Reviewer: "scan `.ai/tasks/` for files with `status: in-progress`" →
  verifies `needs-review`
- Planner: "You own `.ai/tasks/*.md`" → sees everything

## Output format

### SessionStart / UserPromptSubmit / SubagentStart

```xml
<active-tasks>
<task file="2026-04-20-feature.md" state="needs-work">
## Feature Title
- [ ] Step 3: Implement validator
- [ ] Step 4: Write tests
</task>
<task file="2026-04-18-refactor.md" state="needs-review">
## Refactor Title
All tasks completed. Awaiting reviewer verification.
</task>
</active-tasks>
```

### PreCompact

Same wrapper, but each task includes Background/Design/File Map + all
checkboxes (both `[x]` and `[ ]`), identical to current compact body
logic but applied per-task.

```xml
<active-tasks>
<task file="2026-04-20-feature.md" state="needs-work">
## Feature Title
## Background
...
## Design
...
## File Map
...
- [x] 1. Done step
- [ ] 2. Pending step
</task>
</active-tasks>
```

### No active tasks

No `<active-tasks>` block emitted (same as current behavior).

## Migration

The XML tag changes from `<active-task>` (singular) to `<active-tasks>`
(plural) with nested `<task>` elements. No agent prompt changes needed —
the agents parse these as context, not as structured data.
