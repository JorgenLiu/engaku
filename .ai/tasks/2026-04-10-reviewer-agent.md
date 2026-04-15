---
plan_id: 2026-04-10-reviewer-agent
title: Introduce reviewer agent and automate task verification
status: done
created: 2026-04-10
---

## Background

Task lifecycle ownership is currently split poorly: planner both plans and reviews,
creating unnecessary manual friction (user must switch to planner, ask it to audit,
and wait for it to set `status: done`). Dev has no way to signal "I finished, please
verify" except by narrating it. The solution is a dedicated reviewer agent — the
sole authority for `status: done` and failed-checkbox resets — triggered via a
one-click handoff button after dev finishes all tasks.

## Design

- **reviewer.agent.md** — `user-invocable: true`, Sonnet, tools: `read/search/execute/edit`.
  Verification protocol from `verification-before-completion` skill: run command →
  read output → decide PASS/FAIL. All PASS → `status: done`. Any FAIL → reset `[x]`
  to `[ ]` with inline note, leave `status: in-progress`. Edit scope strictly limited
  to `.ai/tasks/*.md`.
- **planner.agent.md** — Remove entire "Task review" section. Remove `status: done`
  authority. Planner retains `status: abandoned` (planning decision, not verification).
  Planner becomes a pure planning/analysis/design agent.
- **dev.agent.md** — Add `handoffs` entry ("Verify Tasks (1 premium request)",
  `send: true`) pointing to reviewer. Add `engaku task-review` to Stop hooks. Update
  `status:` ownership note from @planner to @reviewer.
- **cmd_task_review.py** — New Stop hook command. Scans `.ai/tasks/` for
  `status: in-progress` files where `## Tasks` section has `[x]` entries but no `[ ]`
  entries. If found, outputs `systemMessage` prompting the user to use the handoff.
  Guards against `stop_hook_active` loop. Never blocks.
- **engaku init** — copies `reviewer.agent.md` alongside existing agents.

## File Map

- Create: `src/engaku/templates/agents/reviewer.agent.md`
- Create: `.github/agents/reviewer.agent.md`
- Create: `src/engaku/cmd_task_review.py`
- Create: `tests/test_task_review.py`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/dev.agent.md`
- Modify: `.github/agents/dev.agent.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cli.py`
- Modify: `tests/test_init.py`

## Tasks

- [x] 1. **Create reviewer.agent.md (template + live)**
  - Files: `src/engaku/templates/agents/reviewer.agent.md`, `.github/agents/reviewer.agent.md`
  - Steps:
    - Create template file with frontmatter:
      ```yaml
      ---
      name: reviewer
      user-invocable: true
      tools: ['read', 'search', 'execute', 'edit']
      description: >-
        Task verification agent. Verifies completed tasks against their
        acceptance criteria, updates task document status.
      ---
      ```
    - Body must include these sections, in order:
      - **Ownership** — owns `status:` field and checkbox resets in `.ai/tasks/*.md`
        only. Does NOT create/restructure task plans, touch modules/rules/decisions/docs,
        or modify source code.
      - **How you work (invoked without specific instructions)** — scan `.ai/tasks/`
        for `status: in-progress` files; if multiple, list and ask which to review.
      - **Verification protocol** — For each `[x]` task: (1) find its verification
        command, (2) run it now (do not trust prior output), (3) read full output +
        exit code, (4) compare against expected outcome. Report format per task:
        `Verified with: {cmd} / Result: {summary} / Verdict: PASS | FAIL`.
      - **After verification** — All PASS → set `status: done`. Any FAIL → reset
        `[x]` to `[ ]`, add inline HTML comment with failure reason (e.g.
        `<!-- verify failed: pytest exited 1 -->`), leave `status: in-progress`.
      - **Rules** — Evidence only, no "should work". One task at a time. Do NOT
        fix failing code. Terminal for verification only, never modify project state.
        Edit scope: `.ai/tasks/*.md` exclusively.
    - Create live file at `.github/agents/reviewer.agent.md` with identical content
      (template and live must match — no model override needed since template already
      declares the model).
  - Verify: `diff src/engaku/templates/agents/reviewer.agent.md .github/agents/reviewer.agent.md`
    — files must be identical.

- [x] 2. **Implement cmd_task_review.py**
  - Files: `src/engaku/cmd_task_review.py`
  - Steps:
    - Module docstring: "engaku task-review / Stop hook: detect when all tasks in
      an in-progress plan are checked, emit systemMessage to use the Verify Tasks
      handoff."
    - `_extract_tasks_section(body)` — regex to extract content between `## Tasks`
      and the next `##` heading (or EOF). Use
      `re.search(r'^## Tasks\s*\n(.*?)(?=\n^## |\Z)', body, re.MULTILINE | re.DOTALL)`.
    - `_all_tasks_checked(tasks_section)` — returns True if
      `re.findall(r'^- \[x\]', section, re.MULTILINE)` is non-empty AND
      `re.findall(r'^- \[ \]', section, re.MULTILINE)` is empty.
    - `_find_completed_task_file(cwd)` — scan `.ai/tasks/*.md` (sorted descending
      by filename), parse frontmatter, skip non-`in-progress` files, return relative
      path of first file where `_all_tasks_checked` is True, else None.
    - `run()` — read hook input; if `stop_hook_active` is True, return 0. Call
      `_find_completed_task_file(cwd)`. If None, return 0. Otherwise output:
      ```json
      {"systemMessage": "All tasks in {path} are marked complete. Click 'Verify Tasks (1 premium request)' to run verification."}
      ```
    - `main(argv=None)` — `sys.exit(run())`
  - Verify: `python -c "import ast; ast.parse(open('src/engaku/cmd_task_review.py').read()); print('ok')"`

- [x] 3. **Register task-review subcommand in cli.py**
  - Files: `src/engaku/cli.py`
  - Steps:
    - Add parser entry after the `subagent-start` block:
      ```python
      # engaku task-review
      subparsers.add_parser(
          "task-review",
          help="Detect all-complete task plans and emit handoff reminder (Stop hook)",
      )
      ```
    - Add dispatch branch after the `subagent-start` elif:
      ```python
      elif args.command == "task-review":
          from engaku.cmd_task_review import run
          sys.exit(run())
      ```
  - Verify: `engaku task-review --help` — exits 0, shows help text.

- [x] 4. **Write tests for cmd_task_review.py**
  - Files: `tests/test_task_review.py`
  - Steps:
    - `setUp` creates a temp dir with `.ai/tasks/` structure.
    - Test `_extract_tasks_section`: body with `## Tasks\n- [x] 1.\n## Out of Scope`
      returns only the tasks content, not the Out of Scope section.
    - Test `_all_tasks_checked`: all `[x]` → True; mix of `[x]` and `[ ]` → False;
      no checkboxes → False; only `[ ]` → False.
    - Test `_find_completed_task_file`: (a) no tasks dir → None; (b) one
      `in-progress` file with all `[x]` → returns path; (c) one `in-progress` file
      with a `[ ]` → None; (d) `status: done` file with all `[x]` → None (skip
      non-in-progress); (e) `## Tasks` section with all `[x]` but `## Out of Scope`
      has a `[ ]` → True (only tasks section scanned).
    - Test `run()`: `stop_hook_active: true` → exit 0, no stdout; no task files →
      exit 0; in-progress all-checked file → exit 0, stdout contains `systemMessage`.
  - Verify: `python -m pytest tests/test_task_review.py -v` — all tests pass.

- [x] 5. **Update planner.agent.md — remove Task review section**
  - Files: `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`
  - Steps:
    - In both files, delete the entire `## Task review` section (from `## Task review`
      heading through the end of step 5 "When all tasks are verified complete…").
    - In the `status` values note under Task file format, change:
      `status` values: `in-progress`, `done`, `abandoned`.`
      to:
      `` `status` values: `in-progress`, `abandoned`. (`done` is set by @reviewer after verification.) ``
    - In Principles, replace the Terminal bullet to add context that planner
      may not change any `status:` field — add: `**No status edits** — @reviewer
      is the sole authority for \`status: done\`. Planner may set \`status: abandoned\`
      only for plans that will not be executed.`
  - Verify: `grep -n "Task review\|status: done\|Only planner sets" src/engaku/templates/agents/planner.agent.md`
    — must return no matches.

- [x] 6. **Update dev.agent.md — add handoff + hook + ownership**
  - Files: `src/engaku/templates/agents/dev.agent.md`, `.github/agents/dev.agent.md`
  - Steps:
    - In both files, add `handoffs` to the YAML frontmatter (after `hooks`):
      ```yaml
      handoffs:
        - label: "Verify Tasks (1 premium request)"
          agent: reviewer
          prompt: >-
            Review the most recent in-progress task plan in .ai/tasks/.
            Verify each task marked [x] by running its verification command.
            Report PASS/FAIL per task with evidence.
          send: true
      ```
    - In the `hooks.Stop` list, add after `engaku check-update`:
      ```yaml
          - type: command
            command: engaku task-review
            timeout: 5
      ```
    - In step 3 of the prompt body, change the ownership note from
      "@planner's responsibility" to "@reviewer's responsibility". Change:
      `Do NOT modify `.ai/decisions/` or change the `status:` field or structure of
      `.ai/tasks/` files — those are @planner's responsibility.`
      to:
      `Do NOT modify `.ai/decisions/` or change the `status:` field or structure of
      `.ai/tasks/` files — `status:` is @reviewer's responsibility; task structure
      is @planner's responsibility.`
  - Verify: `grep -n "reviewer\|task-review\|Verify Tasks" src/engaku/templates/agents/dev.agent.md`
    — all three strings must appear.

- [x] 7. **Update cmd_init.py to copy reviewer.agent.md**
  - Files: `src/engaku/cmd_init.py`
  - Steps:
    - In the agents loop, add `"reviewer.agent.md"` to the filename list:
      ```python
      for name in ("dev.agent.md", "knowledge-keeper.agent.md", "planner.agent.md",
                   "reviewer.agent.md", "scanner.agent.md", "scanner-update.agent.md"):
      ```
  - Verify: `python -c "import ast; ast.parse(open('src/engaku/cmd_init.py').read()); print('ok')"`

- [x] 8. **Update test_init.py expected files**
  - Files: `tests/test_init.py`
  - Steps:
    - Add `os.path.join(".github", "agents", "reviewer.agent.md")` to the
      `EXPECTED_FILES` list (keep alphabetical order within the agents entries).
  - Verify: `python -m pytest tests/test_init.py -v` — all tests pass.

- [x] 9. **Run full test suite**
  - Steps:
    - `python -m pytest tests/ -v`
  - Verify: all tests pass, zero failures.

## Out of Scope

- Changing reviewer's model to Opus — Sonnet is the designated model.
- Adding reviewer to `dev.agent.md`'s `agents:` list for subagent use — reviewer
  is triggered via handoff, not as a subagent dispatched by dev.
- Modifying `engaku validate` to check task files.
- Any changes to knowledge-keeper, scanner, or scanner-update agents.
