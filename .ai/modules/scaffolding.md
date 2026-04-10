---
paths:
  - src/engaku/cli.py
  - src/engaku/cmd_init.py
  - src/engaku/utils.py
  - src/engaku/constants.py
  - src/engaku/cmd_apply.py
  - tests/test_init.py
  - tests/test_utils.py
  - tests/test_apply.py
---
## Overview
Project lifecycle layer. `cli.py` routes subcommands; `cmd_init.py` bootstraps the project layout. `constants.py` holds defaults and paths. `utils.py` provides helpers including transcript-edit detection.

`cmd_apply.py` provides repository synchronization helpers:

- `_update_rules_max_chars(rules_path, max_chars)`: replaces the integer after the literal `MAX_CHARS for module knowledge body:` using a regex; returns `(True, "ok")` when it writes the file, `(False, "file not found")` when the rules file is absent, and `(False, "no change")` when the pattern is missing or the value already matches.
- `run()`: applies the `max_chars` sync first (to `.ai/rules.md`), then syncs configured `agents` into `.github/agents/`. Both steps accumulate `total_changed`/`total_skipped`; rules syncing runs even if no agents are configured.

Tests exercise transcript-edit helpers and `cmd_init` installation paths.

`tests/test_apply.py` validates `cmd_apply.py` behaviors at unit and integration levels: it tests `_update_agent_model` (inserting or updating the `model` field in an agent file frontmatter) and `_update_rules_max_chars` (regex-based replacement of the `MAX_CHARS` integer inside `rules.md`). The test suite also exercises `run()` integration paths that perform rules synchronization and agent synchronization, asserting both change and no-change outcomes across configured agent lists.
