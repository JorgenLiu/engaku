---
plan_id: 2026-05-14-github-mcp-office-lessons
title: Default GitHub MCP, Office skill extensions, and lesson tuning
status: done
created: 2026-05-14
---

## Background

VS Code 1.120 adds stronger MCP and agent customization surfaces, and GitHub now provides an official hosted MCP server that can connect directly from GitHub Copilot in VS Code. Engaku already ships default MCP config and MCP-focused skills, so GitHub fits the existing pattern. The Office skills are useful but have a few advertised capabilities that are incomplete, especially XLSX formula graph traversal. The generated lesson-memory rule also needs a method-first design so agents record reusable ways of working rather than incident explanations.

## Design

Use the research note at `.ai/docs/2026-05-14-copilot-mcp-office-skill-research.md` as implementation evidence.

Add GitHub as a default remote HTTP MCP server using the official read-only endpoint `https://api.githubcopilot.com/mcp/readonly`. This avoids local runtime requirements and prevents write tools by default while still exposing repository, issue, PR, user, and context reads.

Add one bundled MCP skill, `github`, matching the current pattern for `chrome-devtools`, `context7`, and `database`. The skill should focus on setup, authentication model, safe read-before-write behavior, and prompt-injection precautions rather than duplicating upstream tool inventories.

Do not add GitLab in this iteration. Keep the gathered GitLab evidence in the research note as a future optional integration path only.

Tune lesson-memory wording in both live and template instruction files. Lessons should capture reusable methods: checks to run, sequences to follow, constraints to remember, or recovery steps that prevent repeated wasted work. Stable repo-wide rules belong in `copilot-instructions.md` or path-specific `.instructions.md`; the lessons file should hold evolving method memories until they are promoted or removed.

Do not move the lessons list back into `copilot-instructions.md`. The current file has enough physical room, but putting accumulated lessons there would make the always-on kernel noisy. Keep only the policy and promotion rule in `copilot-instructions.md`; keep method entries in `.github/instructions/lessons.instructions.md`, which still applies repo-wide through `applyTo: "**"`.

Fix XLSX formula graph contract drift before adding more XLSX features: implement workbook-wide scanning, real `--max-depth`, same-workbook cross-sheet resolution, named-range support where openpyxl exposes destinations, and small-range expansion. Extend DOCX support with read-only comments and tracked-change inspection, then consider hyperlinks/footnotes/endnotes and richer table metadata.

Do not enable preview Copilot settings such as `chat.tools.compressOutput.enabled`, `chat.tools.riskAssessment.enabled`, `chat.mcp.apps.enabled`, or Agent Plugins by default. Document them as optional follow-ups only.

## File Map

- Create: `src/engaku/templates/skills/github/SKILL.md`
- Modify: `src/engaku/templates/mcp.json`
- Modify: `src/engaku/templates/ai/engaku.json`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `src/engaku/templates/instructions/lessons.instructions.md`
- Modify: `.github/copilot-instructions.md`
- Modify: `.github/instructions/lessons.instructions.md`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `src/engaku/__init__.py`
- Modify: `pyproject.toml`
- Modify: `src/engaku/templates/skills/xlsx-analyze/SKILL.md`
- Modify: `src/engaku/templates/skills/xlsx-analyze/scripts/inspect_workbook.py`
- Modify: `src/engaku/templates/skills/xlsx-analyze/scripts/profile_sheet.py`
- Modify: `src/engaku/templates/skills/xlsx-analyze/scripts/formula_graph.py`
- Modify: `src/engaku/templates/skills/docx-read/SKILL.md`
- Modify: `src/engaku/templates/skills/docx-read/scripts/inspect_docx.py`
- Modify: `src/engaku/templates/skills/docx-read/scripts/extract_text.py`
- Modify: `.ai/overview.md`
- Delete: none

## Tasks

- [x] 1. **Add GitHub MCP tests**
  - Files: `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Add expected init output for `.github/skills/github/SKILL.md` in default init.
    - Assert `engaku init --no-mcp` skips `github` together with existing MCP-related skills.
    - Add update assertions that `_SKILLS` contains `github` and does not contain `gitlab`.
    - Add update tests proving missing `github` skill file and MCP server entry are created.
    - Add assertions for the GitHub read-only URL in generated or merged `.vscode/mcp.json`.
    - Add assertions that no generated `.vscode/mcp.json` contains a `gitlab` server.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 2. **Add GitHub MCP config**
  - Files: `src/engaku/templates/mcp.json`, `src/engaku/templates/ai/engaku.json`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`
  - Steps:
    - Add `github` server with `type: "http"` and `url: "https://api.githubcopilot.com/mcp/readonly"`.
    - Add `github/*` to coder/planner/reviewer default MCP tool grants.
    - Register `github` as an MCP-related skill in init/update paths.
    - Do not add any `gitlab` server, skill, tool grant, README default section, or test expectation.
    - Preserve existing update behavior: merge missing servers only, do not overwrite customized existing server entries.
  - Verify: `python -m unittest tests.test_init tests.test_update tests.test_apply`

- [x] 3. **Write GitHub MCP skill**
  - Files: `src/engaku/templates/skills/github/SKILL.md`
  - Steps:
    - Write `github` skill frontmatter and instructions for GitHub repo/issues/PR/actions context, OAuth default, read-only default, explicit write authorization, and private-content handling.
    - State the default endpoint `https://api.githubcopilot.com/mcp/readonly` and note that write-capable GitHub MCP requires explicit local customization.
    - Keep the skill original and compact; do not copy upstream docs prose.
    - Ensure skill name matches directory name and uses plain lowercase `github`.
  - Verify: `grep -n "read-only\|OAuth\|prompt injection\|https://api.githubcopilot.com/mcp/readonly" src/engaku/templates/skills/github/SKILL.md`

- [x] 4. **Tune lesson method rules**
  - Files: `src/engaku/templates/copilot-instructions.md`, `src/engaku/templates/instructions/lessons.instructions.md`, `.github/copilot-instructions.md`, `.github/instructions/lessons.instructions.md`
  - Steps:
    - Replace the current broad lesson trigger with this exact gate in all four files: `Record lessons as reusable methods, not incident explanations. A good lesson says what to do differently next time: a check to run, sequence to follow, constraint to remember, or recovery step that prevents repeated wasted work. Do not record one-off task facts, guesses, root-cause trivia, user preferences, secrets, transient service failures, or unverified theories. Promote durable repo-wide rules to .github/copilot-instructions.md or a path-specific instruction file; update or remove stale lessons instead of adding duplicates.`
    - Preserve existing frontmatter and `## Lessons` section in `lessons.instructions.md`.
    - Do not alter existing lesson entries.
    - Keep actual lesson entries out of `copilot-instructions.md`; store only the policy/promotion rule there.
  - Verify: `grep -n "Record lessons as reusable methods\|Promote durable repo-wide rules" src/engaku/templates/copilot-instructions.md src/engaku/templates/instructions/lessons.instructions.md .github/copilot-instructions.md .github/instructions/lessons.instructions.md`

- [x] 5. **Document GitHub default**
  - Files: `README.md`, `CHANGELOG.md`, `src/engaku/__init__.py`, `pyproject.toml`
  - Steps:
    - Update README generated-file summary so `.vscode/mcp.json` lists chrome-devtools, context7, dbhub, and GitHub.
    - Move GitHub MCP from Optional MCP Servers into default MCP Servers with read-only endpoint and OAuth/PAT/self-hosted notes.
    - Add optional VS Code 1.120 settings note for terminal output compression and terminal risk assessment without enabling them in generated settings.
    - Add changelog entry and bump version only if this work is intended for the next release.
  - Verify: `grep -n "GitHub MCP\|api.githubcopilot.com/mcp/readonly\|chat.tools.compressOutput.enabled\|chat.tools.riskAssessment.enabled" README.md CHANGELOG.md && python -c "p=open('pyproject.toml').read(); q=open('src/engaku/__init__.py').read(); assert ('version = \"1.1.18\"' in p) == ('__version__ = \"1.1.18\"' in q)"`

- [x] 6. **Fix formula graph contract**
  - Files: `src/engaku/templates/skills/xlsx-analyze/SKILL.md`, `src/engaku/templates/skills/xlsx-analyze/scripts/formula_graph.py`
  - Steps:
    - Scan formulas across all workbook sheets, not just the selected sheet, while preserving `--sheet` as the default focus sheet.
    - Implement `--max-depth` traversal for `--focus` in `dependencies`, `dependents`, and `both` modes.
    - Mark cross-sheet references unresolved only when the sheet is missing or the reference is external.
    - Expand simple same-workbook ranges up to `_MAX_RANGE_EXPAND`; preserve larger ranges as range nodes with warnings.
    - Resolve workbook defined names where openpyxl exposes destinations; warn when names cannot be resolved.
    - Update skill limitations to match implemented behavior.
  - Verify: `python -m py_compile src/engaku/templates/skills/xlsx-analyze/scripts/formula_graph.py && python -m unittest tests.test_init tests.test_update`

- [x] 7. **Expand workbook inspection**
  - Files: `src/engaku/templates/skills/xlsx-analyze/SKILL.md`, `src/engaku/templates/skills/xlsx-analyze/scripts/inspect_workbook.py`, `src/engaku/templates/skills/xlsx-analyze/scripts/profile_sheet.py`
  - Steps:
    - Add hidden sheet state, defined names, Excel table count/names, chart count, image count, data validation count, conditional formatting count, freeze panes, autofilter range, and external-link count where openpyxl exposes them.
    - Change CSV/TSV inspection to stream row counts instead of loading every row into memory.
    - Add profile fields for top values, string length stats, boolean-like flag, duplicate row count, blank header warnings, and duplicate header warnings.
    - Keep outputs deterministic and JSON-safe.
  - Verify: `python -m py_compile src/engaku/templates/skills/xlsx-analyze/scripts/inspect_workbook.py src/engaku/templates/skills/xlsx-analyze/scripts/profile_sheet.py`

- [x] 8. **Add DOCX comments and revisions**
  - Files: `src/engaku/templates/skills/docx-read/SKILL.md`, `src/engaku/templates/skills/docx-read/scripts/inspect_docx.py`, `src/engaku/templates/skills/docx-read/scripts/extract_text.py`
  - Steps:
    - Parse DOCX ZIP/XML read-only for `word/comments.xml`, `w:commentRangeStart`, and `w:commentReference`.
    - Add comment counts and optional comment detail output with id, author, date, text, and anchor status.
    - Parse `w:ins` and `w:del` in document XML and output tracked-change counts plus optional inserted/deleted text snippets.
    - Add hyperlink, footnote, and endnote counts if available without new dependencies.
    - Update skill safety notes: inspection only, no accepting/rejecting tracked changes.
  - Verify: `python -m py_compile src/engaku/templates/skills/docx-read/scripts/inspect_docx.py src/engaku/templates/skills/docx-read/scripts/extract_text.py`

- [x] 9. **Sync live skill templates**
  - Files: `.github/skills/github/SKILL.md`, `.github/skills/xlsx-analyze/SKILL.md`, `.github/skills/xlsx-analyze/scripts/inspect_workbook.py`, `.github/skills/xlsx-analyze/scripts/profile_sheet.py`, `.github/skills/xlsx-analyze/scripts/formula_graph.py`, `.github/skills/docx-read/SKILL.md`, `.github/skills/docx-read/scripts/inspect_docx.py`, `.github/skills/docx-read/scripts/extract_text.py`
  - Steps:
    - Because repository policy requires live and template agent/skill files to stay aligned, copy the implemented template skill changes to the live `.github/skills/` paths in the same operation.
    - Keep user-owned unrelated files untouched.
    - Diff live and template skill payloads to confirm parity.
  - Verify: `diff -ru src/engaku/templates/skills/github .github/skills/github && diff -ru src/engaku/templates/skills/xlsx-analyze .github/skills/xlsx-analyze && diff -ru src/engaku/templates/skills/docx-read .github/skills/docx-read`

- [x] 10. **Update project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - Add this exact history text after the v1.1.17 sentence if the implementation ships as v1.1.18: `v1.1.18 adds default GitHub MCP integration using the official hosted read-only endpoint and a bundled github skill for safe repository, issue, PR, and workflow context. The release also changes lesson memory to method-first entries with promotion into stable instruction files, fixes XLSX formula-graph traversal, and adds read-only DOCX comments/tracked-change inspection.`
    - Add this directory line under `## Directory Structure`: `    src/engaku/templates/skills/github/     Bundled GitHub MCP usage skill for repository, issue, PR, and workflow context`.
  - Verify: `grep -n "v1.1.18 adds default GitHub MCP integration\|templates/skills/github" .ai/overview.md`

- [x] 11. **Run full verification**
  - Files: `src/engaku/templates/mcp.json`, `src/engaku/templates/ai/engaku.json`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `src/engaku/templates/copilot-instructions.md`, `src/engaku/templates/instructions/lessons.instructions.md`, `.github/copilot-instructions.md`, `.github/instructions/lessons.instructions.md`, `tests/test_init.py`, `tests/test_update.py`, `tests/test_apply.py`, `src/engaku/templates/skills/github/SKILL.md`, `src/engaku/templates/skills/xlsx-analyze/scripts/*.py`, `src/engaku/templates/skills/docx-read/scripts/*.py`, `README.md`, `CHANGELOG.md`, `.ai/overview.md`
  - Steps:
    - Run focused init/update/apply tests.
    - Run the full unittest suite.
    - Compile all Office helper scripts in template and live skill directories.
    - Confirm Engaku main dependencies remain empty.
    - Inspect `.vscode/mcp.json` generated by tests or a temp init to confirm no hardcoded secrets, PAT prompts, or GitLab server are added.
  - Verify: `python -m unittest tests.test_init tests.test_update tests.test_apply && python -m unittest discover -s tests && python -m py_compile src/engaku/templates/skills/docx-read/scripts/*.py src/engaku/templates/skills/xlsx-analyze/scripts/*.py .github/skills/docx-read/scripts/*.py .github/skills/xlsx-analyze/scripts/*.py && python -c "p=open('pyproject.toml').read(); assert 'dependencies = []' in p"`

## Out of Scope

- GitLab MCP default integration.
- GitLab MCP optional recipe implementation.
- Enabling write-capable GitHub MCP by default.
- Adding PAT inputs or hardcoded secrets to generated MCP config.
- Enabling preview VS Code settings by default: `chat.tools.compressOutput.enabled`, `chat.tools.riskAssessment.enabled`, `chat.mcp.apps.enabled`, Agent Plugins.
- Repackaging Engaku as a Copilot CLI / VS Code agent plugin.
- Formula evaluation or recalculation.
- DOCX editing, accepting/rejecting tracked changes, or exact layout reproduction.
- Legacy `.doc`, `.xls`, or `.xlsb` support in this iteration.