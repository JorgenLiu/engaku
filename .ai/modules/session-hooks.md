---
paths:
  - src/engaku/cmd_inject.py
  - src/engaku/cmd_log_read.py
  - tests/test_inject.py
  - tests/test_log_read.py
  - src/engaku/cmd_prompt_check.py
  - tests/test_prompt_check.py

---
## Overview
Session-lifecycle hooks.

`cmd_inject.py` (SessionStart/PreCompact) scans `.ai/modules/*.md` `paths:` frontmatter to build a module index table, then composes `rules.md` + `overview.md` + index. Returns `hookSpecificOutput.additionalContext` for SessionStart, `systemMessage` for PreCompact.

`cmd_log_read.py` (PostToolUse) appends file paths touched by write tools to the access log and exposes `read_hook_input` / access-log helpers used by other hook commands.

`cmd_prompt_check.py` (UserPromptSubmit) reads stdin JSON via `read_hook_input`, extracts `prompt`, and checks case-insensitively against `_KEYWORDS` (Chinese/English tokens: "从现在开始", "不要用", "always", "never", "规则", "rule", "preference", "constraint", "禁止", "必须", "要求"). Match → `systemMessage` reminding user to update `.ai/rules.md`; no match → `{}`. Always exits 0.

Tests: `test_inject.py`, `test_log_read.py`, `test_prompt_check.py` (14 cases: keyword detection, case-insensitivity, empty/missing prompts, exit code 0).
