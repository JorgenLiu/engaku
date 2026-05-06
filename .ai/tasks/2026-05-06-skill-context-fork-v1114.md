---
plan_id: 2026-05-06-skill-context-fork-v1114
title: Enable dedicated context for bundled tool-heavy skills
status: done
created: 2026-05-06
---

## Background
VS Code 1.118 adds experimental dedicated skill context. The release notes state that skills with multi-step tool calls or large reference material can crowd the main chat context, and can instead run in a dedicated subagent context by adding `context: fork` to `SKILL.md` frontmatter. The feature requires `github.copilot.chat.skillTool.enabled`.

## Design
Add `context: fork` only to bundled skills that are likely to execute tools, gather external context, inspect files, verify work, or carry large workflow reference material. Keep lightweight, always-on reasoning skills inline so their guidance stays directly in the main agent context.

Add `context: fork` to:
- `systematic-debugging`
- `verification-before-completion`
- `frontend-design`
- `proactive-initiative`
- `mcp-builder`
- `doc-coauthoring`
- `skill-authoring`
- `chrome-devtools`
- `context7`
- `database`

Do not add `context: fork` to:
- `brainstorming` — primarily interactive clarification, not a tool-heavy retrieval workflow.
- `karpathy-guidelines` — compact coding principles intended to shape main-agent reasoning directly.

`engaku init` already uses `_ensure_vscode_setting` for `.vscode/settings.json`; reuse that path to also set `github.copilot.chat.skillTool.enabled` to `true`. Preserve existing settings and skip when already set.

Add a README chapter with exact Windows/Linux commands to install the current compact instruction content into the user-level Copilot instruction path. The source content inspected on 2026-05-06 is:

```md
---
applyTo: "**"
---
NEVER output warmth, curiosity, playfulness, or personality. NEVER say "Great!", "Sure!", "Happy to help!", or any affirmation.
NEVER narrate what you are about to do ("I will now...", "Let me...", "I'll start by..."). Report actions and findings only.
NEVER send intermediary status updates before using tools. Use tools immediately; narrate nothing.
ALWAYS respond in the most compact, information-dense form. Fragments are preferred over prose sentences.
ALWAYS use bullets or tables when listing multiple items. NEVER default to flowing prose paragraphs.
```

Version `1.1.14` documents this as a token-efficiency/customization release: forked skill context, generated VS Code setting, compact-instruction README guidance.

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
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Add fork context to template skills**
  - Files: `src/engaku/templates/skills/systematic-debugging/SKILL.md`, `src/engaku/templates/skills/verification-before-completion/SKILL.md`, `src/engaku/templates/skills/frontend-design/SKILL.md`, `src/engaku/templates/skills/proactive-initiative/SKILL.md`, `src/engaku/templates/skills/mcp-builder/SKILL.md`, `src/engaku/templates/skills/doc-coauthoring/SKILL.md`, `src/engaku/templates/skills/skill-authoring/SKILL.md`, `src/engaku/templates/skills/chrome-devtools/SKILL.md`, `src/engaku/templates/skills/context7/SKILL.md`, `src/engaku/templates/skills/database/SKILL.md`
  - Steps:
    - Add `context: fork` to each listed `SKILL.md` frontmatter directly after `description:`.
    - Do not edit `src/engaku/templates/skills/brainstorming/SKILL.md` or `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`.
  - Verify: `grep -R "^context: fork" src/engaku/templates/skills | wc -l`

- [x] 2. **Mirror fork context in live skills**
  - Files: `.github/skills/systematic-debugging/SKILL.md`, `.github/skills/verification-before-completion/SKILL.md`, `.github/skills/frontend-design/SKILL.md`, `.github/skills/proactive-initiative/SKILL.md`, `.github/skills/mcp-builder/SKILL.md`, `.github/skills/doc-coauthoring/SKILL.md`, `.github/skills/skill-authoring/SKILL.md`, `.github/skills/chrome-devtools/SKILL.md`, `.github/skills/context7/SKILL.md`, `.github/skills/database/SKILL.md`
  - Steps:
    - Add the same `context: fork` frontmatter line to the live skill files.
    - Keep live and template frontmatter aligned for each edited skill.
  - Verify: `grep -R "^context: fork" .github/skills | wc -l`

- [x] 3. **Enable skill tool setting during init**
  - Files: `src/engaku/cmd_init.py`
  - Steps:
    - Keep `_ensure_vscode_setting(cwd, "chat.useCustomAgentHooks", True, out)`.
    - Add `_ensure_vscode_setting(cwd, "github.copilot.chat.skillTool.enabled", True, out)` near the existing `.vscode/settings.json` setup.
    - If needed, update the helper docstring/comment so `_ensure_vscode_setting` clearly covers VS Code settings merged by init, not only hooks.
  - Verify: `grep -n "github.copilot.chat.skillTool.enabled" src/engaku/cmd_init.py`

- [x] 4. **Test generated VS Code settings**
  - Files: `tests/test_init.py`
  - Steps:
    - Add a stdlib `unittest` case that runs `engaku init`, loads `.vscode/settings.json`, and asserts both `chat.useCustomAgentHooks` and `github.copilot.chat.skillTool.enabled` are `True`.
    - Add or extend a preservation test so pre-existing unrelated settings remain after init.
  - Verify: `python -m unittest tests.test_init`

- [x] 5. **Document compact instruction installation**
  - Files: `README.md`
  - Steps:
    - Add a new chapter near `Global kernel and lossless compactness` named `## User-level compact instruction`.
    - State the target paths: Windows `%USERPROFILE%\.copilot\instructions\compact.instructions.md`; Linux `~/.copilot/instructions/compact.instructions.md`.
    - Include PowerShell and Linux shell commands that create the directory and write the exact compact instruction block shown in this task's Design section.
  - Verify: `grep -n "User-level compact instruction\|compact.instructions.md" README.md`

- [x] 6. **Record release notes and version bump**
  - Files: `CHANGELOG.md`, `pyproject.toml`, `src/engaku/__init__.py`
  - Steps:
    - Add `## [1.1.14] - 2026-05-06` under `## [Unreleased]` with bullets for forked skill context, generated VS Code setting, and README user-level compact instruction guidance.
    - Change `version = "1.1.13"` to `version = "1.1.14"` in `pyproject.toml`.
    - Change `__version__ = "1.1.13"` to `__version__ = "1.1.14"` in `src/engaku/__init__.py`.
  - Verify: `grep -n "1.1.14" CHANGELOG.md pyproject.toml src/engaku/__init__.py`

- [x] 7. **Update overview with exact release summary**
  - Files: `.ai/overview.md`
  - Steps:
    - Append this exact sentence to the Overview paragraph: `v1.1.14 enables VS Code 1.118 dedicated skill context for bundled tool-heavy skills via \`context: fork\`, turns on \`github.copilot.chat.skillTool.enabled\` during \`engaku init\`, documents user-level compact instruction installation for Windows and Linux, and bumps package metadata to 1.1.14.`
  - Verify: `grep -n "v1.1.14 enables VS Code 1.118 dedicated skill context" .ai/overview.md`

- [x] 8. **Run full validation**
  - Files: `tests/test_init.py`, `src/engaku/templates/skills/*/SKILL.md`, `.github/skills/*/SKILL.md`, `README.md`, `CHANGELOG.md`, `pyproject.toml`, `src/engaku/__init__.py`
  - Steps:
    - Run the full unittest suite.
    - Confirm `context: fork` appears exactly 20 times across live and template skill files.
    - Confirm `brainstorming` and `karpathy-guidelines` have no `context: fork` line.
  - Verify: `python -m unittest discover`

## Out of Scope
- Enabling `context: fork` for user-created skills outside Engaku's bundled live/template skill set.
- Editing `brainstorming` or `karpathy-guidelines` unless later evidence shows they should run in forked context.
- Publishing to PyPI or creating a git tag.
- Rewriting `.vscode/settings.json` formatting beyond JSON load/dump behavior already used by `_ensure_vscode_setting`.
