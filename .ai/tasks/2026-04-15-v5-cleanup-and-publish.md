---
plan_id: 2026-04-15-v5-cleanup-and-publish
title: V5 — Dead Command Cleanup, Prompt-Check Enhancement, PyPI Publish, README Rewrite
status: done
created: 2026-04-15
---

## Background

Post-V4, two commands are dead weight: `check-update` (empty shell — reads
stdin, returns 0) and `log-read` (writes to `.ai/access.log` which nothing
consumes). Removing them shrinks the codebase, eliminates two process spawns
per agent turn, and lets us clean out the remaining V3-era constants.
Meanwhile `prompt-check` is under-utilised — it only does keyword matching
but UserPromptSubmit is the ideal place to refresh active-task context
every turn. Finally, the project needs PyPI readiness, a real `overview.md`
template, and a README that matches the current feature set.

## Design

1. **Delete `check-update` + `log-read`** — remove commands, tests, CLI
   entries, agent hook references, and orphaned code (`is_code_file`,
   `IGNORED_*` constants, `ACCESS_LOG`, `parse_transcript_edits`).
2. **Enhance `prompt-check`** — in addition to keyword→systemMessage,
   also inject the current active-task unchecked steps so the agent
   always knows what to do next. Rename command to keep the CLI surface
   stable (still `engaku prompt-check`).
3. **PyPI publish prep** — bump to 0.2.0, add classifiers / URLs /
   `--version` flag, create `CHANGELOG.md`.
4. **`overview.md` template** — replace empty-comment scaffold with a
   fillable guide that `engaku inject` actually benefits from.
5. **README rewrite** — accurate subcommand table, correct "How it works",
   installation via PyPI, structured Quick Start.

## File Map

**Delete:**
- `src/engaku/cmd_check_update.py`
- `src/engaku/cmd_log_read.py`
- `tests/test_check_update.py`
- `tests/test_log_read.py`

**Modify:**
- `src/engaku/cli.py` — remove check-update + log-read entries; add `--version`
- `src/engaku/constants.py` — remove `IGNORED_*`, `ACCESS_LOG`
- `src/engaku/utils.py` — remove `is_code_file`, `IGNORED_*` imports, `parse_transcript_edits` + `_EDIT_TOOL_NAMES` + `_extract_paths_from_args`
- `src/engaku/cmd_prompt_check.py` — add active-task injection, improve keyword precision
- `tests/test_prompt_check.py` — add tests for active-task injection
- `src/engaku/templates/agents/dev.agent.md` — remove check-update + log-read hooks
- `.github/agents/dev.agent.md` — same
- `README.md` — full rewrite
- `pyproject.toml` — bump version, add classifiers/URLs
- `src/engaku/__init__.py` — add `__version__`
- `src/engaku/templates/ai/overview.md` — useful scaffold

**Create:**
- `CHANGELOG.md`

## Tasks

- [x] 1. **Delete `check-update` command**
  - Files: `src/engaku/cmd_check_update.py`, `tests/test_check_update.py`, `src/engaku/cli.py`
  - Steps:
    - Delete `src/engaku/cmd_check_update.py`
    - Delete `tests/test_check_update.py`
    - In `src/engaku/cli.py`: remove the `# engaku check-update` add_parser block (4 lines) and the `elif args.command == "check-update":` dispatch block (3 lines)
  - Verify: `python -m unittest discover -s tests 2>&1 | tail -3` — all tests pass, count decreases by 4

- [x] 2. **Delete `log-read` command**
  - Files: `src/engaku/cmd_log_read.py`, `tests/test_log_read.py`, `src/engaku/cli.py`
  - Steps:
    - Delete `src/engaku/cmd_log_read.py`
    - Delete `tests/test_log_read.py`
    - In `src/engaku/cli.py`: remove the `# engaku log-read` add_parser block (4 lines) and the `elif args.command == "log-read":` dispatch block (3 lines)
  - Verify: `python -m unittest discover -s tests 2>&1 | tail -3` — all pass

- [x] 3. **Remove check-update + log-read from dev agent hooks (template + live)**
  - Files: `src/engaku/templates/agents/dev.agent.md`, `.github/agents/dev.agent.md`
  - Steps:
    - In both files, remove the Stop hook entry for `engaku check-update` (2 lines: `- type: command` + `command: engaku check-update` + `timeout: 10`)
    - In both files, remove the entire `PostToolUse:` block (3 lines: key + `- type: command` + `command: engaku log-read` + `timeout: 5`)
  - Verify: `grep -r "check-update\|log-read" src/engaku/templates/agents/ .github/agents/` — no output

- [x] 4. **Clean up orphaned code in constants.py, utils.py, and test_utils.py**
  - Files: `src/engaku/constants.py`, `src/engaku/utils.py`, `tests/test_utils.py`
  - Steps:
    - In `constants.py`: delete all `IGNORED_*` frozensets/tuples (`IGNORED_DIR_NAMES`, `IGNORED_DIR_SUFFIXES`, `IGNORED_EXTENSIONS`, `IGNORED_FILENAMES`), `ACCESS_LOG` line, and the section comment `# ── check-update built-in file-type blacklists`. Keep `import os` and `CONFIG_FILE`.
    - In `utils.py`: remove imports of `IGNORED_DIR_NAMES`, `IGNORED_DIR_SUFFIXES`, `IGNORED_EXTENSIONS`, `IGNORED_FILENAMES` from `engaku.constants`. Delete the entire `is_code_file()` function (~15 lines). Delete the entire `# ── transcript-based edit detection` section (~120 lines: `_EDIT_TOOL_NAMES`, `_extract_paths_from_args()`, `parse_transcript_edits()`).
    - In `tests/test_utils.py`: delete the `import` of `parse_transcript_edits`, the `_write_transcript` helper, and the entire `TestParseTranscriptEdits` class (~200 lines). If the file becomes empty (no other test classes), delete the file entirely.
  - Verify: `python -c "from engaku import utils; from engaku import constants"` — no import errors; `python -m unittest discover -s tests 2>&1 | tail -3` — all pass

- [x] 5. **Enhance `prompt-check` with active-task context**
  - Files: `src/engaku/cmd_prompt_check.py`, `tests/test_prompt_check.py`
  - Steps:
    - Add `import os` and import `parse_frontmatter` from `engaku.utils`
    - Add a `_find_active_task(cwd)` function (reuse the same logic from `cmd_inject.py:_find_active_task` — extract title + unchecked lines from in-progress tasks)
    - In `run()`: after the existing keyword matching, call `_find_active_task(os.getcwd())`. If there's an active task, build a `systemMessage` containing the active-task reminder (task title + next unchecked steps, max 5 lines). Combine with existing keyword match message if both fire.
    - Improve keyword precision: replace bare "always"/"never" with phrase patterns that require a following verb or context word (e.g. "always use", "never import", "always run") to reduce false positives on normal conversation.
    - In `tests/test_prompt_check.py`: add tests for active-task injection — create a temp `.ai/tasks/` dir with an in-progress task file, verify the systemMessage includes task info. Add a test for "always" alone not triggering (precision improvement). Update existing tests if keyword behavior changed.
  - Verify: `python -m unittest tests/test_prompt_check.py -v` — all pass including new tests

- [x] 6. **PyPI publish preparation**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `src/engaku/cli.py`, `CHANGELOG.md`
  - Steps:
    - In `pyproject.toml`: bump version to `0.2.0`. Add `classifiers` list (Development Status :: 3 - Alpha, Environment :: Console, Intended Audience :: Developers, License :: OSI Approved :: MIT License, Programming Language :: Python :: 3, Topic :: Software Development :: Quality Assurance). Add `[project.urls]` with Homepage and Repository pointing to GitHub. Add `readme = "README.md"`.
    - In `src/engaku/__init__.py`: add `__version__ = "0.2.0"`.
    - In `src/engaku/cli.py`: add `--version` argument to the main parser: `parser.add_argument("--version", action="version", version="%(prog)s " + __version__)` with import of `__version__` from `engaku`.
    - Create `CHANGELOG.md` with entries for 0.2.0 (this release: delete check-update/log-read, enhance prompt-check, PyPI publish) and 0.1.0 (initial release, V4 native simplification).
  - Verify: `engaku --version` prints `engaku 0.2.0`; `python -m build --sdist 2>&1 | tail -3` succeeds (if build is available)

- [x] 7. **Improve `overview.md` template**
  - Files: `src/engaku/templates/ai/overview.md`
  - Steps:
    - Replace the current HTML-comment scaffold with a fillable template that has real section headings and placeholder text (not HTML comments). Include: `# Project Overview` with `## Overview` (one-paragraph placeholder), `## Directory Structure` (example format), `## Constraints` (bullet list placeholder), `## Tech Stack` (placeholder).
    - Each section should have a brief one-line instruction as plain text (e.g. "Describe your project here: name, language, core purpose.") that the user replaces.
  - Verify: `cat src/engaku/templates/ai/overview.md` — shows the new template with visible placeholder text

- [x] 8. **Rewrite README.md**
  - Files: `README.md`
  - Steps:
    - Update the tagline: remove "keeps module knowledge files in sync" — replace with accurate description
    - Update "What it does" section: remove references to "update module knowledge after edits"
    - Update Installation: `pip install engaku` (primary), `pip install git+https://...` (from source)
    - Update Quick Start: only show `engaku init` and explain what happens next (agents + hooks are activated, scanner is available)
    - Update Subcommands table: remove `check-update` and `log-read`. Update descriptions for remaining 5 commands (init, inject, prompt-check, task-review, apply)
    - Update "How it works" section: describe the 4 hook events (SessionStart → inject, UserPromptSubmit → prompt-check, Stop → task-review, PreCompact → inject). Remove references to access log and module knowledge.
    - Add a "What `engaku init` creates" section listing the directory structure
    - Keep Requirements section accurate
  - Verify: `grep -n "check-update\|log-read\|module knowledge\|rules.md\|access.log" README.md` — no output

- [x] 9. **Update `.ai/overview.md` (this project's own overview)**
  - Files: `.ai/overview.md`
  - Steps:
    - Update to reflect current state: five subcommands (init, inject, prompt-check, task-review, apply), no check-update or log-read. Mention PyPI distribution.
  - Verify: visual inspection

- [x] 10. **Final full test suite run**
  - Steps:
    - Run `python -m unittest discover -s tests` — all tests pass
    - Run `engaku --version` — prints version
    - Run `grep -rn "check.update\|log.read\|access.log\|IGNORED_DIR\|is_code_file\|_EDIT_TOOL_NAMES\|parse_transcript" src/ tests/` — no matches (confirming complete cleanup)
  - Verify: all above pass

## Out of Scope

- Agent Plugin conversion (future V5+ direction)
- Scanner → skill conversion (separate plan)
- `engaku update` command (separate plan)
- `--dry-run` for init (separate plan)
- PreToolUse guard hook (future)
- Actual PyPI `twine upload` — this plan prepares the package; the upload is a manual step
