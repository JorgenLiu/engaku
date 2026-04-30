---
plan_id: 2026-04-30-session-start-compactness-hook
title: Add hook compactness reminders to Engaku inject
status: done
created: 2026-04-30
---

## Background
The previous interrupted reply showed that static global instructions alone are not enough to keep agents anchored on Caveman-style compactness at session boundaries. The same drift can happen across compaction and subagent handoff. Engaku already has `SessionStart`, `PreCompact`, and `SubagentStart` hooks wired to `engaku inject`; this work makes those hooks useful even when no project overview or active task exists.

## Design
Reuse `engaku inject` and add one small compactness reminder block for `SessionStart`, `PreCompact`, and `SubagentStart`. The block should be short, imperative, and lossless: latest user request wins after interruption, use compact output, preserve exact technical evidence, send one concise tool preamble, and report only delta/next action after read-only context batches. Keep each event's existing output shape and context semantics; do not create a new CLI command or duplicate hook registrations in agent templates.

## File Map
- Create: `.ai/decisions/015-session-start-compactness-reminder.md`
- Modify: `src/engaku/cmd_inject.py`
- Modify: `tests/test_inject.py`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Add failing hook reminder tests**
  - Files: `tests/test_inject.py`
  - Steps:
    - Update `test_no_files_produces_empty_context` so SessionStart with no `.ai/overview.md` or active tasks expects a non-empty compactness reminder.
    - Update PreCompact empty-context coverage so `systemMessage` contains the compactness reminder when no project/task context exists.
    - Add or update SubagentStart empty-context coverage so `additionalContext` contains the compactness reminder when no project/task context exists.
    - Add assertions that the reminder contains exact anchors for latest request, Lossless Compactness, exact evidence, and concise tool preambles.
  - Verify: `python -m unittest tests.test_inject`

- [x] 2. **Inject compactness reminder on hook events**
  - Files: `src/engaku/cmd_inject.py`
  - Steps:
    - Add a small constant or helper for the compactness reminder block.
    - Include the reminder for effective events `SessionStart`, `PreCompact`, and `SubagentStart`.
    - Preserve existing project context and active task ordering after the reminder.
    - Preserve output shapes: `SessionStart`/`SubagentStart` use `hookSpecificOutput.additionalContext`; `PreCompact` uses `systemMessage`.
    - Keep stdout as valid JSON and preserve `ensure_ascii=False`.
  - Verify: `python -m unittest tests.test_inject`

- [x] 3. **Record overview change**
  - Files: `.ai/overview.md`
  - Steps:
    - Append this exact sentence to the Overview paragraph: `v1.1.12 makes the existing SessionStart, PreCompact, and SubagentStart inject hooks emit a short compactness reminder even when no project overview or active task exists, anchoring resumed, compacted, and delegated contexts on latest-user-request priority, Lossless Compactness, exact evidence, and concise tool preambles while preserving each hook's existing output shape.`
    - Do not change directory structure unless implementation adds or removes files.
  - Verify: `rg -n "v1.1.12 makes the existing SessionStart, PreCompact, and SubagentStart inject hooks" .ai/overview.md`

- [x] 4. **Run focused verification**
  - Files: `src/engaku/cmd_inject.py`, `tests/test_inject.py`, `.ai/overview.md`
  - Steps:
    - Run focused inject tests.
    - Run full unittest discovery to catch hook regressions.
    - Inspect diff for accidental changes outside the file map.
  - Verify: `python -m unittest tests.test_inject && python -m unittest discover -s tests && git --no-pager diff --name-only | cat`

## Out of Scope
- Adding a new `engaku session-start` subcommand.
- Changing agent template hook frontmatter or `engaku apply` hook rewriting.
- Changing `UserPromptSubmit` or `Stop` hook behavior.
- Copying Caveman upstream text or adding Caveman as a dependency.
