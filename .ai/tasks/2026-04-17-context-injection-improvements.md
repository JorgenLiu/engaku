---
plan_id: 2026-04-17-context-injection-improvements
title: "Context injection improvements + reviewer commit + Release section"
status: done
created: 2026-04-17
---

## Background

Four weaknesses in the current context injection system were identified in
design review: PreCompact injects only unchecked task lines instead of the
full task body; UserPromptSubmit caps task steps at 5; there is no structured
gate preventing dev from executing irreversible release operations before
reviewer verification; and reviewer has no protocol for committing after a
successful verification. These changes address all four without introducing
new files, dependencies, or data stores.

## Design

### 1. PreCompact — inject task's key sections, not just unchecked lines

`PreCompact` fires before the compact model summarises the conversation.
Whatever we put in `systemMessage` is visible to that model and anchors its
summary. Currently we only send unchecked `- [ ]` lines, so the compact
summary loses Background, Design decisions, and completed progress.

New behaviour: inject `## Background`, `## Design`, `## File Map`, and all
checkbox lines (`[x]` and `[ ]`) from the active task. `## Out of Scope` and
per-step `Verify:` commands are excluded to keep size manageable.

A new helper `_extract_task_compact_body(body)` extracts these sections using
regex. `_find_active_task()` is extended to return the full body so both
callers (inject, prompt-check) can select the slice they need.

### 2. UserPromptSubmit — inject all remaining unchecked steps

Current `[:5]` slice was a conservative default. Removing it means the agent
always sees the full remaining work list on every turn, preventing it from
drifting toward already-completed steps.

### 3. `## Release` section in task format — structural gate for irreversible ops

A new optional section in task files gates all git-push / tag / publish
operations behind reviewer verification. planner puts irreversible operations
here instead of in `## Tasks`. dev's prompt explicitly forbids it from
executing anything under `## Release`. reviewer executes `## Release` steps
sequentially after all Tasks PASS, then sets `status: done`.

`task-review` (Stop hook) is unchanged — it only watches `## Tasks` checkboxes.

### 4. Reviewer — commit after all Tasks PASS

When all `## Tasks` are verified PASS, reviewer runs:
`git add -A && git commit -m "{task title}"` before setting `status: done`.
This replaces the ad-hoc pattern of dev committing mid-task.

If `## Release` exists in the task file, reviewer executes its steps in order
instead of a bare commit, then sets `status: done`.

Reviewer template and live file are always updated together per project convention.

## File Map

- Modify: `src/engaku/cmd_inject.py`
- Modify: `src/engaku/cmd_prompt_check.py`
- Modify: `.github/agents/dev.agent.md`
- Modify: `src/engaku/templates/agents/dev.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `tests/test_inject.py`
- Modify: `tests/test_prompt_check.py`

## Tasks

- [x] 1. **Extend `_find_active_task()` to return full task body**
  - Files: `src/engaku/cmd_inject.py`
  - Steps:
    - Change `_find_active_task()` return type from `(title, unchecked_lines)`
      to `(title, unchecked_lines, body)` where `body` is the full markdown
      body string after frontmatter
    - Add `_extract_task_compact_body(body)` that extracts and returns a string
      containing: `## Background` section, `## Design` section, `## File Map`
      section, and all lines matching `^\s*- \[[x ]\]` (both checked and
      unchecked). Use `re.search` per section with `re.MULTILINE | re.DOTALL`.
      Return empty string if none of these sections exist.
    - Update the `run()` call-site in `cmd_inject.py` that builds
      `<active-task>` to use `_extract_task_compact_body(body)` for
      `PreCompact` events, and unchecked lines only for `SessionStart` /
      `SubagentStart` (existing behaviour preserved)
  - Verify: `python -m pytest tests/test_inject.py -v`

- [x] 2. **Update `cmd_prompt_check.py` to inject all unchecked steps**
  - Files: `src/engaku/cmd_prompt_check.py`
  - Steps:
    - Import `_find_active_task` from `cmd_inject` or duplicate the lookup
      locally — check which pattern the file currently uses and keep it
      consistent
    - Remove the `[:5]` slice in `task_lines.extend(unchecked[:5])`, replacing
      with `task_lines.extend(unchecked)` to show all remaining steps
  - Verify: `python -m pytest tests/test_prompt_check.py -v`

- [x] 3. **Add tests for new inject behaviour**
  - Files: `tests/test_inject.py`
  - Steps:
    - Add a test for `_extract_task_compact_body`: fixture task body containing
      Background, Design, File Map, and mixed checkbox lines; assert returned
      string contains all four sections and both `[x]` and `[ ]` lines; assert
      it does NOT contain `## Out of Scope`
    - Add a test for PreCompact event: mock a task with Background + Design +
      checkboxes, call `run()` with `hookEventName: PreCompact` in stdin,
      assert `systemMessage` contains the Background text and both checkbox lines
    - Add a test for SessionStart event: same task, assert `additionalContext`
      contains only unchecked lines (existing behaviour)
  - Verify: `python -m pytest tests/test_inject.py -v`

- [x] 4. **Add tests for prompt-check uncapped behaviour**
  - Files: `tests/test_prompt_check.py`
  - Steps:
    - Add a task fixture with 8 unchecked steps
    - Assert the `systemMessage` output contains all 8 steps (previously only 5
      would appear)
  - Verify: `python -m pytest tests/test_prompt_check.py -v`

- [x] 5. **Update dev agent — forbid executing `## Release` section**
  - Files: `.github/agents/dev.agent.md`, `src/engaku/templates/agents/dev.agent.md`
  - Steps:
    - In the agent body, add a rule under the existing constraints: "Do NOT
      execute steps listed under `## Release` in any task file. That section is
      reserved for @reviewer to run after verification."
    - Update both live and template files in a single operation
  - Verify: `grep -n "Release" .github/agents/dev.agent.md src/engaku/templates/agents/dev.agent.md`

- [x] 6. **Update planner agent — document `## Release` section format**
  - Files: `.github/agents/planner.agent.md`, `src/engaku/templates/agents/planner.agent.md`
  - Steps:
    - In the task file format example, add `## Release` section after
      `## Out of Scope` with a comment explaining its purpose and showing
      example steps (commit, tag, push, publish)
    - Add a rule: "Place all irreversible operations (git push, git tag,
      PyPI publish, deployment commands) in `## Release`, never in `## Tasks`"
    - Update both live and template files in a single operation
  - Verify: `grep -n "Release" .github/agents/planner.agent.md src/engaku/templates/agents/planner.agent.md`

- [x] 7. **Update reviewer agent — commit + execute `## Release` after PASS**
  - Files: `.github/agents/reviewer.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`
  - Steps:
    - Change the "All tasks PASS" branch in "After verification" section:
      - If task has NO `## Release` section: run
        `git add -A && git commit -m "{task title from frontmatter}"` then set
        `status: done`
      - If task HAS `## Release` section: execute each `## Release` step in
        order (tick each `- [ ]` as it completes), then set `status: done`
    - Loosen the "Terminal for verification only" rule to explicitly permit
      commit and Release-section commands
    - Update both live and template files in a single operation
  - Verify: `grep -n "Release\|commit\|git add" .github/agents/reviewer.agent.md src/engaku/templates/agents/reviewer.agent.md`

- [x] 8. **Full test suite clean**
  - Files: (all test files)
  - Steps:
    - Run the full test suite and confirm zero failures
  - Verify: `python -m pytest tests/ -v`

## Out of Scope

- `task-review` Stop hook changes (currently only watches `## Tasks` — preserved)
- `cmd_task_review.py` logic changes
- learnings.jsonl mechanism (post-1.0, see decision doc)
- Python 3.11 migration (post-1.0, see decision doc)
- Reviewer handoff button changes

## Release
> Executed by @reviewer after all Tasks above are verified PASS.

- [x] R1. Bump version in `pyproject.toml` to `0.6.0`
- [x] R2. `git add -A && git commit -m "feat: v0.6.0 — context injection improvements + reviewer commit + Release section"`
- [x] R3. `git tag v0.6.0 && git push origin main --tags`
