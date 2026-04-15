---
plan_id: 2026-04-10-task-lifecycle-clarity
title: Clarify task lifecycle ownership between planner and dev
status: done
created: 2026-04-10
---

## Background

After the boundary-fix session, `.ai/tasks/` is fully locked from dev, but this
creates a gap: nobody ticks checkboxes during execution, so the task file gives
no progress signal until planner does a review pass. The correct split is:
dev ticks individual checkboxes as mechanical progress tracking during execution;
planner holds exclusive authority over `status:` and task structure, and performs
acceptance review (verify → approve or reset). Neither agent's prompt currently
describes this division precisely.

Separately, `.ai/overview.md` does not mention `.ai/docs/` (created by `engaku
init` as of the planner-redesign task) and does not describe the planner agent's
role in the project.

## Design

**Dev prompt (step 3):** Replace the blanket prohibition on `.ai/tasks/` with a
nuanced rule: dev MAY tick `[ ]` → `[x]` after completing each step, but must NOT
touch `status:`, create/delete task files, or change task structure or decisions.

**Planner prompt (Task review section):** Make the acceptance authority explicit.
Add a fork in the review procedure: verified → leave `[x]`; not verified →
reset to `[ ]` with an inline note. State explicitly that only planner sets
`status: done`.

**overview.md:** Add `.ai/docs/` to Directory Structure. Add one sentence
describing the planner agent's role (no handoff, owns task/decision/docs lifecycle).

All agent file changes must update template + live copy in the same operation.

## File Map

- Modify: `src/engaku/templates/agents/dev.agent.md`
- Modify: `.github/agents/dev.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Update dev.agent.md step 3 — allow checkbox-ticking only**
  - Files: `src/engaku/templates/agents/dev.agent.md`, `.github/agents/dev.agent.md`
  - Steps:
    - In both files, replace step 3:

      Old:
      ```
      3. **Update project-level files** (`.ai/overview.md`, `.ai/rules.md`) if the
      changes affect architecture or constraints. Do NOT modify `.ai/tasks/` or
      `.ai/decisions/` — those are owned by @planner.
      ```

      New:
      ```
      3. **Update project-level files** (`.ai/overview.md`, `.ai/rules.md`) if the
      changes affect architecture or constraints. Do NOT modify `.ai/decisions/` or
      change the `status:` field or structure of `.ai/tasks/` files — those are
      @planner's responsibility. You MAY tick completed task checkboxes `[ ]` → `[x]`
      as you finish each step.
      ```

  - Verify: `grep -A3 "Update project-level" .github/agents/dev.agent.md` —
    confirm "MAY tick" is present and "Do NOT modify `.ai/tasks/`" is gone

- [x] 2. **Update planner.agent.md Task review — add acceptance fork**
  - Files: `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`
  - Steps:
    - In both files, replace the "When reviewing an existing plan:" block:

      Old:
      ```
      When reviewing an existing plan:

      1. Read the task file from `.ai/tasks/`.
      2. Check actual project state against each task's expected outcome —
         read files, run verification commands, inspect git history.
      3. Update checkboxes and status based on evidence.
      4. If scope has changed, revise the Tasks section but preserve
         Background and Design.
      5. When all tasks are complete, set `status: done`.
      ```

      New:
      ```
      When reviewing an existing plan:

      1. Read the task file from `.ai/tasks/`.
      2. Check actual project state against each task's expected outcome —
         read files, run verification commands, inspect git history.
      3. For each task @dev has ticked `[x]`: verify the stated outcome holds.
         - Verified: leave `[x]` as-is.
         - Not verified: reset to `[ ]` and add a brief inline note explaining
           what failed (e.g. `- [ ] 2. **Title** <!-- verify failed: reason -->`).
      4. If scope has changed, revise the Tasks section but preserve
         Background and Design.
      5. When all tasks are verified complete, set `status: done`. Only planner
         sets this field — dev never changes `status:`.
      ```

  - Verify: `grep -A12 "When reviewing an existing plan" .github/agents/planner.agent.md` —
    confirm "Not verified" fork and "Only planner sets this field" are present

- [x] 3. **Update .ai/overview.md**
  - Files: `.ai/overview.md`
  - Steps:
    - Add `.ai/docs/` line to Directory Structure, after `.ai/`:
      ```
          .ai/              This project's own knowledge (bootstrapped by engaku init)
          .ai/docs/         Design documents and analysis (owned by planner agent)
          .github/          Agent definitions for this repo
      ```
    - Append one sentence to the Overview paragraph:
      `The planner agent owns task/decision/docs lifecycle and performs acceptance
      review; dev executes tasks and ticks progress checkboxes.`
  - Verify: `grep "docs" .ai/overview.md` — line present

- [x] 4. **Verify template/live sync and run tests**
  - Steps:
    - `diff <(grep -v '^model:' .github/agents/dev.agent.md) src/engaku/templates/agents/dev.agent.md`
    - `diff <(grep -v '^model:' .github/agents/planner.agent.md) src/engaku/templates/agents/planner.agent.md`
    - `python -m pytest tests/ -q`
  - Verify: both diffs empty, all tests pass

## Out of Scope

- Changes to knowledge-keeper, scanner, scanner-update agents
- Changing who creates task files (still planner only)
- Changing dev's ability to touch `.ai/decisions/` (still prohibited)
