# Config Unification & Code Deduplication — Implementation Plan

**Goal:** Extract duplicated constants into `constants.py`, duplicated utility
functions into `utils.py`, expand `engaku.json` as unified project config,
and add user-configurable ignore list + uncovered-action setting.

**Architecture:** New shared modules `constants.py` and `utils.py` under
`src/engaku/`. Config loading via `engaku.json` with fallback defaults.
All existing `cmd_*.py` files updated to import from shared modules.

**Constraints:** Python >=3.8, stdlib only, no third-party dependencies.

---

## File Map

### Create

- `src/engaku/constants.py` — framework built-in defaults
- `src/engaku/utils.py` — shared utility functions

### Modify

- `src/engaku/cmd_check_update.py` — remove constants + duplicated functions, import from shared modules, add config-based ignore + `uncovered_action`
- `src/engaku/cmd_validate.py` — remove constants + `_parse_frontmatter()`, import from shared modules, read `max_chars` from config
- `src/engaku/cmd_inject.py` — remove `SESSION_EDITS` + `_read_hook_input()` + `_parse_paths_frontmatter()`, import from shared modules
- `src/engaku/cmd_log_edit.py` — remove all constants + duplicated functions, import from shared modules
- `src/engaku/cmd_log_read.py` — remove `_read_hook_input()` + `_is_ai_file()` + `_relative_to_cwd()`, import from shared modules
- `src/engaku/cmd_stats.py` — remove `STALE_DAYS`, import from shared modules
- `src/engaku/cmd_apply.py` — use shared `load_config()` + `_parse_frontmatter()` from utils
- `src/engaku/templates/ai/engaku.json` — expand schema with `max_chars` + `check_update`
- `.ai/engaku.json` — expand with `max_chars` + `check_update` for dogfooding
- `tests/test_check_update.py` — update imports, add config ignore + uncovered_action tests
- `tests/test_validate.py` — update imports
- `tests/test_inject.py` — update imports
- `tests/test_log_edit.py` — update imports
- `tests/test_log_read.py` — update imports

---

## Duplication Inventory

Before implementation, here is the full list of what gets extracted where.

### → `constants.py`

| Constant | Current locations | Notes |
|----------|-------------------|-------|
| `IGNORED_DIR_NAMES` | cmd_check_update.py, cmd_log_edit.py | Exact duplicate |
| `IGNORED_DIR_SUFFIXES` | cmd_check_update.py, cmd_log_edit.py | Exact duplicate |
| `IGNORED_EXTENSIONS` | cmd_check_update.py, cmd_log_edit.py | Exact duplicate |
| `IGNORED_FILENAMES` | cmd_check_update.py, cmd_log_edit.py | Exact duplicate |
| `RECENT_SECONDS` | cmd_check_update.py, cmd_validate.py | Same value (600) |
| `SESSION_EDITS` | cmd_check_update.py, cmd_inject.py, cmd_log_edit.py | Same value |
| `MAX_CHARS` | cmd_validate.py | Single source but config-overridable |
| `MIN_CHARS` | cmd_validate.py | Single source |
| `REQUIRED_HEADING` | cmd_validate.py | Single source |
| `FORBIDDEN_PHRASES` | cmd_validate.py | Single source |
| `ACCESS_LOG` | cmd_log_read.py | Single source |
| `STALE_DAYS` | cmd_stats.py | Single source |
| `CONFIG_FILE` | (new) | `.ai/engaku.json` path |

### → `utils.py`

| Function | Current locations | Notes |
|----------|-------------------|-------|
| `read_hook_input()` | cmd_check_update.py, cmd_inject.py, cmd_log_edit.py, cmd_log_read.py | 4 exact copies |
| `parse_frontmatter(content)` | cmd_check_update.py, cmd_validate.py, (inline in cmd_apply.py) | 3 copies |
| `parse_paths_from_frontmatter(fm_str)` | cmd_check_update.py, cmd_inject.py | 2 near-duplicates |
| `is_code_file(path)` | cmd_check_update.py, cmd_log_edit.py | 2 exact copies |
| `is_ai_file(path, cwd)` | cmd_log_edit.py, cmd_log_read.py | 2 exact copies |
| `relative_to_cwd(path, cwd)` | cmd_log_edit.py, cmd_log_read.py | 2 exact copies |
| `load_config(cwd)` | (new, replaces cmd_apply.py's `_load_config`) | Expanded to return full merged config |

**Naming convention:** Public functions in `utils.py` drop the `_` prefix since
they are no longer module-private.

---

## Tasks

### Task 1: Create `constants.py`

**Files:**
- Create: `src/engaku/constants.py`

- [ ] Create `src/engaku/constants.py` with all constants from the inventory above
- [ ] Include `CONFIG_FILE = os.path.join(".ai", "engaku.json")` as new constant
- [ ] Verify: `python -c "from engaku.constants import MAX_CHARS, IGNORED_DIR_NAMES; print('OK')"`

---

### Task 2: Create `utils.py`

**Files:**
- Create: `src/engaku/utils.py`

- [ ] Create `src/engaku/utils.py` with the following functions:
      ```
      read_hook_input() -> dict
      parse_frontmatter(content) -> (frontmatter_str | None, body_str)
      parse_paths_from_frontmatter(fm_str) -> list[str]
      is_code_file(path) -> bool
      is_ai_file(path, cwd) -> bool
      relative_to_cwd(path, cwd) -> str
      load_config(cwd) -> dict
      ```
- [ ] `is_code_file()` imports blacklists from `constants.py`
- [ ] `load_config(cwd)` reads `.ai/engaku.json`, merges with defaults from `constants.py`:
      ```python
      def load_config(cwd):
          path = os.path.join(cwd, CONFIG_FILE)
          raw = {}
          if os.path.isfile(path):
              with open(path, "r", encoding="utf-8") as f:
                  try:
                      raw = json.loads(f.read())
                  except ValueError:
                      pass
          cu = raw.get("check_update", {})
          return {
              "agents": raw.get("agents", {}),
              "max_chars": raw.get("max_chars", MAX_CHARS),
              "check_update": {
                  "ignore": cu.get("ignore", []),
                  "uncovered_action": cu.get("uncovered_action", "warn"),
              },
          }
      ```
- [ ] Verify: `python -c "from engaku.utils import read_hook_input, load_config; print('OK')"`

---

### Task 3: Migrate `cmd_check_update.py`

**Files:**
- Modify: `src/engaku/cmd_check_update.py`

This is the largest migration. The file currently defines ~60 lines of constants and several
duplicated functions.

- [ ] Remove all constant definitions (IGNORED_DIR_NAMES, IGNORED_DIR_SUFFIXES,
      IGNORED_EXTENSIONS, IGNORED_FILENAMES, RECENT_SECONDS, SESSION_EDITS)
- [ ] Remove duplicated functions: `_read_hook_input()`, `_parse_frontmatter()`,
      `_parse_paths_from_frontmatter()`, `_is_code_file()`
- [ ] Add imports:
      ```python
      from engaku.constants import RECENT_SECONDS, SESSION_EDITS
      from engaku.utils import (
          read_hook_input, parse_frontmatter, parse_paths_from_frontmatter,
          is_code_file, load_config,
      )
      ```
- [ ] Update all internal call sites — `_read_hook_input()` → `read_hook_input()`, etc.
- [ ] In `_load_module_paths()`: replace `_parse_frontmatter(content)` →
      `parse_frontmatter(content)`, `_parse_paths_from_frontmatter(fm)` →
      `parse_paths_from_frontmatter(fm)`
- [ ] Add `_is_ignored_path(path, patterns)` function:
      ```python
      def _is_ignored_path(path, patterns):
          """Return True if path matches any user-configured ignore pattern."""
          for pattern in patterns:
              if _match_path(path, pattern):
                  return True
          return False
      ```
      (Reuses the existing `_match_path()` function already in this file.)
- [ ] In `run()`, after `_is_code_file` filter, add config-based ignore filter:
      ```python
      config = load_config(cwd)
      ignore_patterns = config["check_update"]["ignore"]
      code_changes = [
          f for f in changed
          if is_code_file(f) and not _is_ignored_path(f, ignore_patterns)
      ]
      ```
- [ ] Modify Case 3 (unclaimed files) to respect `uncovered_action`:
      ```python
      action = config["check_update"]["uncovered_action"]
      if unclaimed and action != "ignore":
          if action == "block":
              # existing block behavior (hookSpecificOutput with decision: block)
              ...
          else:
              # warn: systemMessage, no block, exit 0
              output = {
                  "systemMessage": (
                      "Uncovered files detected: {}.\n"
                      "Consider running the scanner agent to add module coverage."
                  ).format(", ".join(unclaimed))
              }
              sys.stdout.write(json.dumps(output) + "\n")
      ```
- [ ] Verify: `python -m pytest tests/test_check_update.py -v`

---

### Task 4: Migrate `cmd_validate.py`

**Files:**
- Modify: `src/engaku/cmd_validate.py`

- [ ] Remove constants: `FORBIDDEN_PHRASES`, `MIN_CHARS`, `MAX_CHARS`,
      `REQUIRED_HEADING`, `RECENT_SECONDS`
- [ ] Remove `_parse_frontmatter()` function
- [ ] Add imports:
      ```python
      from engaku.constants import FORBIDDEN_PHRASES, MIN_CHARS, MAX_CHARS, REQUIRED_HEADING
      from engaku.utils import parse_frontmatter, load_config
      ```
- [ ] Update `_validate_file()` to accept an optional `max_chars` parameter
      (defaults to `MAX_CHARS`), so `run()` can pass the config value:
      ```python
      def _validate_file(path, max_chars=None):
          if max_chars is None:
              max_chars = MAX_CHARS
          ...
      ```
- [ ] In `run()`, call `load_config(cwd)` and pass `config["max_chars"]` to
      `_validate_file(path, max_chars=config["max_chars"])`
- [ ] Verify: `python -m pytest tests/test_validate.py -v`

---

### Task 5: Migrate `cmd_inject.py`

**Files:**
- Modify: `src/engaku/cmd_inject.py`

- [ ] Remove `SESSION_EDITS` constant
- [ ] Remove `_read_hook_input()` function
- [ ] Remove `_parse_paths_frontmatter()` function
- [ ] Add imports:
      ```python
      from engaku.utils import read_hook_input, parse_frontmatter, parse_paths_from_frontmatter
      ```
- [ ] Rewrite `_build_module_index()` to use shared functions:
      read file content → `parse_frontmatter(content)` → if frontmatter exists,
      `parse_paths_from_frontmatter(fm_str)` → build table.
      (Currently it has its own inline parsing; switch to shared functions.)
- [ ] Update `run()`: `_read_hook_input()` → `read_hook_input()`
- [ ] Verify: `python -m pytest tests/test_inject.py -v`

---

### Task 6: Migrate `cmd_log_edit.py`

**Files:**
- Modify: `src/engaku/cmd_log_edit.py`

- [ ] Remove all constant definitions (SESSION_EDITS, IGNORED_DIR_NAMES,
      IGNORED_DIR_SUFFIXES, IGNORED_EXTENSIONS, IGNORED_FILENAMES)
- [ ] Remove duplicated functions: `_read_hook_input()`, `_is_code_file()`,
      `_is_ai_file()`, `_relative_to_cwd()`
- [ ] Add imports:
      ```python
      from engaku.constants import SESSION_EDITS
      from engaku.utils import read_hook_input, is_code_file, is_ai_file, relative_to_cwd
      ```
- [ ] Update all call sites to use imported names (drop `_` prefix)
- [ ] Verify: `python -m pytest tests/test_log_edit.py -v`

---

### Task 7: Migrate `cmd_log_read.py`

**Files:**
- Modify: `src/engaku/cmd_log_read.py`

- [ ] Remove `ACCESS_LOG` constant
- [ ] Remove duplicated functions: `_read_hook_input()`, `_is_ai_file()`,
      `_relative_to_cwd()`
- [ ] Add imports:
      ```python
      from engaku.constants import ACCESS_LOG
      from engaku.utils import read_hook_input, is_ai_file, relative_to_cwd
      ```
- [ ] Update all call sites
- [ ] Verify: `python -m pytest tests/test_log_read.py -v`

---

### Task 8: Migrate `cmd_stats.py` and `cmd_apply.py`

**Files:**
- Modify: `src/engaku/cmd_stats.py`
- Modify: `src/engaku/cmd_apply.py`

- [ ] `cmd_stats.py`: remove `STALE_DAYS`, add `from engaku.constants import STALE_DAYS`
- [ ] `cmd_apply.py`: remove `_load_config()`, add `from engaku.utils import load_config`.
      Note: `cmd_apply.py` only reads the `"agents"` key, so its call site changes from
      `_load_config(cwd)` returning `(config, path)` to `load_config(cwd)` returning
      a dict. Adjust the call site accordingly — the config path for error messages
      can be constructed from `constants.CONFIG_FILE`.
- [ ] `cmd_apply.py`: remove inline frontmatter parsing in `_update_agent_model()`,
      use `from engaku.utils import parse_frontmatter` instead
- [ ] Verify: `python -m pytest tests/ -v`

---

### Task 9: Update `engaku.json` schema (template + dogfooding)

**Files:**
- Modify: `src/engaku/templates/ai/engaku.json`
- Modify: `.ai/engaku.json`

- [ ] Update `src/engaku/templates/ai/engaku.json` to new schema:
      ```json
      {
        "agents": {},
        "max_chars": 1200,
        "check_update": {
          "ignore": [],
          "uncovered_action": "warn"
        }
      }
      ```
- [ ] Update `.ai/engaku.json` (engaku's own config) to new schema:
      ```json
      {
        "agents": {
          "dev": "Claude Sonnet 4.6 (copilot)",
          "knowledge-keeper": "GPT-5 mini (copilot)",
          "planner": "Claude Sonnet 4.6 (copilot)",
          "scanner": "Claude Sonnet 4.6 (copilot)",
          "scanner-update": "GPT-5 mini (copilot)"
        },
        "max_chars": 1200,
        "check_update": {
          "ignore": [
            "docs/"
          ],
          "uncovered_action": "warn"
        }
      }
      ```
- [ ] Verify: `python -c "from engaku.utils import load_config; import os; c = load_config(os.getcwd()); print(c)"`

---

### Task 10: Update all tests

**Files:**
- Modify: `tests/test_check_update.py`
- Modify: `tests/test_validate.py`
- Modify: `tests/test_inject.py`
- Modify: `tests/test_log_edit.py`
- Modify: `tests/test_log_read.py`

- [ ] Fix any broken imports in existing tests (constants/functions moved)
- [ ] Add tests in `test_check_update.py`:
      - `test_config_ignore_filters_files`: write engaku.json with `check_update.ignore: ["docs/"]`,
        create a changed file under `docs/`, verify it is filtered out
      - `test_uncovered_action_warn`: set `uncovered_action: "warn"`, verify systemMessage
        output (not block)
      - `test_uncovered_action_ignore`: set `uncovered_action: "ignore"`, verify no output
        for uncovered files
      - `test_uncovered_action_block`: set `uncovered_action: "block"`, verify existing
        block behavior preserved
- [ ] Add test for `load_config()` defaults: missing keys fall back correctly
- [ ] Verify all tests pass: `python -m pytest tests/ -v`

---

## Execution Notes

- Tasks 1-2 (create shared modules) must be done first.
- Tasks 3-8 (migrate cmd files) can be done in any order but should each be
  verified individually before moving on.
- Task 9 (config schema) can be done at any point after Task 2.
- Task 10 (tests) should be done last, after all migrations are complete,
  to fix any remaining import breakage in one pass.
- **Recommended approach:** do Tasks 1-2 together, then iterate through 3-8
  one file at a time with test verification after each, then 9, then 10.

## Out of Scope

- Refactoring `_match_path()` — stays in `cmd_check_update.py` since it's only
  used there (plus the new `_is_ignored_path` wrapper). If needed elsewhere
  later, can be moved to `utils.py` in a separate PR.
- JSON schema validation for `engaku.json` — invalid keys are silently ignored,
  missing keys fall back to defaults.
- Migration of `_extract_edited_paths()` (cmd_log_edit) or `_extract_file_path()`
  (cmd_log_read) — these are module-specific, not duplicated.
