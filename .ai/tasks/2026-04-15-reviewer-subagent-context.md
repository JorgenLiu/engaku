---
plan_id: 2026-04-15-reviewer-subagent-context
title: Enhance reviewer with SubagentStart context injection
status: done
created: 2026-04-15
---

## Background

When @dev hands off to @reviewer via the `handoffs` mechanism, the reviewer
agent starts as a subagent with a blank context — it only receives the handoff
prompt and whatever the reviewer's own instructions say. It has no awareness of
the project overview, the active task plan, or recent session context. This
means reviewer must manually scan `.ai/tasks/` and `.ai/overview.md` every
time, wasting tokens and risking incomplete context.

VS Code 1.115 introduced `SubagentStart` hooks, which fire when a subagent is
spawned and can inject `additionalContext` into the subagent's conversation.
By adding a SubagentStart hook to the reviewer agent, we can pre-load the
active task plan and project overview so reviewer starts with full context.

## Design

Two options were considered:

**Option A: Agent-scoped SubagentStart hook on reviewer.agent.md**
Add a `hooks.SubagentStart` entry to reviewer's frontmatter that calls
`engaku inject SubagentStart`. This only fires when reviewer is spawned as a
subagent.

**Option B: Workspace-level SubagentStart hook in .github/hooks/**
Add a SubagentStart hook that fires for all subagents and injects context
universally.

**Chosen: Option A** — more targeted, only reviewer needs the injection.
Other subagents (like planner) have their own distinct context needs.

The `cmd_inject.py` module needs a minor change: it currently only handles
`SessionStart` and `PreCompact`. It must also handle `SubagentStart`, which
uses the same `hookSpecificOutput.additionalContext` pattern as SessionStart
but with `hookEventName: "SubagentStart"`.

## File Map

- Modify: `src/engaku/cmd_inject.py`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `tests/test_inject.py`

## Tasks

- [x] 1. **Add SubagentStart event handling to cmd_inject.py**
  - Files: `src/engaku/cmd_inject.py`
  - Steps:
    - In the event branching logic (around line 84), add `SubagentStart` as a case that produces `hookSpecificOutput` with `hookEventName: "SubagentStart"` and `additionalContext` — same structure as SessionStart but different hookEventName
    - Update the cli.py help text for the inject subcommand to mention SubagentStart
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -c "import engaku.cmd_inject; print('import ok')"`

- [x] 2. **Add SubagentStart hook to reviewer agent template**
  - Files: `src/engaku/templates/agents/reviewer.agent.md`, `.github/agents/reviewer.agent.md`
  - Steps:
    - Add a `hooks:` field to reviewer's YAML frontmatter (reviewer currently has no hooks)
    - Add `SubagentStart` entry: `type: command`, `command: engaku inject`, `timeout: 5`
    - Both files must be identical (except .github version may have a `model:` field)
  - Verify: `grep -A3 SubagentStart src/engaku/templates/agents/reviewer.agent.md && grep -A3 SubagentStart .github/agents/reviewer.agent.md`

- [x] 3. **Add test for SubagentStart injection**
  - Files: `tests/test_inject.py`
  - Steps:
    - Add a test method that feeds `{"hookEventName": "SubagentStart"}` as stdin to `cmd_inject.run()` and asserts the output JSON contains `hookSpecificOutput.hookEventName == "SubagentStart"` and `hookSpecificOutput.additionalContext` containing the overview content
    - Pattern: follow the existing test structure (mock stdin, capture stdout, parse JSON)
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -m pytest tests/test_inject.py -q`

- [x] 4. **Verify end-to-end that reviewer gets context when spawned**
  - Files: (none — manual verification)
  - Steps:
    - In a test workspace with `.ai/overview.md` and an in-progress task in `.ai/tasks/`, invoke @reviewer via @dev's handoff
    - Check that reviewer's first response references the project context and active task without having to scan files
    - Alternatively, run `echo '{"hookEventName":"SubagentStart","cwd":"/tmp/test"}' | engaku inject` and verify JSON output
  - Verify: `echo '{"hookEventName":"SubagentStart"}' | cd /Users/jordan.liu/dev/engaku && python -m engaku inject 2>/dev/null | python -c "import sys,json; d=json.load(sys.stdin); assert d['hookSpecificOutput']['hookEventName']=='SubagentStart'; print('OK')"`

## Out of Scope

- SubagentStop hooks (no current use case for reviewer).
- SubagentStart hooks for other agents (planner, scanner).
- Changes to the reviewer's verification protocol or instructions.
- Workspace-level hooks in `.github/hooks/`.
