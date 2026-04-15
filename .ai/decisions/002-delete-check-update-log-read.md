---
id: 002
title: Delete check-update and log-read commands
status: accepted
date: 2026-04-15
related_task: 2026-04-15-v5-cleanup-and-publish
---

## Context

After V4 removed the module knowledge system, `check-update` became an empty
shell (reads stdin, checks `stop_hook_active`, returns 0). It runs as a Stop
hook on every agent turn, spawning a Python process that does nothing.

`log-read` writes `.ai/access.log` entries when PostToolUse reads `.ai/` files.
No command or workflow in engaku consumes this log. The data accumulates with
no consumer. Its test file (`test_log_read.py`) also uses pytest conventions
instead of the project's stdlib unittest standard.

Both commands cost a process spawn per agent turn with zero user-visible value.

## Decision

Delete both commands entirely: source files, test files, CLI entries, agent
hook references, and the orphaned supporting code they depended on
(`IGNORED_*` constants, `ACCESS_LOG`, `is_code_file()`,
`parse_transcript_edits()` and helpers).

If Stop-hook functionality is needed in the future, extend `task-review`
rather than resurrecting `check-update`.

## Consequences

- Dev agent Stop hook goes from 2 hooks to 1 (`task-review` only)
- Dev agent PostToolUse hook section is removed entirely
- `constants.py` shrinks to just `CONFIG_FILE`
- `utils.py` loses ~135 lines of dead transcript-parsing code
- Test count decreases (~20 tests removed), all remaining tests stay green
