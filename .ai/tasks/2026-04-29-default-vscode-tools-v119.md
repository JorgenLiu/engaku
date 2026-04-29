---
plan_id: 2026-04-29-default-vscode-tools-v119
title: Default VS Code Semantic Tools v1.1.9
status: done
created: 2026-04-29
---

## Background
Engaku is focused on VS Code Copilot, so the bundled agents should use VS Code's default built-in tools before considering custom extensions or MCP-based LSP bridges. Planner, scanner, and coder already have broad read/search capabilities, but the semantic and context tools should be listed explicitly so generated agents expose them consistently. This release also bumps the package version to 1.1.9.

## Design
Add only VS Code default built-in tools; do not introduce any MCP server, VS Code extension, or custom LSP wrapper. Preserve every existing tool entry in each agent and append the new entries without removing live MCP wildcard tools such as `context7/*`, `dbhub/*`, or `chrome-devtools/*`. This change is a generic capability update, not a task-specific workflow for API call-chain analysis.

Default built-in tools to add where missing:
- `selection`
- `read/problems`
- `search/changes`
- `search/codebase`
- `search/usages`
- `vscode/askQuestions`

## File Map
- Modify: `.github/agents/planner.agent.md`
- Modify: `.github/agents/scanner.agent.md`
- Modify: `.github/agents/coder.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/scanner.agent.md`
- Modify: `src/engaku/templates/agents/coder.agent.md`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `CHANGELOG.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Add default tools to live agents**
  - Files: `.github/agents/planner.agent.md`, `.github/agents/scanner.agent.md`, `.github/agents/coder.agent.md`
  - Steps:
    - Append the default built-in tools listed in the Design section to planner, scanner, and coder where missing.
    - Preserve all existing tools in each file, including current MCP wildcard tools and role-specific tool sets.
    - Do not add `vscode/runCommand`, `vscode/installExtension`, `newWorkspace`, or experimental `browser` tools.
  - Verify: `python - <<'PY'
from pathlib import Path
required = {'selection','read/problems','search/changes','search/codebase','search/usages','vscode/askQuestions'}
for path in ['.github/agents/planner.agent.md','.github/agents/scanner.agent.md','.github/agents/coder.agent.md']:
    text = Path(path).read_text()
    missing = sorted(tool for tool in required if tool not in text)
    assert not missing, (path, missing)
print('live agent tool entries present')
PY`

- [x] 2. **Sync generated agent templates**
  - Files: `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `src/engaku/templates/agents/coder.agent.md`
  - Steps:
    - Apply the same default built-in tool additions to the generated templates.
    - Preserve each template's existing tool entries and role boundaries.
    - Keep scanner without `execute` unless it already has it; this task only adds the default read/search/context tools listed above.
  - Verify: `python - <<'PY'
from pathlib import Path
required = {'selection','read/problems','search/changes','search/codebase','search/usages','vscode/askQuestions'}
for path in ['src/engaku/templates/agents/planner.agent.md','src/engaku/templates/agents/scanner.agent.md','src/engaku/templates/agents/coder.agent.md']:
    text = Path(path).read_text()
    missing = sorted(tool for tool in required if tool not in text)
    assert not missing, (path, missing)
print('template agent tool entries present')
PY`

- [x] 3. **Bump package version to 1.1.9**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`
  - Steps:
    - Change `[project].version` from `1.1.8` to `1.1.9`.
    - Change `__version__` from `1.1.8` to `1.1.9`.
  - Verify: `python - <<'PY'
from pathlib import Path
assert 'version = "1.1.9"' in Path('pyproject.toml').read_text()
assert '__version__ = "1.1.9"' in Path('src/engaku/__init__.py').read_text()
print('version is 1.1.9')
PY`

- [x] 4. **Update release notes and overview**
  - Files: `CHANGELOG.md`, `.ai/overview.md`
  - Steps:
    - Add a `## [1.1.9] - 2026-04-29` section above `## [1.1.8]`.
    - Move the current Unreleased entries into the 1.1.9 section if they are part of this release, leaving `## [Unreleased]` present for future changes.
    - Add a 1.1.9 changelog entry under `### Added`: `Planner, scanner, and coder agent templates now explicitly include VS Code default semantic/context tools such as selection, read/problems, search/changes, search/codebase, search/usages, and vscode/askQuestions while preserving each agent's existing tools.`
    - Update `.ai/overview.md` by appending this exact sentence to the end of the `## Overview` paragraph: ` v1.1.9 explicitly grants planner, scanner, and coder VS Code default semantic/context tools (`selection`, `read/problems`, `search/changes`, `search/codebase`, `search/usages`, and `vscode/askQuestions`) while preserving existing role-specific and MCP tools.`
  - Verify: `python - <<'PY'
from pathlib import Path
changelog = Path('CHANGELOG.md').read_text()
overview = Path('.ai/overview.md').read_text()
assert '## [1.1.9] - 2026-04-29' in changelog
assert 'Planner, scanner, and coder agent templates now explicitly include VS Code default semantic/context tools' in changelog
assert 'v1.1.9 explicitly grants planner, scanner, and coder VS Code default semantic/context tools' in overview
print('release notes and overview updated')
PY`

- [x] 5. **Run regression tests**
  - Files: `tests/test_init.py`, `tests/test_update.py`, `tests/test_apply.py`
  - Steps:
    - Run the tests most likely to cover generated templates, updates, and applied tool preservation.
    - If these pass, run the full unittest suite.
  - Verify: `python -m unittest tests.test_init tests.test_update tests.test_apply && python -m unittest discover -s tests`

## Out of Scope
- Adding a custom VS Code extension or MCP LSP bridge.
- Adding custom `lsp_hover`, call hierarchy, or other non-default tools.
- Changing agent role boundaries or adding task-specific API call-chain workflows.
- Releasing to PyPI or pushing a git tag.