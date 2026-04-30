---
plan_id: 2026-04-30-planner-workflow-discretion-v111
title: Planner discretion, compact replies, v1.1.11
status: done
created: 2026-04-30
---

## Background
Planner lost the old discretion guard without an equivalent replacement. The numbered workflow can read as mandatory for every request. Global compactness lacks a chat-language rule, and agent prompts do not locally mark `Lossless Compactness` as mandatory. Release docs mention v1.1.11, but `pyproject.toml` and `src/engaku/__init__.py` still report `1.1.9`.

## Design
Use `.github/copilot-instructions.md` as the source of truth. Add only three exact rules:

- Planner discretion: `Use only the workflow steps the request needs. Simple questions can end after context and a direct answer; task, decision, and doc artifacts are required only when the user asks for them or scope needs them.`
- English replies: `Reply in English unless quoting user text or preserving exact non-English evidence.`
- Agent reinforcement: `Follow the Engaku Global Kernel in .github/copilot-instructions.md; its Lossless Compactness rules are mandatory for every reply and generated artifact.`

Rejected: re-add the old phrase (stale), rewrite the full planner workflow (too broad), duplicate compactness bullets in each agent (drift). Also bump package metadata, changelog, and overview to v1.1.11.

## File Map
- Modify: `.github/agents/planner.agent.md`
- Modify: `.github/agents/coder.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `.github/agents/scanner.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/coder.agent.md`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `src/engaku/templates/agents/scanner.agent.md`
- Modify: `.github/copilot-instructions.md`
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `CHANGELOG.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Restore live planner discretion rule**
  - Files: `.github/agents/planner.agent.md`
  - Steps:
    - Add this sentence under `## How you work`, before the numbered workflow: `Use only the workflow steps the request needs. Simple questions can end after context and a direct answer; task, decision, and doc artifacts are required only when the user asks for them or scope needs them.`
    - Keep ownership limits, terminal-observation-only guidance, and the `.ai/overview.md` restriction unchanged.
    - Do not re-add `Not every conversation needs all three.`
  - Verify: `rg -n "Use only the workflow steps the request needs|Not every conversation needs all three|Produce the needed artifact" .github/agents/planner.agent.md`

- [x] 2. **Mirror planner discretion into template**
  - Files: `src/engaku/templates/agents/planner.agent.md`
  - Steps:
    - Add the exact same discretion sentence under `## How you work`, before the numbered workflow.
    - Preserve template-only frontmatter differences while keeping the body aligned with the live planner prompt.
  - Verify: `python -c "from pathlib import Path; live=Path('.github/agents/planner.agent.md').read_text().split('---',2)[2].strip(); template=Path('src/engaku/templates/agents/planner.agent.md').read_text().split('---',2)[2].strip(); assert live == template; print('planner bodies aligned')"`

- [x] 3. **Add global English-response rule**
  - Files: `.github/copilot-instructions.md`, `src/engaku/templates/copilot-instructions.md`
  - Steps:
    - Under `### Lossless Compactness`, add this exact bullet in both live and template files: `- Reply in English unless quoting user text or preserving exact non-English evidence.`
    - Keep `All user-facing strings in English` in `## Code Style`; do not rely on it for agent chat language.
    - Preserve the live/template differences outside this shared global kernel.
  - Verify: `rg -n "Reply in English unless quoting user text|All user-facing strings in English" .github/copilot-instructions.md src/engaku/templates/copilot-instructions.md`

- [x] 4. **Reinforce compactness in agent prompts**
  - Files: `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`, `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `src/engaku/templates/agents/scanner.agent.md`
  - Steps:
    - Add this exact sentence near the start of each agent body, immediately after the opening role sentence or before the first ownership/workflow section: `Follow the Engaku Global Kernel in .github/copilot-instructions.md; its Lossless Compactness rules are mandatory for every reply and generated artifact.`
    - Do not copy the full `Lossless Compactness` bullet list into agent files; `.github/copilot-instructions.md` remains the source of truth.
    - Preserve live/template frontmatter differences and role-specific workflows.
  - Verify: `for f in .github/agents/*.agent.md src/engaku/templates/agents/*.agent.md; do rg -q "Lossless Compactness rules are mandatory" "$f" || exit 1; done; echo "all agents reinforce compactness"`

- [x] 5. **Bump package metadata to 1.1.11**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`
  - Steps:
    - Change `[project].version` from `1.1.9` to `1.1.11`.
    - Change `__version__` from `1.1.9` to `1.1.11`.
  - Verify: `python -c "from pathlib import Path; assert 'version = \"1.1.11\"' in Path('pyproject.toml').read_text(); assert '__version__ = \"1.1.11\"' in Path('src/engaku/__init__.py').read_text(); print('version is 1.1.11')"`

- [x] 6. **Record global-policy fixes in changelog**
  - Files: `CHANGELOG.md`
  - Steps:
    - Under `## [1.1.11] - 2026-04-30`, add a concise changed entry: `Planner prompt now states its workflow is discretionary: simple questions can end with a direct answer, while task, decision, and doc artifacts are used only when requested or needed by scope.`
    - Under the same section, add a concise changed entry: `Global compactness policy now requires agent replies in English except when quoting user text or preserving exact non-English evidence.`
    - Under the same section, add a concise changed entry: `All agent prompts now explicitly treat the Engaku Global Kernel's Lossless Compactness rules as mandatory for replies and generated artifacts.`
    - Leave `## [Unreleased]` present and empty unless other pending changes already require it.
  - Verify: `rg -n "Planner prompt now states its workflow is discretionary|Global compactness policy now requires agent replies in English|All agent prompts now explicitly treat|## \[1\.1\.11\]" CHANGELOG.md`

- [x] 7. **Align project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - Append this exact sentence to the end of the Overview paragraph: `v1.1.11 also restores planner workflow discretion: the planner uses only the steps a request needs, so simple questions can end with a direct answer while task, decision, and doc artifacts remain reserved for requests or scope that need them.`
    - Append this exact sentence immediately after it: `The same v1.1.11 cleanup also makes English the mandatory agent reply language except when quoting user text or preserving exact non-English evidence.`
    - Append this exact sentence immediately after it: `All generated agent prompts now explicitly require the Engaku Global Kernel's Lossless Compactness rules for every reply and generated artifact, while .github/copilot-instructions.md remains the source of truth.`
    - Do not change the directory structure section.
  - Verify: `rg -n "v1.1.11 also restores planner workflow discretion|The same v1.1.11 cleanup also makes English the mandatory agent reply language|All generated agent prompts now explicitly require" .ai/overview.md`

- [x] 8. **Run regression tests**
  - Files: `tests/`
  - Steps:
    - Run the full stdlib unittest suite from the repository root.
    - Do not fix unrelated failures in this task; report them with exact failing command and output.
  - Verify: `python -m unittest discover -s tests`

- [x] 9. **Check scope before review**
  - Files: `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`, `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `.github/copilot-instructions.md`, `src/engaku/templates/copilot-instructions.md`, `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`, `.ai/overview.md`
  - Steps:
    - Confirm only the four bundled agent prompts changed under `.github/agents/` and `src/engaku/templates/agents/`.
    - Confirm this pass does not edit `hooks:` frontmatter.
    - Review the diff for accidental scope growth beyond the file map.
  - Verify: `git --no-pager diff --name-only -- .github/agents src/engaku/templates/agents .github/copilot-instructions.md src/engaku/templates/copilot-instructions.md pyproject.toml src/engaku/__init__.py CHANGELOG.md .ai/overview.md | cat && ! git --no-pager diff -- .github/agents src/engaku/templates/agents | rg -n "^[+-].*hooks:"`

## Out of Scope
Changing planner ownership boundaries, tools, hooks, model frontmatter, or terminal policy.
Changing non-planner agent behavior beyond the compactness reminder, or changing bundled skills.
Publishing, tagging, committing, or modifying release automation.
