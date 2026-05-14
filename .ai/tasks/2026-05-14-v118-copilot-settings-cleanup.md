---
plan_id: 2026-05-14-v118-copilot-settings-cleanup
title: VS Code 1.120 Copilot settings defaults
status: done
created: 2026-05-14
---

## Background

VS Code 1.120 introduced `chat.tools.compressOutput.enabled`, a preview setting for compressing large agent tool output before it enters model context. Engaku's 1.1.18 README currently documents it as optional, but the setting directly supports Engaku's compactness and token-budget goals. The generated `.vscode/settings.json` still writes `chat.useCustomAgentHooks`, which local VS Code 1.120 reports as unknown.

## Design

Integrate `chat.tools.compressOutput.enabled` into generated defaults with value `true`. Official Copilot settings docs list it under Agent settings, default `false`, preview, and describe large terminal output compression that collapses unchanged diff hunks, drops lockfile diffs, and strips install progress. VS Code source confirms the setting key is `ChatConfiguration.CompressOutputEnabled`, default `false`, preview, and gates `ToolResultCompressorService.maybeCompress`; current registered filters target terminal outputs such as `git diff`, `git status`, `ls -l`, `find`, `rg`/`grep`, test runners, build tools, linters, package installs, and `env`, while structured JSON/YAML/TOML-like text is protected from compression. Enable it by default because Engaku optimizes agent sessions for compact, exact work and most generated projects benefit immediately. Document the preview risk: users can disable it if they need full raw output in model context.

Remove `chat.useCustomAgentHooks` from generated settings. Official Copilot settings docs still list it as Preview/default `false`, but local VS Code 1.120 reports it as unknown and current VS Code source shows hooks are controlled by `PromptsConfig.USE_CHAT_HOOKS = "chat.useHooks"`, registered as default `true`, restricted, preview, and policy-backed. Source also shows selected custom agent frontmatter hooks are merged into request hooks when `chat.useHooks` is enabled. Do not generate `chat.useHooks`; it already defaults to `true`, and explicit workspace settings should not override user or policy choices. Remove the obsolete key from this repo's `.vscode/settings.json` and have init/update stop writing it. Add cleanup for the obsolete generated key during `engaku init`/`engaku update` when `.vscode/settings.json` is valid JSON, preserving unrelated settings.

Keep this as a 1.1.18 follow-up task because `.ai/tasks/2026-05-14-github-mcp-office-lessons.md` is already marked `status: done` by reviewer. This task belongs to the same release train and should be completed before publishing 1.1.18.

## File Map

- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.vscode/settings.json`
- Modify: `.ai/overview.md`
- Delete: none

## Tasks

- [x] 1. **Update settings helpers**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`
  - Steps:
    - Add a helper that removes one key from `.vscode/settings.json` when the file is valid JSON and preserves all unrelated keys.
    - Stop writing `chat.useCustomAgentHooks` in both `engaku init` and `engaku update`.
    - Write `chat.tools.compressOutput.enabled: true` in both `engaku init` and `engaku update` using the existing merge behavior.
    - Remove obsolete `chat.useCustomAgentHooks` during init/update after reading existing settings.
    - Do not write `chat.useHooks`; VS Code source defaults it to `true` and user/policy ownership should remain intact.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 2. **Adjust settings tests**
  - Files: `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Replace assertions expecting `chat.useCustomAgentHooks` with assertions that the key is absent.
    - Add assertions that `chat.tools.compressOutput.enabled` is generated as `true`.
    - Add preservation tests proving unrelated `.vscode/settings.json` keys survive init/update.
    - Add cleanup tests proving an existing `chat.useCustomAgentHooks` key is removed during init/update.
    - Keep existing assertions that `github.copilot.chat.skillTool.enabled` is not generated.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 3. **Update release docs**
  - Files: `README.md`, `CHANGELOG.md`, `.vscode/settings.json`
  - Steps:
    - Change the generated-file summary so `.vscode/settings.json` says it enables Copilot terminal/tool-output compression, not custom agent hooks.
    - Move `chat.tools.compressOutput.enabled` out of the optional-settings note and state that Engaku now enables it by default in generated workspace settings.
    - Correct the effect text to terminal/tool output examples from VS Code source/docs: `git diff`, `ls -l`, package install progress, test/build/lint output, and repeated terminal-output cache hits.
    - Keep `chat.tools.riskAssessment.enabled` optional; do not enable it by default.
    - Add a 1.1.18 changelog entry that Engaku now enables `chat.tools.compressOutput.enabled` and removes obsolete `chat.useCustomAgentHooks` generation.
    - Remove `chat.useCustomAgentHooks` from this repo's `.vscode/settings.json` and add `chat.tools.compressOutput.enabled: true`.
  - Verify: `grep -n "chat.tools.compressOutput.enabled\|chat.useCustomAgentHooks\|chat.tools.riskAssessment.enabled" README.md CHANGELOG.md .vscode/settings.json`

- [x] 4. **Update project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - Replace the current v1.1.18 history sentence with this exact text: `v1.1.18 adds default GitHub MCP integration using the official hosted read-only endpoint and a bundled github skill for safe repository, issue, PR, and workflow context. The release also changes lesson memory to method-first entries with promotion into stable instruction files, fixes XLSX formula-graph traversal (all-sheets scanning, BFS max-depth, named-range resolution), adds read-only DOCX comments/tracked-change inspection, enables VS Code's preview terminal/tool-output compression setting by default, and stops generating the obsolete chat.useCustomAgentHooks workspace setting.`
  - Verify: `grep -n "v1.1.18 adds default GitHub MCP integration\|chat.useCustomAgentHooks\|terminal/tool-output compression" .ai/overview.md`

- [x] 5. **Run final verification**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `tests/test_init.py`, `tests/test_update.py`, `README.md`, `CHANGELOG.md`, `.vscode/settings.json`, `.ai/overview.md`
  - Steps:
    - Run focused init/update tests.
    - Run the full unittest suite.
    - Inspect a temp `engaku init` output and generated `.vscode/settings.json` to confirm `chat.tools.compressOutput.enabled` is present and `chat.useCustomAgentHooks` is absent.
    - Confirm README/CHANGELOG no longer describe `chat.tools.compressOutput.enabled` as optional-only.
  - Verify: `python -m unittest tests.test_init tests.test_update && python -m unittest discover -s tests`

## Out of Scope

- Enabling `chat.tools.riskAssessment.enabled` by default.
- Generating `chat.useHooks` explicitly.
- Changing hook file formats or moving Engaku hooks out of `.agent.md` frontmatter.
- Reworking `.vscode/settings.json` parsing beyond the existing valid-JSON behavior.
- Publishing or tagging the release.