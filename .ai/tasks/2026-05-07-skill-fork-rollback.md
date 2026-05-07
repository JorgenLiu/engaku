---
plan_id: 2026-05-07-skill-fork-rollback
title: Temporarily roll back forked skill context
status: done
created: 2026-05-07
---

## Background
VS Code 1.118's skill tool path is still experimental. Public VS Code issue microsoft/vscode#312445 describes `github.copilot.chat.skillTool.enabled` as a new experimental skill execution tool whose main goal is regression testing, and microsoft/vscode#312904 shows UI behavior still being refined for skill-tool execution. Community issue kimseungbin/claude-skills#13 reports that `context: fork` can isolate a skill into a subagent where deferred tools are unavailable; its proposed fix is to remove `context: fork`. Local practice also found that enabling `github.copilot.chat.skillTool.enabled` changes skill storage behavior and that forked skills can trigger confusing multi-subagent execution.

## Design
Temporarily revert Engaku's v1.1.14 fork-context integration until upstream behavior stabilizes. Remove `context: fork` from every bundled live/template skill that v1.1.14 changed, and stop `engaku init` from writing `github.copilot.chat.skillTool.enabled` into newly generated `.vscode/settings.json`.

Do not delete a user's pre-existing `github.copilot.chat.skillTool.enabled` setting from an existing workspace; Engaku should only stop generating or requiring it. Keep `chat.useCustomAgentHooks` unchanged. Keep the v1.1.14 changelog entry as historical record, then add a new rollback entry for the next version.

## File Map
- Modify: `src/engaku/templates/skills/systematic-debugging/SKILL.md`
- Modify: `src/engaku/templates/skills/verification-before-completion/SKILL.md`
- Modify: `src/engaku/templates/skills/frontend-design/SKILL.md`
- Modify: `src/engaku/templates/skills/proactive-initiative/SKILL.md`
- Modify: `src/engaku/templates/skills/mcp-builder/SKILL.md`
- Modify: `src/engaku/templates/skills/doc-coauthoring/SKILL.md`
- Modify: `src/engaku/templates/skills/skill-authoring/SKILL.md`
- Modify: `src/engaku/templates/skills/chrome-devtools/SKILL.md`
- Modify: `src/engaku/templates/skills/context7/SKILL.md`
- Modify: `src/engaku/templates/skills/database/SKILL.md`
- Modify: `.github/skills/systematic-debugging/SKILL.md`
- Modify: `.github/skills/verification-before-completion/SKILL.md`
- Modify: `.github/skills/frontend-design/SKILL.md`
- Modify: `.github/skills/proactive-initiative/SKILL.md`
- Modify: `.github/skills/mcp-builder/SKILL.md`
- Modify: `.github/skills/doc-coauthoring/SKILL.md`
- Modify: `.github/skills/skill-authoring/SKILL.md`
- Modify: `.github/skills/chrome-devtools/SKILL.md`
- Modify: `.github/skills/context7/SKILL.md`
- Modify: `.github/skills/database/SKILL.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `tests/test_init.py`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Remove fork context from template skills**
  - Files: `src/engaku/templates/skills/systematic-debugging/SKILL.md`, `src/engaku/templates/skills/verification-before-completion/SKILL.md`, `src/engaku/templates/skills/frontend-design/SKILL.md`, `src/engaku/templates/skills/proactive-initiative/SKILL.md`, `src/engaku/templates/skills/mcp-builder/SKILL.md`, `src/engaku/templates/skills/doc-coauthoring/SKILL.md`, `src/engaku/templates/skills/skill-authoring/SKILL.md`, `src/engaku/templates/skills/chrome-devtools/SKILL.md`, `src/engaku/templates/skills/context7/SKILL.md`, `src/engaku/templates/skills/database/SKILL.md`
  - Steps:
    - Delete only the `context: fork` frontmatter line from each listed template skill.
    - Leave descriptions, tool guidance, and all skill body content unchanged.
  - Verify: `grep -R "^context: fork" src/engaku/templates/skills || true`

- [x] 2. **Mirror fork removal in live skills**
  - Files: `.github/skills/systematic-debugging/SKILL.md`, `.github/skills/verification-before-completion/SKILL.md`, `.github/skills/frontend-design/SKILL.md`, `.github/skills/proactive-initiative/SKILL.md`, `.github/skills/mcp-builder/SKILL.md`, `.github/skills/doc-coauthoring/SKILL.md`, `.github/skills/skill-authoring/SKILL.md`, `.github/skills/chrome-devtools/SKILL.md`, `.github/skills/context7/SKILL.md`, `.github/skills/database/SKILL.md`
  - Steps:
    - Delete only the `context: fork` frontmatter line from each listed live skill.
    - Keep live and template frontmatter aligned for every edited skill.
  - Verify: `grep -R "^context: fork" .github/skills || true`

- [x] 3. **Stop generating skillTool setting**
  - Files: `src/engaku/cmd_init.py`
  - Steps:
    - Remove `_ensure_vscode_setting(cwd, "github.copilot.chat.skillTool.enabled", True, out)`.
    - Keep `_ensure_vscode_setting(cwd, "chat.useCustomAgentHooks", True, out)` unchanged.
    - Do not add deletion logic for existing user settings.
  - Verify: `grep -n "github.copilot.chat.skillTool.enabled" src/engaku/cmd_init.py || true`

- [x] 4. **Update init settings tests**
  - Files: `tests/test_init.py`
  - Steps:
    - Change `test_vscode_settings_generated` so it expects `chat.useCustomAgentHooks` to be `True` and expects `github.copilot.chat.skillTool.enabled` to be absent from fresh generated settings.
    - Change `test_vscode_settings_preserves_existing` so it still verifies unrelated settings are preserved and `chat.useCustomAgentHooks` is `True`, without expecting Engaku to add `github.copilot.chat.skillTool.enabled`.
  - Verify: `python -m unittest tests.test_init`

- [x] 5. **Record rollback release metadata**
  - Files: `CHANGELOG.md`, `pyproject.toml`, `src/engaku/__init__.py`
  - Steps:
    - Add `## [1.1.15] - 2026-05-07` under `## [Unreleased]`.
    - Add a `### Changed` bullet: `Temporarily removed bundled skill \`context: fork\` frontmatter and stopped generating \`github.copilot.chat.skillTool.enabled\` because upstream skill-tool/fork behavior is still experimental and can cause confusing subagent/tool behavior.`
    - Change package version from `1.1.14` to `1.1.15` in both metadata files.
  - Verify: `grep -n "1.1.15\|context: fork\|github.copilot.chat.skillTool.enabled" CHANGELOG.md pyproject.toml src/engaku/__init__.py`

- [x] 6. **Update overview with rollback note**
  - Files: `.ai/overview.md`
  - Steps:
    - Append this exact sentence to the Overview paragraph: `v1.1.15 temporarily reverts the VS Code skillTool/fork-context integration: bundled skills no longer include \`context: fork\`, and \`engaku init\` no longer writes \`github.copilot.chat.skillTool.enabled\`, pending upstream stabilization of forked skill execution and storage behavior.`
  - Verify: `grep -n "v1.1.15 temporarily reverts" .ai/overview.md`

- [x] 7. **Run full validation**
  - Files: `src/engaku/templates/skills/*/SKILL.md`, `.github/skills/*/SKILL.md`, `src/engaku/cmd_init.py`, `tests/test_init.py`, `CHANGELOG.md`, `pyproject.toml`, `src/engaku/__init__.py`, `.ai/overview.md`
  - Steps:
    - Run the full stdlib unittest suite.
    - Confirm `context: fork` no longer appears in live or template skill files.
    - Confirm `github.copilot.chat.skillTool.enabled` remains only in historical docs/changelog/task text, not in `src/engaku/cmd_init.py` or active init tests.
  - Verify: `python -m unittest discover`

## Out of Scope
- Removing user-created skills or user-level skill directories.
- Deleting `github.copilot.chat.skillTool.enabled` from existing user/workspace settings.
- Rewriting bundled skill bodies beyond removing `context: fork` frontmatter.
- Publishing to PyPI, pushing tags, or committing changes.