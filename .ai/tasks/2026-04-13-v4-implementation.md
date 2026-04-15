---
plan_id: 2026-04-13-v4-implementation
title: Engaku V4 — Native Simplification Implementation
status: done
created: 2026-04-13
---

## Background

V4 removes the module knowledge system (`.ai/modules/`, knowledge-keeper, scanner-update,
validate, stats, subagent-start) and replaces it with VS Code native `.instructions.md`
files. Rules are merged into `copilot-instructions.md`. Four curated skills are bundled
with `engaku init`. Estimated net code deletion: ~750–800 lines.

Full design: `docs/v4-native-simplification.md`

## Design

See `docs/v4-native-simplification.md` for design decisions D1–D9.

Key deltas from current code:
- `cmd_inject.py`: remove `_build_module_index`, add active-task injection with `<project-context>` / `<active-task>` fence tags
- `cmd_check_update.py`: remove all `_load_module_paths`, `_classify_files`, `_claimed_modules_updated` — command becomes a lightweight exit
- `cmd_prompt_check.py`: remove `_build_stale_reminder`, `_build_unclaimed_reminder` and imports from check_update
- `cmd_init.py`: remove `.ai/modules/` and `.ai/rules.md` generation; add `.github/instructions/` and `.github/skills/` generation

## File Map

**Delete:**
- `src/engaku/cmd_validate.py`
- `src/engaku/cmd_stats.py`
- `src/engaku/cmd_subagent_start.py`
- `tests/test_validate.py`
- `tests/test_stats.py`
- `tests/test_subagent_start.py`
- `.github/agents/knowledge-keeper.agent.md`
- `.github/agents/scanner-update.agent.md`
- `src/engaku/templates/agents/knowledge-keeper.agent.md`
- `src/engaku/templates/agents/scanner-update.agent.md`
- `src/engaku/templates/modules/` (directory)
- `src/engaku/templates/ai/rules.md`
- `.ai/modules/` (directory + all contents)
- `.ai/rules.md`

**Modify:**
- `src/engaku/cli.py` — remove validate / stats / subagent-start entries
- `src/engaku/cmd_inject.py` — remove module index, add active-task injection
- `src/engaku/cmd_check_update.py` — remove all module stale/unclaimed logic
- `src/engaku/cmd_prompt_check.py` — remove stale/unclaimed reminders + imports
- `src/engaku/cmd_init.py` — new structure: instructions/ + skills/; no modules/ or rules.md
- `src/engaku/templates/copilot-instructions.md` — merge rules.md content
- `src/engaku/templates/agents/dev.agent.md` — remove knowledge-keeper + scanner-update callouts
- `src/engaku/templates/agents/planner.agent.md` — already updated (web tool, modules ref)
- `src/engaku/templates/agents/scanner.agent.md` — rewrite: generate .instructions.md, not .ai/modules/
- `.github/agents/dev.agent.md` — same as template changes
- `.github/agents/scanner.agent.md` — same as template changes
- `.github/copilot-instructions.md` — merge .ai/rules.md content, then rules.md deleted
- `tests/test_inject.py` — update for new output format
- `tests/test_check_update.py` — remove module-specific assertions
- `tests/test_prompt_check.py` — remove stale/unclaimed assertions

**Create:**
- `src/engaku/templates/instructions/hooks.instructions.md` (stub, applyTo cmd_*.py)
- `src/engaku/templates/instructions/tests.instructions.md` (stub, applyTo tests/**)
- `src/engaku/templates/instructions/templates.instructions.md` (stub, applyTo templates/**)
- `src/engaku/templates/skills/systematic-debugging/SKILL.md`
- `src/engaku/templates/skills/verification-before-completion/SKILL.md`
- `src/engaku/templates/skills/frontend-design/SKILL.md`
- `.github/instructions/hooks.instructions.md` (live project)
- `.github/instructions/templates.instructions.md` (live project)
- `.github/instructions/tests.instructions.md` (live project)
- `.github/skills/systematic-debugging/SKILL.md` (live project)
- `.github/skills/verification-before-completion/SKILL.md` (live project)
- `.github/skills/frontend-design/SKILL.md` (live project)

## Tasks

- [x] 1. **Delete validate, stats, subagent-start commands**
  - Files: `src/engaku/cmd_validate.py`, `src/engaku/cmd_stats.py`, `src/engaku/cmd_subagent_start.py`, `tests/test_validate.py`, `tests/test_stats.py`, `tests/test_subagent_start.py`
  - Steps:
    - Delete the six files above
    - In `src/engaku/cli.py`: remove the three `add_parser` blocks (validate, stats, subagent-start) and their dispatch branches in `main()`
  - Verify: `python -m unittest discover -s tests` passes; `engaku validate` returns "command not found"-style error

- [x] 2. **Delete knowledge-keeper and scanner-update agents**
  - Files: `.github/agents/knowledge-keeper.agent.md`, `.github/agents/scanner-update.agent.md`, `src/engaku/templates/agents/knowledge-keeper.agent.md`, `src/engaku/templates/agents/scanner-update.agent.md`
  - Steps:
    - Delete all four files
  - Verify: `ls .github/agents/` shows exactly: `dev.agent.md`, `planner.agent.md`, `reviewer.agent.md`, `scanner.agent.md`

- [x] 3. **Delete module template directory and live modules**
  - Files: `src/engaku/templates/modules/` (dir), `src/engaku/templates/ai/rules.md`, `.ai/modules/` (dir)
  - Steps:
    - `rm -rf src/engaku/templates/modules/`
    - Delete `src/engaku/templates/ai/rules.md`
    - `rm -rf .ai/modules/`
  - Verify: none of the above paths exist

- [x] 4. **Refactor cmd_inject.py — remove module index, add active-task injection**
  - Files: `src/engaku/cmd_inject.py`, `tests/test_inject.py`
  - Steps:
    - Delete `_parse_paths_frontmatter()` and `_build_module_index()` functions entirely
    - Add `_find_active_task(cwd)` function: scans `.ai/tasks/*.md`, finds frontmatter `status: in-progress`, returns `(title, unchecked_items_list)` for the first match, or `None`
    - In `run()`:
      - Wrap overview content: `<project-context>\n{content}\n</project-context>`
      - After overview, call `_find_active_task(cwd)`. If found, append `<active-task>\n## {title}\n{unchecked checklist lines}\n</active-task>` as a separate part
      - Remove `_build_module_index` call and the `module_index` variable
    - Update `tests/test_inject.py`: replace any assertions about module index table with assertions about `<project-context>` fence and `<active-task>` block
  - Verify: `python -m unittest tests.test_inject` passes; `echo '{}' | engaku inject` emits JSON with `<project-context>` fence

- [x] 5. **Refactor cmd_check_update.py — remove stale/unclaimed module logic**
  - Files: `src/engaku/cmd_check_update.py`, `tests/test_check_update.py`
  - Steps:
    - Delete functions: `_suggest_modules()`, `_load_module_paths()`, `_classify_files()`, `_claimed_modules_updated()`
    - Remove unused imports: `fnmatch`, `parse_frontmatter`, `parse_paths_from_frontmatter`, `load_config`, `RECENT_SECONDS` (only if unused after refactor)
    - Simplify `run()`: keep `_get_changed_files()` call for transcript reading; remove all stale/unclaimed branch logic; the command should exit 0 silently (no blocking)
    - Update `tests/test_check_update.py`: remove all test cases that reference module stale/unclaimed logic
  - Verify: `python -m unittest tests.test_check_update` passes; `echo '{}' | engaku check-update` exits 0

- [x] 6. **Refactor cmd_prompt_check.py — remove stale/unclaimed reminders**
  - Files: `src/engaku/cmd_prompt_check.py`, `tests/test_prompt_check.py`
  - Steps:
    - Remove `from engaku.cmd_check_update import _classify_files, _claimed_modules_updated` import
    - Delete `_build_stale_reminder()` and `_build_unclaimed_reminder()` functions
    - In `run()`: remove calls to both deleted functions; keep only keyword detection → systemMessage output
    - Update `tests/test_prompt_check.py`: remove stale/unclaimed test cases
  - Verify: `python -m unittest tests.test_prompt_check` passes

- [x] 7. **Rewrite scanner.agent.md — new mandate (template + live)**
  - Files: `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/scanner.agent.md`
  - Steps:
    - Replace body of both files with the new mandate: scan project, recommend `.instructions.md` groupings, generate `.github/instructions/<name>.instructions.md` with `applyTo` glob, wait for user approval before writing
    - Remove all references to `.ai/modules/`, knowledge files, and `paths:` frontmatter
    - New workflow steps: (1) list source + test files, (2) propose groupings as table (name, glob pattern, rationale), (3) wait for approval, (4) write `.instructions.md` files, (5) update `.ai/overview.md` if needed
    - Keep same frontmatter tools list; add `web` if not present (for looking up glob patterns etc.)
  - Verify: template and live bodies are identical (ignoring `model:` line)

- [x] 8. **Update dev.agent.md — remove knowledge-keeper and scanner-update callouts (template + live)**
  - Files: `src/engaku/templates/agents/dev.agent.md`, `.github/agents/dev.agent.md`
  - Steps:
    - Remove step "Assign unclaimed files" (scanner-update call)
    - Remove step "Update module knowledge" (knowledge-keeper call)
    - Remove any reference to `@scanner-update`, `@knowledge-keeper`, `.ai/modules/`
    - Simplify "Before responding that work is done" section to: (1) update project-level files (`.ai/overview.md`, decisions, tasks) if architecture/constraints changed
    - Keep hooks frontmatter unchanged
  - Verify: template and live bodies identical (ignoring `model:`); no occurrence of "knowledge-keeper" or "scanner-update" in either file

- [x] 9. **Update template copilot-instructions.md — merge rules content**
  - Files: `src/engaku/templates/copilot-instructions.md`
  - Steps:
    - Read `src/engaku/templates/ai/rules.md` (already deleted in task 3 — use the content captured before deletion or from `.ai/rules.md`)
    - Merge the "Project Constraints", "Forbidden", and "Agent Configuration" sections from rules.md into the template copilot-instructions.md
    - Remove any rule that references `.ai/modules/`, `knowledge-keeper`, `scanner-update`, `MAX_CHARS`, or `@scanner-update`
    - Keep the file under 40 lines total (global rules only — path-specific rules go into .instructions.md)
  - Verify: `wc -l src/engaku/templates/copilot-instructions.md` ≤ 40; no reference to "module" or "knowledge-keeper"

- [x] 10. **Add skill templates (4 skills)**
  - Files: `src/engaku/templates/skills/systematic-debugging/SKILL.md`, `src/engaku/templates/skills/verification-before-completion/SKILL.md`, `src/engaku/templates/skills/frontend-design/SKILL.md`, `src/engaku/templates/skills/writing-plans/SKILL.md`
  - Steps:
    - Copy content from `~/.copilot/skills/systematic-debugging/SKILL.md` → `src/engaku/templates/skills/systematic-debugging/SKILL.md`
    - Copy content from `~/.copilot/skills/verification-before-completion/SKILL.md` → `src/engaku/templates/skills/verification-before-completion/SKILL.md`
    - Copy content from `~/.copilot/skills/frontend-design/SKILL.md` → `src/engaku/templates/skills/frontend-design/SKILL.md`
  - Verify: all three files exist and have valid YAML frontmatter with `name:` and `description:` fields; `grep -r "^name:" src/engaku/templates/skills/` shows 3 results

- [x] 11. **Add instructions stubs to templates**
  - Files: `src/engaku/templates/instructions/hooks.instructions.md`, `src/engaku/templates/instructions/tests.instructions.md`, `src/engaku/templates/instructions/templates.instructions.md`
  - Steps:
    - Create three stub `.instructions.md` files with appropriate `applyTo` frontmatter and placeholder body text (project fills in their own content)
    - `hooks.instructions.md`: `applyTo: "src/**/cmd_*.py"` — describes hook command conventions
    - `tests.instructions.md`: `applyTo: "tests/**"` — describes test conventions
    - `templates.instructions.md`: `applyTo: "src/**/templates/**"` — describes template conventions
    - Each stub body: 3–5 sentences explaining purpose, with `<!-- Add project-specific conventions here. -->` comment
  - Verify: `ls src/engaku/templates/instructions/` shows 3 files, each has valid YAML frontmatter `applyTo:` key

- [x] 12. **Update cmd_init.py — generate new structure**
  - Files: `src/engaku/cmd_init.py`
  - Steps:
    - Remove generation of: `.ai/rules.md`, `.ai/modules/.gitkeep`
    - Remove copying of `knowledge-keeper.agent.md`, `scanner-update.agent.md`
    - Add generation of: `.github/instructions/` (copy 3 stubs from templates), `.github/skills/` (copy 4 skill directories from templates)
    - Update the module docstring to reflect new structure
  - Verify: run `engaku init` in a temp directory; confirm `.github/skills/` and `.github/instructions/` exist; confirm `.ai/modules/` and `.ai/rules.md` do NOT exist; `python -m unittest tests.test_init` passes

- [x] 13. **Migrate live engaku project — create instructions + skills, merge rules, delete modules**
  - Files: `.github/copilot-instructions.md`, `.ai/rules.md`, `.github/instructions/` (new), `.github/skills/` (new)
  - Steps:
    - Merge relevant content from `.ai/rules.md` into `.github/copilot-instructions.md` (Project Constraints + Forbidden sections; strip module/KK/SU references)
    - Delete `.ai/rules.md`
    - Create `.github/instructions/hooks.instructions.md` (applyTo: `src/engaku/cmd_*.py`; describe hook command conventions specific to engaku)
    - Create `.github/instructions/tests.instructions.md` (applyTo: `tests/**`; describe engaku test conventions: stdlib unittest, stdin mock pattern)
    - Create `.github/instructions/templates.instructions.md` (applyTo: `src/engaku/templates/**`; describe template dual-update rule)
    - Copy skill files from `~/.copilot/skills/` to `.github/skills/` for all 3 skills (systematic-debugging, verification-before-completion, frontend-design)
  - Verify: `cat .github/copilot-instructions.md` contains no reference to "rules.md" or ".ai/modules"; `.github/skills/` has 3 directories; `.github/instructions/` has 3 files

- [x] 14. **Full test suite + smoke test**
  - Steps:
    - `python -m unittest discover -s tests`
    - `engaku inject` (with empty stdin) — check JSON output has `<project-context>` fence
    - `engaku check-update` (with empty stdin) — check exits 0
    - `engaku prompt-check` (with empty stdin) — check exits 0
    - `engaku init --help` — check validate/stats/subagent-start not listed
  - Verify: all tests pass (0 errors, 0 failures); all smoke commands behave as expected

## Out of Scope

- PostToolUse guard for forbidden path writes (D7 in design doc — optional, deferred)
- Cross-session SQLite memory
- `engaku apply` changes (model config unaffected)
- `engaku log-read` changes (PostToolUse logging unaffected)
- `engaku task-review` changes (Stop hook for all-complete tasks unaffected)
- Content of the `.instructions.md` stubs beyond placeholder text — scanner agent handles real content per-project
