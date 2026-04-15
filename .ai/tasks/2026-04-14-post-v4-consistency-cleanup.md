---
plan_id: 2026-04-14-post-v4-consistency-cleanup
title: Post-V4 Consistency Cleanup
status: done
created: 2026-04-14
---

## Background

V4 deleted the module-knowledge system (`cmd_validate`, `cmd_stats`, `cmd_subagent_start`,
`knowledge-keeper agent`, `rules.md`, `.ai/modules/`) but left behind ghost references,
stale documentation, dead constants, and hollow command logic. A new user who runs
`engaku init` today encounters hook errors (`subagent-start: command not found`),
a README listing non-existent subcommands, and misleading config files.

Source audit: `.ai/docs/2026-04-13-project-audit.md`

## Design

No new features. Pure deletion and synchronisation across five areas:
1. Remove the `SubagentStart` hook that calls the deleted `engaku subagent-start`
2. Sync README to actual CLI
3. Strip the hollow transcript-parsing logic from `check-update`
4. Delete dead constants and the `max_chars`/`rules.md` path in `apply`
5. Replace the empty `overview.md` template with a useful guide scaffold

## File Map

- Modify: `src/engaku/templates/agents/dev.agent.md`
- Modify: `.github/agents/dev.agent.md`
- Modify: `README.md`
- Modify: `src/engaku/cli.py`
- Modify: `src/engaku/cmd_check_update.py`
- Modify: `tests/test_check_update.py`
- Modify: `src/engaku/constants.py`
- Modify: `src/engaku/utils.py`
- Modify: `src/engaku/cmd_apply.py`
- Modify: `tests/test_apply.py`
- Modify: `src/engaku/templates/ai/engaku.json`
- Modify: `.ai/engaku.json`
- Modify: `src/engaku/templates/ai/overview.md`

## Tasks

- [x] 1. **Remove SubagentStart ghost hook from dev agent templates**
  - Files: `src/engaku/templates/agents/dev.agent.md`, `.github/agents/dev.agent.md`
  - Steps:
    - In both files, delete the entire `SubagentStart:` block (3 lines: the key + `- type: command` + `command: engaku subagent-start` + `timeout: 5`). The `SessionStart:` block immediately follows and must remain.
    - Confirm no `subagent-start` remains in either file.
  - Verify: `grep -r "subagent-start" src/engaku/templates/ .github/agents/`
  - Expected: no output

- [x] 2. **Sync README.md to actual CLI**
  - Files: `README.md`
  - Steps:
    - In the subcommand table, remove the three rows for `subagent-start`, `validate`, and `stats`.
    - Change the `inject` row description from "Inject `.ai/` context (overview, rules, module index) into stdout" to "Inject `.ai/overview.md` + active-task context into SessionStart / PreCompact hooks".
    - In the "How it works" section, remove the bullet for `SubagentStart → engaku subagent-start` entirely.
    - Remove the sentence "Module knowledge lives in `.ai/modules/*.md`..." paragraph entirely.
  - Verify: `grep -n "subagent-start\|validate\|stats\|rules, module" README.md`
  - Expected: no output

- [x] 3. **Fix inject CLI help text and strip check-update hollow logic**
  - Files: `src/engaku/cli.py`, `src/engaku/cmd_check_update.py`, `tests/test_check_update.py`
  - Steps:
    - In `src/engaku/cli.py`, change the `inject` help string from `"Output rules.md + overview.md as SessionStart hook JSON"` to `"Inject .ai/overview.md + active-task context (SessionStart/PreCompact hook)"`.
    - In `src/engaku/cmd_check_update.py`:
      - Remove the `from engaku.utils import parse_transcript_edits, read_hook_input` import; replace with `from engaku.utils import read_hook_input`.
      - Delete the entire `_get_changed_files()` function.
      - In `run()`, remove the two lines `cwd = os.getcwd()` and `_get_changed_files(cwd, hook_input=hook_input)`. The body becomes: read hook_input, guard on `stop_hook_active`, return 0.
    - In `tests/test_check_update.py`:
      - Remove the `changed_files` parameter from `_run()` and the monkey-patching block for `orig_get = mod._get_changed_files`.
      - Remove the `changed_files=` argument from all four test call sites.
      - Replace the assertions in `test_code_changes_exits_zero_silently` and `test_only_config_files_exits_zero` as needed (they still assert exit code 0).
  - Verify: `python -m unittest tests/test_check_update.py -v`
  - Expected: 4 tests pass, OK

- [x] 4. **Remove dead constants and max_chars/rules.md machinery**
  - Files: `src/engaku/constants.py`, `src/engaku/utils.py`, `src/engaku/cmd_apply.py`, `tests/test_apply.py`, `src/engaku/templates/ai/engaku.json`, `.ai/engaku.json`
  - Steps:
    - In `src/engaku/constants.py`, delete the entire `# ── validation defaults` section and `# ── stats defaults` section: remove `FORBIDDEN_PHRASES`, `MIN_CHARS`, `MAX_CHARS`, `REQUIRED_HEADING`, `STALE_DAYS`. Also remove `RECENT_SECONDS` (unused since check-update no longer tracks timing). Keep `CONFIG_FILE` and `ACCESS_LOG` and all `IGNORED_*` constants.
    - In `src/engaku/utils.py`:
      - Remove `MAX_CHARS` from the import list at the top.
      - Simplify `load_config()` to return only `{"agents": raw.get("agents", {})}`. Delete the `cu`, `max_chars`, and `check_update` lines.
    - In `src/engaku/cmd_apply.py`:
      - Delete the entire `_update_rules_max_chars()` function (lines from `def _update_rules_max_chars` through its closing `return True, "ok"`).
      - In `run()`, delete the `# ── max_chars → .ai/rules.md` block: the `max_chars = config.get(...)`, `rules_path = ...`, `rules_changed = 0`, `rules_skipped = 0`, and the `if max_chars is not None:` block.
      - Update the final summary line's `total_changed`/`total_skipped` to drop the `rules_*` variables.
    - In `tests/test_apply.py`:
      - Remove `_update_rules_max_chars` from the import on line 9.
      - Delete the entire `TestUpdateRulesMaxChars` class.
      - Delete the entire `TestApplyMaxCharsIntegration` class.
    - In `src/engaku/templates/ai/engaku.json`, replace the file content with just `{"agents": {}}`.
    - In `.ai/engaku.json`, replace content with `{"agents": {}}`.
  - Verify: `python -m unittest tests/test_apply.py tests/test_utils.py -v`
  - Expected: all tests pass (TestApply class still has 9 tests; max_chars classes are gone)

- [x] 5. **Improve overview.md template with a usable scaffold**
  - Files: `src/engaku/templates/ai/overview.md`
  - Steps:
    - Replace the current file (which contains only HTML comment placeholders) with a filled scaffold that has three sections with brief example text inside comments so users know exactly what to write:
      - `## Overview` — one example sentence showing format
      - `## Directory Structure` — example rows showing src/, tests/ etc.
      - `## Constraints` — example bullet list showing the kind of content that belongs here (language version, zero-dep rule, etc.)
    - The file must NOT contain any engaku-specific content — it must be generic enough for any project.
  - Verify: `python -m unittest tests/test_init.py -v`
  - Expected: all 5 tests pass (init copies the file correctly regardless of content changes)

- [x] 6. **Full regression run**
  - Files: none
  - Steps:
    - Run the complete test suite.
    - Confirm 0 failures and that total test count has decreased by ~15 (removed max_chars and check_update redundant tests).
  - Verify: `python -m unittest discover -s tests -v 2>&1 | tail -5`
  - Expected: `OK` with no failures; count ≈ 71–75 tests

## Out of Scope

- `engaku update` / template upgrade mechanism (new feature)
- `--dry-run` flag for init (new feature)
- `engaku uninstall` (new feature)
- Removing `frontend-design` skill from bundled templates (content decision, not a bug)
- PyPI publishing
- Adding `.ai/access.log` to `.gitignore` (minor polish, separate task)
- `engaku.json` `agents` documentation / examples (separate UX task)
