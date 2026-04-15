# Stale Module Reminder — Implementation Plan

## Goal

Reduce the frequency of missed `knowledge-keeper` calls at session end without
consuming extra premium-model requests. Replace the current blocking Stop-hook
approach for stale modules with a layered, zero-cost reminder strategy.

## Architecture Summary

Three independent changes, each independently deployable and testable:

1. **`cmd_prompt_check` — stale-module injection on `UserPromptSubmit`**  
   Every time the dev agent receives a new message, check whether any code files
   edited this session have a module knowledge file that is older than the code.
   If so, append a `systemMessage` to the existing keyword-match output. Zero cost.

2. **`cmd_check_update` Case 2 — non-blocking warning**  
   The Stop hook currently returns exit code 2 for stale modules, which causes a
   blocking re-run (premium request). Change it to exit 0 + stdout `systemMessage`.
   The Stop hook remains a last-resort visible warning, not a forced re-run.

3. **`dev.agent.md` — `SubagentStart` hook for knowledge-keeper**  
   When dev invokes `knowledge-keeper` as a subagent, automatically inject a
   list of modules with stale files into the subagent's context via the new
   `SubagentStart` hook event (requires `chat.useCustomAgentHooks: true`).
   Improves quality of knowledge-keeper calls that *do* happen.

## Key Technologies

- Python 3.8+, stdlib only
- VS Code hook protocol: `UserPromptSubmit`, `Stop`, `SubagentStart`
- Existing helpers: `parse_transcript_edits`, `_classify_files`, `_claimed_modules_updated`, `_load_module_paths`

---

## File Map

### Files to modify

| File | Change |
|------|--------|
| `src/engaku/cmd_prompt_check.py` | Add stale-module check at end of `run()` |
| `src/engaku/cmd_check_update.py` | Case 2: replace `return 2` + stderr with `return 0` + stdout `systemMessage` |
| `src/engaku/templates/agents/dev.agent.md` | Add `SubagentStart` hook in frontmatter |
| `.github/agents/dev.agent.md` | Same SubagentStart hook (live copy) |

### Files to create

| File | Purpose |
|------|---------|
| `src/engaku/templates/hooks/subagent-start.json` | Template hook file for `SubagentStart` event |
| `.github/hooks/subagent-start.json` | Live copy of above |

### Tests to modify

| File | Change |
|------|--------|
| `tests/test_prompt_check.py` | Add cases: no-edit session (silent), stale module (reminder injected), already-updated (silent) |
| `tests/test_check_update.py` | Update Case 2 assertions: no longer expects exit 2, expects exit 0 + systemMessage stdout |

---

## Task 1 — `cmd_prompt_check`: stale-module reminder

**Files:** `src/engaku/cmd_prompt_check.py`, `tests/test_prompt_check.py`

### Steps

- [ ] 1.1 Add imports to `cmd_prompt_check.py`:
  ```python
  import os
  from engaku.utils import parse_transcript_edits
  from engaku.cmd_check_update import _classify_files, _claimed_modules_updated
  ```

- [ ] 1.2 Add `_build_stale_reminder(cwd, hook_input)` helper in `cmd_prompt_check.py`:
  - Read `transcript_path` from `hook_input`
  - Call `parse_transcript_edits(tp, cwd, last_turn_only=False)` — all edits this session
  - Filter to code files via `is_code_file` (import from `engaku.utils`)
  - Call `_classify_files(cwd, code_files)` → `(claimed_by_stem, unclaimed)`
  - If `claimed_by_stem` and NOT `_claimed_modules_updated(cwd, claimed_by_stem, code_files)`:
    - Collect stale stems (same logic as Case 2 in `cmd_check_update`)
    - Return reminder string: `"Knowledge update pending: modules [{stems}] have stale files. Call knowledge-keeper before ending the session."`
  - Otherwise return `None`

- [ ] 1.3 Update `run()` in `cmd_prompt_check.py`:
  - After the existing keyword-match block, call `_build_stale_reminder(cwd, hook_input)`
  - If reminder is not None, append/merge into `systemMessage` (concatenate with `\n` if keyword match also fired)
  - `cwd = os.getcwd()` at top of `run()`

- [ ] 1.4 Write failing tests in `tests/test_prompt_check.py`:
  - `test_no_transcript_no_message` — no `transcript_path` in hook input → empty output
  - `test_no_stale_modules` — transcript has edits, all modules up to date → no stale reminder
  - `test_stale_modules_reminder_injected` — transcript has code edits with stale module → reminder in `systemMessage`
  - `test_keyword_and_stale_both_fire` — both keyword match and stale → single `systemMessage` containing both

- [ ] 1.5 Run tests: `python -m pytest tests/test_prompt_check.py -v`  
  Confirm new tests fail before implementation, pass after.

- [ ] 1.6 Run full suite: `python -m pytest` — confirm no regressions.

---

## Task 2 — `cmd_check_update` Case 2: non-blocking

**Files:** `src/engaku/cmd_check_update.py`, `tests/test_check_update.py`

### Steps

- [ ] 2.1 In `cmd_check_update.py`, find the Case 2 block (around line 218–248).  
  Replace the current:
  ```python
  sys.stderr.write("Code changes detected but no knowledge files were updated.\n" ...)
  ...
  return 2
  ```
  With:
  ```python
  output = {
      "systemMessage": (
          "Knowledge update pending: modules [{}] have stale files.\n"
          "Call @knowledge-keeper to update them."
      ).format(", ".join(stale_stems))
  }
  sys.stdout.write(json.dumps(output) + "\n")
  return 0
  ```
  Remove all `sys.stderr.write` calls in this block.

- [ ] 2.2 Write/update tests in `tests/test_check_update.py`:
  - Find existing test for Case 2 stale behaviour — update assertion from `exit_code == 2` to `exit_code == 0`
  - Assert stdout contains `systemMessage` with stale stem names
  - Assert stderr is empty

- [ ] 2.3 Run: `python -m pytest tests/test_check_update.py -v`

- [ ] 2.4 Run full suite: `python -m pytest`

---

## Task 3 — `SubagentStart` hook for knowledge-keeper context injection

**Files:** `src/engaku/templates/agents/dev.agent.md`, `.github/agents/dev.agent.md`,  
`src/engaku/templates/hooks/subagent-start.json`, `.github/hooks/subagent-start.json`

### Background

The `SubagentStart` hook event fires when dev spawns a subagent. The hook receives
`agent_type` in stdin. We only want to act when `agent_type == "knowledge-keeper"`.
The hook can return `hookSpecificOutput.additionalContext` to inject text into the
subagent's context.

Requires VS Code setting `chat.useCustomAgentHooks: true`.

### Steps

- [ ] 3.1 Create `src/engaku/cmd_subagent_start.py`:
  ```
  Reads stdin. If agent_type == "knowledge-keeper":
    - Run the stale-module check (reuse logic from Task 1's helper)
    - If stale stems found, output:
      {
        "hookSpecificOutput": {
          "hookEventName": "SubagentStart",
          "additionalContext": "Stale modules needing update: [X, Y]\nFiles changed: [...]"
        }
      }
  Otherwise exits 0 silently.
  ```

- [ ] 3.2 Add `main(argv=None)` entry point to `cmd_subagent_start.py`.

- [ ] 3.3 Register in `pyproject.toml` under `[project.scripts]`:
  ```toml
  engaku-subagent-start = "engaku.cmd_subagent_start:main"
  ```
  Or reuse the existing `engaku` CLI dispatch pattern — check how other commands
  are registered and follow the same pattern.

- [ ] 3.4 Create `src/engaku/templates/hooks/subagent-start.json`:
  ```json
  {
    "hooks": {
      "SubagentStart": [
        {
          "type": "command",
          "command": "engaku subagent-start",
          "timeout": 5
        }
      ]
    }
  }
  ```

- [ ] 3.5 Copy to `.github/hooks/subagent-start.json` (live copy).

- [ ] 3.6 Add `SubagentStart` hook to frontmatter of both  
  `src/engaku/templates/agents/dev.agent.md` and `.github/agents/dev.agent.md`:
  ```yaml
  hooks:
    Stop:
      - type: command
        command: engaku check-update
        timeout: 10
    UserPromptSubmit:
      - type: command
        command: engaku prompt-check
        timeout: 5
    SubagentStart:
      - type: command
        command: engaku subagent-start
        timeout: 5
  ```

- [ ] 3.7 Add hook copy in `cmd_init.py` to include `subagent-start.json`  
  (same loop that copies `prompt-check.json` — just add to the list).

- [ ] 3.8 Write tests in `tests/test_subagent_start.py`:
  - `test_non_knowledge_keeper_agent_silent` — `agent_type=Plan` → empty stdout, exit 0
  - `test_knowledge_keeper_no_stale` — `agent_type=knowledge-keeper`, no stale files → empty stdout
  - `test_knowledge_keeper_stale_injects_context` — stale modules → `additionalContext` in stdout

- [ ] 3.9 Run: `python -m pytest tests/test_subagent_start.py -v`

- [ ] 3.10 Run full suite: `python -m pytest`

---

## Verification

After all three tasks are done:

```bash
python -m pytest          # all tests pass
engaku validate           # all .ai/modules/*.md pass frontmatter validation
```

Manually verify in a live session:
1. Edit a code file without calling knowledge-keeper.
2. Send a follow-up message → confirm stale reminder appears in system message.
3. Session end (Stop) → confirm non-blocking warning only (no extra agent turn).
4. Call `@knowledge-keeper` → confirm SubagentStart injects stale modules into subagent context.

## Scope Boundaries

**In scope:**
- The three changes above, plus their tests.

**Out of scope:**
- Changes to `scanner-update` or any other agent.
- Modifying `cmd_inject.py` — PreCompact stale injection is a future improvement if the above proves insufficient.
- UI changes or new CLI commands beyond `engaku subagent-start`.
