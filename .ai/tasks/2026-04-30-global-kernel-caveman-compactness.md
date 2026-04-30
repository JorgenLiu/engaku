---
plan_id: 2026-04-30-global-kernel-caveman-compactness
title: Move global kernel and lossless compactness into Copilot instructions
status: done
created: 2026-04-30
---

## Background
Engaku currently generates `token-budget.instructions.md` as an always-on `.instructions.md` file, but recent session analysis showed this is not strong enough to shape commentary, review, and generated prompt/doc output. VS Code 1.118 improves token efficiency through caching, tool search, dedicated skill context, and agentic search/execution, but these platform features reduce input/tool cost rather than enforcing concise agent speech. Caveman's useful lesson is not the meme voice or skill packaging; it is an always-on, lossless compactness protocol that preserves technical substance while removing ceremony.

## Design
Move Engaku's universal policy into `.github/copilot-instructions.md` because it is the clearest global, unconditional customization surface for Copilot. Use Engaku-authored Caveman-inspired rules, not copied Caveman skill text: lossless compactness, no arbitrary final-answer cap, no `Now let me...` progress filler, complete evidence when meaningful, and compact generated artifacts. Keep agent files focused on role workflows; keep `.github/instructions/*.instructions.md` for path/file-specific rules; keep hooks for dynamic state injection only.

This supersedes `.ai/decisions/011-token-budget-as-always-on-instruction.md`; `.ai/decisions/013-global-kernel-in-copilot-instructions.md` records the new accepted decision. The implementation must also rewrite Engaku-authored generated artifacts using the same lossless compactness principles: agents, instruction stubs, and skills should become shorter without dropping workflow requirements, exact commands, paths, verification rules, safety warnings, or acceptance criteria.

## File Map
- Create: `.ai/decisions/013-global-kernel-in-copilot-instructions.md`
- Modify: `.ai/decisions/011-token-budget-as-always-on-instruction.md`
- Modify: `.github/copilot-instructions.md`
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `.github/agents/coder.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `.github/agents/scanner.agent.md`
- Modify: `src/engaku/templates/agents/coder.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `src/engaku/templates/agents/scanner.agent.md`
- Modify: `.github/instructions/agent-boundaries.instructions.md`
- Modify: `.github/instructions/hooks.instructions.md`
- Modify: `.github/instructions/lessons.instructions.md`
- Modify: `.github/instructions/templates.instructions.md`
- Modify: `.github/instructions/tests.instructions.md`
- Modify: `src/engaku/templates/instructions/agent-boundaries.instructions.md`
- Modify: `src/engaku/templates/instructions/lessons.instructions.md`
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
- Delete: `.github/instructions/token-budget.instructions.md`
- Delete: `src/engaku/templates/instructions/token-budget.instructions.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Record global-kernel decision**
  - Files: `.ai/decisions/013-global-kernel-in-copilot-instructions.md`, `.ai/decisions/011-token-budget-as-always-on-instruction.md`
  - Steps:
    - Verify decision 013 exists with `status: accepted`, related task `2026-04-30-global-kernel-caveman-compactness`, and rationale for moving global policy to `copilot-instructions.md`.
    - Verify decision 011 frontmatter is `status: superseded`.
    - Keep text concise; mention Caveman as inspiration and MIT upstream, but do not copy Caveman's skill body.
  - Verify: `test -f .ai/decisions/013-global-kernel-in-copilot-instructions.md && rg -n "status: superseded|status: accepted|copilot-instructions|Caveman" .ai/decisions/011-token-budget-as-always-on-instruction.md .ai/decisions/013-global-kernel-in-copilot-instructions.md`

- [x] 2. **Add global kernel to live Copilot instructions**
  - Files: `.github/copilot-instructions.md`
  - Steps:
    - Replace the top comment with wording that says this file owns global Engaku policy; path-specific conventions remain in `.github/instructions/*.instructions.md`.
    - Add an `Engaku Global Kernel` section near the top containing compact agent boundaries for coder, planner, reviewer, and scanner.
    - Add `Lossless Compactness` rules: compact by default, preserve complete meaningful output, remove ceremony, no arbitrary final-answer caps, no `Now let me...` progress text, preserve exact technical evidence.
    - Add `Generated Artifact Style` rules so future docs, prompts, skills, agents, and instructions use Caveman-inspired concision: every sentence must carry function; use checklists/tables where clearer; preserve commands, paths, schemas, acceptance criteria, and risks.
  - Verify: `rg -n "Engaku Global Kernel|Lossless Compactness|Generated Artifact Style|No arbitrary|Now let me" .github/copilot-instructions.md`

- [x] 3. **Mirror global kernel in template**
  - Files: `src/engaku/templates/copilot-instructions.md`
  - Steps:
    - Apply the same global-kernel, lossless-compactness, and generated-artifact-style sections to the generated template.
    - Keep template text compatible with all initialized repos; do not include this repo's release-only rules unless already template-appropriate.
    - Preserve global Engaku constraints currently in the template.
  - Verify: `rg -n "Engaku Global Kernel|Lossless Compactness|Generated Artifact Style|No arbitrary|Now let me" src/engaku/templates/copilot-instructions.md`

- [x] 4. **Rewrite agent prompts compactly**
  - Files: `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`, `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `src/engaku/templates/agents/scanner.agent.md`
  - Steps:
    - Rewrite each agent body using lossless compactness: remove repeated rationale, throat-clearing, and long prose while preserving ownership boundaries, hooks, handoffs, verification rules, and user-facing workflow requirements.
    - Keep frontmatter tools/hooks/model fields valid and unchanged unless needed for schema correctness.
    - Ensure live and template versions stay paired for all generated agents.
  - Verify: `python -m unittest tests.test_init tests.test_update tests.test_apply && rg -n "You own:|You do NOT:|Verify|handoffs|hooks" .github/agents src/engaku/templates/agents`

- [x] 5. **Rewrite instruction stubs compactly**
  - Files: `.github/instructions/agent-boundaries.instructions.md`, `.github/instructions/hooks.instructions.md`, `.github/instructions/lessons.instructions.md`, `.github/instructions/templates.instructions.md`, `.github/instructions/tests.instructions.md`, `src/engaku/templates/instructions/agent-boundaries.instructions.md`, `src/engaku/templates/instructions/lessons.instructions.md`
  - Steps:
    - Rewrite live repo instructions with Caveman-inspired concision while preserving exact `applyTo` frontmatter, ownership rules, hook constraints, template-sync rules, test conventions, and lesson-memory behavior.
    - Rewrite generated instruction templates with the same compact style where template versions exist.
    - Do not add project-specific hook/test/template rules to generated templates unless they already belong there.
  - Verify: `rg -n "applyTo|coder|planner|reviewer|scanner|Lessons|templates|unittest" .github/instructions src/engaku/templates/instructions && ! rg -n "token-budget.instructions.md" .github/instructions src/engaku/templates/instructions`

- [x] 6. **Rewrite bundled skills compactly**
  - Files: `.github/skills/brainstorming/SKILL.md`, `.github/skills/chrome-devtools/SKILL.md`, `.github/skills/context7/SKILL.md`, `.github/skills/database/SKILL.md`, `.github/skills/doc-coauthoring/SKILL.md`, `.github/skills/frontend-design/SKILL.md`, `.github/skills/karpathy-guidelines/SKILL.md`, `.github/skills/mcp-builder/SKILL.md`, `.github/skills/proactive-initiative/SKILL.md`, `.github/skills/serena/SKILL.md`, `.github/skills/skill-authoring/SKILL.md`, `.github/skills/systematic-debugging/SKILL.md`, `.github/skills/verification-before-completion/SKILL.md`, `src/engaku/templates/skills/brainstorming/SKILL.md`, `src/engaku/templates/skills/chrome-devtools/SKILL.md`, `src/engaku/templates/skills/context7/SKILL.md`, `src/engaku/templates/skills/database/SKILL.md`, `src/engaku/templates/skills/doc-coauthoring/SKILL.md`, `src/engaku/templates/skills/frontend-design/SKILL.md`, `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`, `src/engaku/templates/skills/mcp-builder/SKILL.md`, `src/engaku/templates/skills/proactive-initiative/SKILL.md`, `src/engaku/templates/skills/serena/SKILL.md`, `src/engaku/templates/skills/skill-authoring/SKILL.md`, `src/engaku/templates/skills/systematic-debugging/SKILL.md`, `src/engaku/templates/skills/verification-before-completion/SKILL.md`
  - Steps:
    - Rewrite each live skill and matching template skill to remove filler and repeated meta-instructions while preserving trigger criteria, required workflow phases, safety gates, exact commands, docs/tool usage rules, and verification requirements.
    - Keep YAML frontmatter valid and skill names/descriptions accurate.
    - Keep domain-specific detail; do not compress away constraints needed for safe execution.
  - Verify: `python -m unittest tests.test_init tests.test_update && rg -n "^---|^name:|^description:" .github/skills src/engaku/templates/skills`

- [x] 7. **Remove token-budget instruction generation**
  - Files: `.github/instructions/token-budget.instructions.md`, `src/engaku/templates/instructions/token-budget.instructions.md`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`
  - Steps:
    - Delete live and template `token-budget.instructions.md`.
    - Remove `token-budget.instructions.md` from init/update generated instruction lists.
    - Update `cmd_init.py` module docstring so generated files no longer list token-budget instruction.
  - Verify: `! test -e .github/instructions/token-budget.instructions.md && ! test -e src/engaku/templates/instructions/token-budget.instructions.md && ! rg -n "token-budget.instructions.md" src/engaku/cmd_init.py src/engaku/cmd_update.py`

- [x] 8. **Update init tests**
  - Files: `tests/test_init.py`
  - Steps:
    - Remove expected-file assertions for `.github/instructions/token-budget.instructions.md`.
    - Remove tests that expect token-budget instruction creation or preservation.
    - Add assertions that generated `.github/copilot-instructions.md` contains `Engaku Global Kernel`, `Lossless Compactness`, and `Generated Artifact Style`.
    - Keep `token-budget` skill absence tests only if they remain useful as regression coverage.
  - Verify: `python -m unittest tests.test_init && ! rg -n "token-budget.instructions.md|Compact mode" tests/test_init.py`

- [x] 9. **Update update tests**
  - Files: `tests/test_update.py`
  - Steps:
    - Remove tests that expect `engaku update` to create or preserve token-budget instruction files.
    - Add assertions that `token-budget` is not part of `_SKILLS` and that `engaku update` does not create `.github/instructions/token-budget.instructions.md`.
    - Preserve tests for lessons and agent-boundaries unless a later plan removes those files.
  - Verify: `python -m unittest tests.test_update && ! rg -n "creates_token_budget|preserves_token_budget|token-budget.instructions.md" tests/test_update.py`

- [x] 10. **Refresh user docs and changelog**
  - Files: `README.md`, `CHANGELOG.md`
  - Steps:
    - Update README token-budget section to describe global kernel in `.github/copilot-instructions.md`, not `token-budget.instructions.md`.
    - Explain Caveman relationship: Engaku uses Caveman-inspired lossless compactness, does not install or copy Caveman by default, and users may install Caveman separately for commands/compress workflows.
    - Add CHANGELOG entry for moving global token/boundary policy into Copilot instructions and retiring generated token-budget instruction.
  - Verify: `rg -n "copilot-instructions.md|Lossless Compactness|Caveman|token-budget" README.md CHANGELOG.md && ! rg -n "token-budget.instructions.md" README.md CHANGELOG.md`

- [x] 11. **Update project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - Replace the overview sentence claiming token budgeting is an always-on generated instruction with: `v1.1.11 moves global Engaku policy into .github/copilot-instructions.md: agent boundaries, Caveman-inspired lossless compactness, and generated-artifact style live in one unconditional kernel, while .github/instructions/ remains path-specific and hooks inject dynamic state only.`
    - Remove `token-budget.instructions.md` from the directory structure line for generated instructions.
  - Verify: `rg -n "v1.1.11 moves global Engaku policy|hooks inject dynamic state only" .ai/overview.md && ! rg -n "token-budget.instructions.md|always-on generated instruction" .ai/overview.md`

- [x] 12. **Run full verification**
  - Files: `.github/copilot-instructions.md`, `src/engaku/templates/copilot-instructions.md`, `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`, `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `.github/instructions/agent-boundaries.instructions.md`, `.github/instructions/hooks.instructions.md`, `.github/instructions/lessons.instructions.md`, `.github/instructions/templates.instructions.md`, `.github/instructions/tests.instructions.md`, `src/engaku/templates/instructions/agent-boundaries.instructions.md`, `src/engaku/templates/instructions/lessons.instructions.md`, `.github/skills/brainstorming/SKILL.md`, `.github/skills/chrome-devtools/SKILL.md`, `.github/skills/context7/SKILL.md`, `.github/skills/database/SKILL.md`, `.github/skills/doc-coauthoring/SKILL.md`, `.github/skills/frontend-design/SKILL.md`, `.github/skills/karpathy-guidelines/SKILL.md`, `.github/skills/mcp-builder/SKILL.md`, `.github/skills/proactive-initiative/SKILL.md`, `.github/skills/serena/SKILL.md`, `.github/skills/skill-authoring/SKILL.md`, `.github/skills/systematic-debugging/SKILL.md`, `.github/skills/verification-before-completion/SKILL.md`, `src/engaku/templates/skills/brainstorming/SKILL.md`, `src/engaku/templates/skills/chrome-devtools/SKILL.md`, `src/engaku/templates/skills/context7/SKILL.md`, `src/engaku/templates/skills/database/SKILL.md`, `src/engaku/templates/skills/doc-coauthoring/SKILL.md`, `src/engaku/templates/skills/frontend-design/SKILL.md`, `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`, `src/engaku/templates/skills/mcp-builder/SKILL.md`, `src/engaku/templates/skills/proactive-initiative/SKILL.md`, `src/engaku/templates/skills/serena/SKILL.md`, `src/engaku/templates/skills/skill-authoring/SKILL.md`, `src/engaku/templates/skills/systematic-debugging/SKILL.md`, `src/engaku/templates/skills/verification-before-completion/SKILL.md`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `tests/test_init.py`, `tests/test_update.py`, `README.md`, `CHANGELOG.md`, `.ai/overview.md`
  - Steps:
    - Run focused init/update tests.
    - Run full unittest suite.
    - Search for stale token-budget instruction references in current source, templates, tests, README, CHANGELOG, and overview.
    - Inspect diff for accidental source/template/doc drift outside the file map.
  - Verify: `python -m unittest tests.test_init tests.test_update && python -m unittest discover -s tests && ! rg -n "token-budget.instructions.md|Compact mode is \*\*on by default\*\*" src tests README.md CHANGELOG.md .ai/overview.md .github/copilot-instructions.md .github/instructions && git diff --stat`

## Out of Scope
- Copying Caveman's full skill body into Engaku agent prompts.
- Installing Caveman by default or adding Caveman as an Engaku dependency.
- Removing `agent-boundaries.instructions.md`; this plan moves a compact boundary source of truth into `copilot-instructions.md` but leaves compatibility reinforcement for a later decision.
- Changing hook payload structure beyond documentation that hooks should inject dynamic state only.