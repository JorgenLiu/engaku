---
plan_id: 2026-04-10-planner-boundary-fix
title: Tighten planner edit scope and fix dev task ownership
status: done
created: 2026-04-10
---

## Background

During the planner-redesign execution session, the planner agent directly edited
source files (`cmd_init.py`, `tests/test_init.py`, template agent files) instead
of writing a task plan and handing off to @dev. Root cause: the planner prompt's
"You do NOT" list is too narrow — it only prohibits "application or test code" and
`.ai/modules/`/`rules.md`, leaving all other source files implicitly editable.
A second violation occurred when planner again edited agent files in response to a
"make the boundaries clearer" request. See decision 001 for the root cause analysis.

Separately, `dev.agent.md` step 3 lists `.ai/tasks/` and `.ai/decisions/` as files
dev should update, conflicting with planner's declared ownership of those files.

## Design

Two targeted prompt fixes:

1. **planner.agent.md** — Replace vague "You do NOT" bullets with an explicit
   allowlist: the `edit` tool is only for `.ai/tasks/`, `.ai/decisions/`,
   `.ai/docs/`, and `.ai/overview.md`. Everything else is read-only for planner.

2. **dev.agent.md** — Remove `.ai/tasks/` and `.ai/decisions/` from step 3's
   file list; add an explicit prohibition pointing to @planner as owner.

Both fixes must be applied to the template file and the live `.github/` copy
in the same operation (per project rules).

## File Map

- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/dev.agent.md`
- Modify: `.github/agents/dev.agent.md`
- Create: `.ai/decisions/001-planner-edit-scope.md`

## Tasks

- [x] 1. **Tighten planner.agent.md "You do NOT" section**
  - Files: `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`
  - Steps:
    - In both files, replace the "You do NOT" block:

      Old:
      ```
      **You do NOT:**
      - Write application or test code
      - Modify `.ai/modules/` or `.ai/rules.md`
      ```

      New:
      ```
      **You do NOT:**
      - Write or modify source code, test files, or template files
      - Modify `.ai/modules/` or `.ai/rules.md`
      - Use `edit` outside `.ai/tasks/`, `.ai/decisions/`, `.ai/docs/`, and `.ai/overview.md`
      ```

  - Verify: `grep -A3 "You do NOT" src/engaku/templates/agents/planner.agent.md` —
    confirm all three bullets present, no mention of "application or test code"

- [x] 2. **Fix dev.agent.md step 3 — remove task/decision ownership**
  - Files: `src/engaku/templates/agents/dev.agent.md`, `.github/agents/dev.agent.md`
  - Steps:
    - In both files, replace step 3:

      Old:
      ```
      3. **Update project-level files** (`.ai/overview.md`, `.ai/rules.md`, `.ai/decisions/`, `.ai/tasks/`) if the changes affect architecture, constraints, or an in-progress plan.
      ```

      New:
      ```
      3. **Update project-level files** (`.ai/overview.md`, `.ai/rules.md`) if the changes affect architecture or constraints. Do NOT modify `.ai/tasks/` or `.ai/decisions/` — those are owned by @planner.
      ```

  - Verify: `grep "tasks" .github/agents/dev.agent.md` — should only appear in
    the "Do NOT" clause, not as a file to update

- [x] 3. **Write decision record 001**
  - Files: `.ai/decisions/001-planner-edit-scope.md`
  - Steps:
    - Create the file with the content specified in Appendix A below
  - Verify: `cat .ai/decisions/001-planner-edit-scope.md` — frontmatter parses,
    all three sections present

## Out of Scope

- Changes to any other agent files (knowledge-keeper, scanner, scanner-update)
- Changes to Python source code
- Backfilling existing task files

---

## Appendix A: `.ai/decisions/001-planner-edit-scope.md`

```markdown
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
```
