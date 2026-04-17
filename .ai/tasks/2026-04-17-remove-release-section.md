---
plan_id: 2026-04-17-remove-release-section
title: "Remove ## Release section, simplify reviewer protocol"
status: done
created: 2026-04-17
---

## Background

The `## Release` section in task files creates an irreconcilable paradox:
reviewer must tick each step as it completes, but the commit step itself
produces a new change (the tick), which is never committed. This chase
condition cannot be closed. The solution is to remove `## Release` entirely,
move version bumps and changelog into normal `## Tasks` (dev executes), and
have reviewer do a single commit after all tasks PASS. Irreversible ops
(tag, push, publish) are left to the user or CI.

## Design

1. **Remove `## Release`** from planner's task file format and quality rules.
2. **Add version-bump guidance to planner** — when the task warrants a
   version bump, planner includes it as a normal task step (dev edits
   `pyproject.toml`, `__init__.py`, `CHANGELOG.md`). Planner also
   pre-writes the specific `.ai/overview.md` update text as a task step
   when the work changes architecture, subcommands, hooks, or directory
   structure.
3. **Simplify reviewer protocol** — all tasks PASS → set `status: done` →
   `git add -A && git commit -m "{task title}"`. No branching logic.
4. **Remove dev's `## Release` prohibition** — no longer needed.
5. **Update copilot-instructions.md** — remove any Release-related rules.
6. **Both live and template files** updated in each task per project convention.

## File Map

- Modify: `.github/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `.github/agents/dev.agent.md`
- Modify: `src/engaku/templates/agents/dev.agent.md`
- Modify: `.github/copilot-instructions.md`
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `src/engaku/__init__.py`
- Modify: `pyproject.toml`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Remove `## Release` from planner agent — task format and rules**
  - Files: `.github/agents/planner.agent.md`, `src/engaku/templates/agents/planner.agent.md`
  - Steps:
    - In the task file format example, delete the entire `## Release` block
      (from `## Release` through `- [ ] R3. {publish command}`)
    - In "Task quality rules", delete the bullet about irreversible ops
      in `## Release`
    - Add a new bullet to "Task quality rules": "When completed work will
      change `.ai/overview.md` content (project architecture, directory
      structure, or major features), include an overview update step with
      the exact new text."
    - Update both live and template files identically
  - Verify: `grep -c "Release" .github/agents/planner.agent.md` (expect 0)

- [x] 2. **Simplify reviewer agent — remove Release branching**
  - Files: `.github/agents/reviewer.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`
  - Steps:
    - Replace the "After verification" section's "All tasks PASS" block
      (both branches) with a single action: set `status: done` in the task
      doc first, then run
      `git add -A && git commit -m "{task title from frontmatter}"`
      (so the committed snapshot already shows the final done state)
    - In Rules, simplify the terminal rule to: "Terminal for verification
      and commit only. During verification, never run commands that modify
      project state. After all tasks PASS, run the commit command above."
    - Update both live and template files identically
  - Verify: `grep -c "Release" .github/agents/reviewer.agent.md` (expect 0)

- [x] 3. **Remove `## Release` prohibition from dev agent**
  - Files: `.github/agents/dev.agent.md`, `src/engaku/templates/agents/dev.agent.md`
  - Steps:
    - Delete the numbered item "2. **Do NOT execute steps listed under
      `## Release`…**" from both live and template files
    - Renumber remaining items if needed (currently only item 1 remains,
      so numbering can be dropped)
  - Verify: `grep -c "Release" .github/agents/dev.agent.md` (expect 0)

- [x] 4. **Update copilot-instructions.md — remove Release-related rules**
  - Files: `.github/copilot-instructions.md`, `src/engaku/templates/copilot-instructions.md`
  - Steps:
    - In the live file, check for any bullets mentioning `## Release`
      or irreversible operations gated by reviewer; remove them if found
    - The template file currently has no Release references — confirm and
      leave unchanged
  - Verify: `grep -c "Release" .github/copilot-instructions.md` (expect 0)

- [x] 5. **Bump version to 0.7.0 and update CHANGELOG**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Change `version = "0.6.0"` to `version = "0.7.0"` in `pyproject.toml`
    - Change `__version__ = "0.6.0"` to `__version__ = "0.7.0"` in
      `src/engaku/__init__.py`
    - Add `## [0.7.0] — 2026-04-17` section to top of CHANGELOG with:
      - Removed: `## Release` section from task file format — irreversible
        ops (tag, push, publish) are now user/CI responsibility
      - Changed: Reviewer protocol simplified to a single commit after all
        tasks PASS (no more Release-section branching)
      - Changed: Version bumps and changelog edits are now normal task steps
        executed by dev
  - Verify: `python3 -c "import engaku; assert engaku.__version__ == '0.7.0'"`

- [x] 6. **Update README and overview**
  - Files: `README.md`, `.ai/overview.md`
  - Steps:
    - In `.ai/overview.md`, replace the sentence about `## Release` with:
      "Version bumps and changelog edits are normal task steps; reviewer
      commits after all Tasks PASS; irreversible ops (tag, push, publish)
      are left to the user or CI."
    - In `README.md`, no changes needed (README does not mention Release) —
      confirm with grep
  - Verify: `grep -c "Release" .ai/overview.md` (expect 0)

- [x] 7. **Full test suite clean**
  - Files: (all test files)
  - Steps:
    - Run the full test suite and confirm zero failures
  - Verify: `python -m pytest tests/ -v`

## Out of Scope

- `cmd_task_review.py` logic changes (does not parse `## Release`)
- `cmd_inject.py` changes (does not reference `## Release`)
- ADR creation (this is a simplification, not a new architecture decision)
- New test cases (no Python code changes beyond version bump)
