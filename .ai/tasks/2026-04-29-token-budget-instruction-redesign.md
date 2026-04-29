---
plan_id: 2026-04-29-token-budget-instruction-redesign
title: Replace token-budget skill spread with always-on instruction
status: done
created: 2026-04-29
---

## Background

The previous token-budget implementation put global communication policy into a conditional skill and repeated it across unrelated skills. VS Code Copilot only loads skill bodies when the model chooses the skill, so this cannot reliably affect every response. Caveman's useful design is an always-active compact response mode with concrete style rules, intensity controls, and clarity/safety exceptions.

## Design

Create a generated `token-budget.instructions.md` with `applyTo: "**"` and make it the single default source of token-budget behavior. The instruction should use Engaku-authored compact style inspired by Caveman mechanics: terse technical prose, fragments allowed, filler/hedging/pleasantries removed, exact technical content preserved, and normal clear English for risky or ambiguity-prone cases. Remove the current `token-budget` bundled skill and remove token-budget sections from unrelated skills and agent bodies.

Longer analysis is recorded in `.ai/docs/2026-04-29-token-budget-instruction-redesign.md`. The decision is `.ai/decisions/011-token-budget-as-always-on-instruction.md`.

## File Map

- Create: `src/engaku/templates/instructions/token-budget.instructions.md`
- Create: `.github/instructions/token-budget.instructions.md`
- Delete: `src/engaku/templates/skills/token-budget/SKILL.md`
- Delete: `.github/skills/token-budget/SKILL.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `.github/copilot-instructions.md`
- Modify: `src/engaku/templates/agents/coder.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `src/engaku/templates/agents/scanner.agent.md`
- Modify: `.github/agents/coder.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `.github/agents/scanner.agent.md`
- Modify: `src/engaku/templates/skills/brainstorming/SKILL.md`
- Modify: `src/engaku/templates/skills/chrome-devtools/SKILL.md`
- Modify: `src/engaku/templates/skills/context7/SKILL.md`
- Modify: `src/engaku/templates/skills/database/SKILL.md`
- Modify: `src/engaku/templates/skills/doc-coauthoring/SKILL.md`
- Modify: `src/engaku/templates/skills/frontend-design/SKILL.md`
- Modify: `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`
- Modify: `src/engaku/templates/skills/mcp-builder/SKILL.md`
- Modify: `src/engaku/templates/skills/proactive-initiative/SKILL.md`
- Modify: `src/engaku/templates/skills/serena/SKILL.md`
- Modify: `src/engaku/templates/skills/skill-authoring/SKILL.md`
- Modify: `src/engaku/templates/skills/systematic-debugging/SKILL.md`
- Modify: `src/engaku/templates/skills/verification-before-completion/SKILL.md`
- Modify: `.github/skills/brainstorming/SKILL.md`
- Modify: `.github/skills/chrome-devtools/SKILL.md`
- Modify: `.github/skills/context7/SKILL.md`
- Modify: `.github/skills/database/SKILL.md`
- Modify: `.github/skills/doc-coauthoring/SKILL.md`
- Modify: `.github/skills/frontend-design/SKILL.md`
- Modify: `.github/skills/karpathy-guidelines/SKILL.md`
- Modify: `.github/skills/mcp-builder/SKILL.md`
- Modify: `.github/skills/proactive-initiative/SKILL.md`
- Modify: `.github/skills/serena/SKILL.md`
- Modify: `.github/skills/skill-authoring/SKILL.md`
- Modify: `.github/skills/systematic-debugging/SKILL.md`
- Modify: `.github/skills/verification-before-completion/SKILL.md`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `README.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Add always-on token-budget instruction**
  - Files: `src/engaku/templates/instructions/token-budget.instructions.md`, `.github/instructions/token-budget.instructions.md`
  - Steps:
    - Create template and live files with identical Engaku-authored content.
    - Add frontmatter `applyTo: "**"`.
    - Define compact mode as active by default, with optional user controls for normal/lite/full compactness.
    - Include concrete style rules: drop filler, pleasantries, hedging, repeated summaries, avoidable articles, and long lead-ins; fragments are allowed.
    - Include preservation and escape rules: keep code, paths, commands, identifiers, exact errors, verification output, safety warnings, irreversible confirmations, and ordered instructions clear.
  - Verify: `cmp src/engaku/templates/instructions/token-budget.instructions.md .github/instructions/token-budget.instructions.md && grep -n "applyTo: \"\*\*\"\|Compact mode\|fragments\|exact errors\|normal mode" src/engaku/templates/instructions/token-budget.instructions.md`

- [x] 2. **Generate instruction during init and update**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Add `token-budget.instructions.md` to the generated instruction stubs copied by `engaku init`.
    - Add it to the generated instruction stubs created by `engaku update` when missing.
    - Preserve existing user-edited `token-budget.instructions.md` on both init and update.
    - Update init/update tests for creation and preservation.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 3. **Remove token-budget as bundled skill**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `src/engaku/templates/skills/token-budget/SKILL.md`, `.github/skills/token-budget/SKILL.md`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Remove `token-budget` from the init always-copied skill list.
    - Remove `token-budget` from `_SKILLS` in `cmd_update.py`.
    - Delete template and live `token-budget/SKILL.md` files.
    - Update tests so fresh init/update no longer expects or creates `.github/skills/token-budget/SKILL.md`.
  - Verify: `python -m unittest tests.test_init tests.test_update && test ! -e src/engaku/templates/skills/token-budget/SKILL.md && test ! -e .github/skills/token-budget/SKILL.md`

- [x] 4. **Remove duplicated token-budget text from agents and skills**
  - Files: `src/engaku/templates/copilot-instructions.md`, `.github/copilot-instructions.md`, `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`, `src/engaku/templates/skills/brainstorming/SKILL.md`, `src/engaku/templates/skills/chrome-devtools/SKILL.md`, `src/engaku/templates/skills/context7/SKILL.md`, `src/engaku/templates/skills/database/SKILL.md`, `src/engaku/templates/skills/doc-coauthoring/SKILL.md`, `src/engaku/templates/skills/frontend-design/SKILL.md`, `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`, `src/engaku/templates/skills/mcp-builder/SKILL.md`, `src/engaku/templates/skills/proactive-initiative/SKILL.md`, `src/engaku/templates/skills/serena/SKILL.md`, `src/engaku/templates/skills/skill-authoring/SKILL.md`, `src/engaku/templates/skills/systematic-debugging/SKILL.md`, `src/engaku/templates/skills/verification-before-completion/SKILL.md`, `.github/skills/brainstorming/SKILL.md`, `.github/skills/chrome-devtools/SKILL.md`, `.github/skills/context7/SKILL.md`, `.github/skills/database/SKILL.md`, `.github/skills/doc-coauthoring/SKILL.md`, `.github/skills/frontend-design/SKILL.md`, `.github/skills/karpathy-guidelines/SKILL.md`, `.github/skills/mcp-builder/SKILL.md`, `.github/skills/proactive-initiative/SKILL.md`, `.github/skills/serena/SKILL.md`, `.github/skills/skill-authoring/SKILL.md`, `.github/skills/systematic-debugging/SKILL.md`, `.github/skills/verification-before-completion/SKILL.md`
  - Steps:
    - Remove `## Token Budget` sections from all bundled skills.
    - Remove `Token Budget Principle` sections from copilot instructions and all agent bodies.
    - Remove `See the token-budget skill` references.
    - Update `skill-authoring` so generated skills are not required to include token-budget sections.
    - Keep template/live file pairs identical after each edit.
  - Verify: `for skill in brainstorming chrome-devtools context7 database doc-coauthoring frontend-design karpathy-guidelines mcp-builder proactive-initiative serena skill-authoring systematic-debugging verification-before-completion; do cmp "src/engaku/templates/skills/$skill/SKILL.md" ".github/skills/$skill/SKILL.md" || exit 1; done && ! grep -R "Token Budget\|token-budget skill\|generated skill must include.*Token Budget" src/engaku/templates/skills .github/skills src/engaku/templates/agents .github/agents src/engaku/templates/copilot-instructions.md .github/copilot-instructions.md`

- [x] 5. **Update docs and overview**
  - Files: `README.md`, `.ai/overview.md`
  - Steps:
    - Update README to describe token-budget behavior as an always-on instruction, not a bundled skill.
    - Keep Caveman attribution as inspiration, but state Engaku uses its own compact mode and does not copy upstream skill text.
    - Keep Serena setup documentation intact.
    - In `.ai/overview.md`, replace the v1.1.10 sentence with: `v1.1.10 makes compact token budgeting an always-on generated instruction, keeps Serena as default symbol-level navigation, and removes token-budget policy from conditional skills.`
  - Verify: `grep -n "always-on generated instruction\|compact token budgeting\|Serena" README.md .ai/overview.md && ! grep -n "bundled token-budget skill" README.md .ai/overview.md`

- [x] 6. **Run full verification**
  - Files: `src/engaku/templates/instructions/token-budget.instructions.md`, `.github/instructions/token-budget.instructions.md`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `src/engaku/templates/copilot-instructions.md`, `.github/copilot-instructions.md`, `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`, `src/engaku/templates/skills`, `.github/skills`, `tests/test_init.py`, `tests/test_update.py`, `README.md`, `.ai/overview.md`
  - Steps:
    - Run the full stdlib unittest suite.
    - Compare every live/template skill pair.
    - Compare the new live/template instruction pair.
    - Inspect the diff for unrelated edits.
  - Verify: `python -m unittest discover -s tests && for skill in brainstorming chrome-devtools context7 database doc-coauthoring frontend-design karpathy-guidelines mcp-builder proactive-initiative serena skill-authoring systematic-debugging verification-before-completion; do cmp "src/engaku/templates/skills/$skill/SKILL.md" ".github/skills/$skill/SKILL.md" || exit 1; done && cmp src/engaku/templates/instructions/token-budget.instructions.md .github/instructions/token-budget.instructions.md && git diff -- src/engaku/templates/instructions .github/instructions src/engaku/templates/skills .github/skills src/engaku/templates/copilot-instructions.md .github/copilot-instructions.md src/engaku/templates/agents .github/agents src/engaku/cmd_init.py src/engaku/cmd_update.py tests/test_init.py tests/test_update.py README.md .ai/overview.md`

## Out of Scope

- Removing or redesigning Serena setup, Serena MCP config, or `serena/*` tool assignments.
- Copying upstream Caveman text verbatim.
- Adding token accounting, billing telemetry, or model auto-selection.
- Installing upstream Caveman automatically.
- Rewriting unrelated skill workflows.