---
plan_id: 2026-04-18-failure-memory-and-hooks
title: "Failure memory system, hook coverage, planner verification rule"
status: done
created: 2026-04-18
---

## Background

Agents repeat the same mistakes across sessions (e.g. running `ng` in a
project without Angular CLI, executing tests twice). VS Code transcript
analysis confirmed that tool failures are not structured—`success` is always
`true` at the tool level—so automated detection is unreliable. The most
effective approach is instruction-based self-documentation: agents write
lessons when they encounter errors, and a new `.instructions.md` file
auto-injects those lessons into future sessions.

Separately, only dev has `SessionStart`/`PreCompact` hooks. Planner, reviewer,
and scanner miss project context and active task injection when invoked
directly. Planner's prompt also lacks a rule about verifying external system
behaviour before making assertions.

This is the v0.8.0 release.

## Design

### 1. Lessons instruction file

Create `.github/instructions/lessons.instructions.md` with
`applyTo: "**"` so it is attached whenever the agent touches any file.
The file starts with a brief preamble and an empty `## Lessons` section.
Agents are instructed (via `copilot-instructions.md`) to append one-line
entries here when they encounter errors.

Template version at `src/engaku/templates/instructions/lessons.instructions.md`
uses the same content so `engaku init` and `engaku update` propagate it.

### 2. Hook coverage for all agents

Add `SessionStart` and `PreCompact` hooks to planner, reviewer, and scanner
(both template and live files). Reviewer keeps its existing `SubagentStart`
hook. This ensures all agents receive `<project-context>` and `<active-task>`
injection regardless of how they are invoked.

### 3. Planner verification principle

Add a new bullet to planner's `## Principles` section requiring it to
fetch documentation or source code before asserting facts about external
systems (VS Code APIs, GitHub behaviour, library semantics, etc.).

### 4. Agent lesson-writing instruction

Add a rule to `copilot-instructions.md` (both template and live) telling all
agents to append lessons to `.github/instructions/lessons.instructions.md`
when they encounter environment errors, tool failures, or repeated mistakes.

### 5. Version bump to 0.8.0

Bump version in `pyproject.toml`, `src/engaku/__init__.py`, and add a
CHANGELOG entry.

## File Map

- Create: `src/engaku/templates/instructions/lessons.instructions.md`
- Create: `.github/instructions/lessons.instructions.md`
- Modify: `src/engaku/templates/agents/planner.agent.md` (add hooks)
- Modify: `src/engaku/templates/agents/reviewer.agent.md` (add SessionStart + PreCompact hooks)
- Modify: `src/engaku/templates/agents/scanner.agent.md` (add hooks)
- Modify: `.github/agents/planner.agent.md` (add hooks)
- Modify: `.github/agents/reviewer.agent.md` (add SessionStart + PreCompact hooks)
- Modify: `.github/agents/scanner.agent.md` (add hooks)
- Modify: `src/engaku/templates/copilot-instructions.md` (add lesson-writing rule)
- Modify: `.github/copilot-instructions.md` (add lesson-writing rule)
- Modify: `src/engaku/templates/agents/planner.agent.md` (add verification principle)
- Modify: `.github/agents/planner.agent.md` (add verification principle)
- Modify: `pyproject.toml` (version bump)
- Modify: `src/engaku/__init__.py` (version bump)
- Modify: `CHANGELOG.md` (add 0.8.0 entry)
- Modify: `tests/test_init.py` (add test for lessons template)
- Modify: `tests/test_update.py` (add test for lessons template propagation)

## Tasks

- [x] 1. **Create lessons instruction file (template + live)**
  - Files: `src/engaku/templates/instructions/lessons.instructions.md`, `.github/instructions/lessons.instructions.md`
  - Steps:
    - Create `src/engaku/templates/instructions/lessons.instructions.md` with YAML frontmatter (`applyTo: "**"`) and empty `## Lessons` section with a comment explaining agent append behaviour
    - Copy identical content to `.github/instructions/lessons.instructions.md`
  - Verify: `test -f src/engaku/templates/instructions/lessons.instructions.md && test -f .github/instructions/lessons.instructions.md && head -5 src/engaku/templates/instructions/lessons.instructions.md | grep -q "applyTo" && echo PASS`

- [x] 2. **Add lesson-writing rule to copilot-instructions.md (template + live)**
  - Files: `src/engaku/templates/copilot-instructions.md`, `.github/copilot-instructions.md`
  - Steps:
    - Add a `## Lessons` section to `src/engaku/templates/copilot-instructions.md` with a rule: "When you encounter an environment error, command failure, or repeated mistake, append a one-line lesson to `.github/instructions/lessons.instructions.md` under the `## Lessons` heading. Keep entries concise (one line each). Do not duplicate existing entries."
    - Add the same section to `.github/copilot-instructions.md`
  - Verify: `grep -q "lessons.instructions.md" src/engaku/templates/copilot-instructions.md && grep -q "lessons.instructions.md" .github/copilot-instructions.md && echo PASS`

- [x] 3. **Add hooks to planner agent (template + live)**
  - Files: `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`
  - Steps:
    - Add `hooks:` block with `SessionStart` and `PreCompact` entries (both `engaku inject`, timeout 5) to template frontmatter
    - Add identical `hooks:` block to live file frontmatter (preserve existing `model:` field in live only)
  - Verify: `grep -A2 "SessionStart" src/engaku/templates/agents/planner.agent.md | grep -q "engaku inject" && grep -A2 "PreCompact" .github/agents/planner.agent.md | grep -q "engaku inject" && echo PASS`

- [x] 4. **Add SessionStart + PreCompact hooks to reviewer agent (template + live)**
  - Files: `src/engaku/templates/agents/reviewer.agent.md`, `.github/agents/reviewer.agent.md`
  - Steps:
    - Add `SessionStart` and `PreCompact` hook entries to template frontmatter (keep existing `SubagentStart`)
    - Add identical entries to live file frontmatter (preserve existing `model:` field in live only)
  - Verify: `grep -A2 "SessionStart" .github/agents/reviewer.agent.md | grep -q "engaku inject" && grep -A2 "SubagentStart" .github/agents/reviewer.agent.md | grep -q "engaku inject" && echo PASS`

- [x] 5. **Add hooks to scanner agent (template + live)**
  - Files: `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/scanner.agent.md`
  - Steps:
    - Add `hooks:` block with `SessionStart` and `PreCompact` entries to template frontmatter
    - Add identical entries to live file frontmatter (preserve existing `model:` field in live only)
  - Verify: `grep -A2 "SessionStart" .github/agents/scanner.agent.md | grep -q "engaku inject" && echo PASS`

- [x] 6. **Add verification principle to planner agent (template + live)**
  - Files: `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`
  - Steps:
    - Add to `## Principles` section: `- **Verify before asserting** — when a design decision depends on external tool behaviour, API semantics, or platform capabilities (VS Code, GitHub, npm, etc.), fetch the relevant documentation or source code first. Do not rely on memory for facts about external systems.`
    - Add identical bullet to live file
  - Verify: `grep -q "Verify before asserting" src/engaku/templates/agents/planner.agent.md && grep -q "Verify before asserting" .github/agents/planner.agent.md && echo PASS`

- [x] 7. **Add test for lessons template in test_init.py**
  - Files: `tests/test_init.py`
  - Steps:
    - Add a test method that runs `engaku init` and verifies `lessons.instructions.md` is created in `.github/instructions/` with `applyTo` in its content
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -m pytest tests/test_init.py -v -k lessons 2>&1 | tail -5`

- [x] 8. **Add test for lessons template in test_update.py**
  - Files: `tests/test_update.py`
  - Steps:
    - Add a test method that runs `engaku update` and verifies `lessons.instructions.md` is created/updated in `.github/instructions/`
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -m pytest tests/test_update.py -v -k lessons 2>&1 | tail -5`

- [x] 9. **Version bump to 0.8.0**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`
  - Steps:
    - Change `version = "0.7.0"` to `version = "0.8.0"` in `pyproject.toml`
    - Change `__version__ = "0.7.0"` to `__version__ = "0.8.0"` in `src/engaku/__init__.py`
  - Verify: `python3 -c "import engaku; assert engaku.__version__ == '0.8.0'; print('PASS')"`

- [x] 10. **Add CHANGELOG entry for 0.8.0**
  - Files: `CHANGELOG.md`
  - Steps:
    - Add `## [0.8.0] — 2026-04-18` entry above the 0.7.0 entry with sections: Added (lessons instruction file, hook coverage for all agents, planner verification principle), Changed (copilot-instructions.md gains lesson-writing rule)
  - Verify: `head -20 CHANGELOG.md | grep -q "0.8.0" && echo PASS`

- [x] 11. **Run full test suite**
  - Files: (none)
  - Steps:
    - Run `cd /Users/jordan.liu/dev/engaku && python -m pytest tests/ -v 2>&1 | tail -20`
    - Confirm all tests pass
  - Verify: `python -m pytest tests/ -v 2>&1 | grep -E "passed|failed" | tail -1`

- [x] 12. **Update .ai/overview.md**
  - Files: `.ai/overview.md`
  - Steps:
    - Add mention of lessons instruction file in overview text
    - Add `src/engaku/templates/instructions/` to Directory Structure
  - Verify: `grep -q "lessons" .ai/overview.md && echo PASS`

## Out of Scope

- Transcript-based automated failure detection (deferred — data gaps make it unreliable)
- Skill-creator agent (design saved in `.ai/docs/skill-creator-agent-design.md`)
- `engaku learn` subcommand for transcript analysis (deferred)
- Modifying `cmd_inject.py` logic (current inject handles all hooks correctly already)
- Changing the lessons file format beyond one-line entries
