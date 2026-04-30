---
plan_id: 2026-04-30-planner-caveman-rewrite-audit
title: Tighten planner prompt and selected instruction surfaces for Caveman compactness
status: done
created: 2026-04-30
---

## Background
The planner agent still contains the stale line `Not every conversation needs all three.`, which no longer fits the current artifact flow. The global kernel already moved into `.github/copilot-instructions.md`, but the planner prompt and the requested instruction surfaces have not been fully rewritten into the same tighter Caveman-style shape. GitHub's custom agent configuration reference also does not list `hooks:` as a supported frontmatter property for GitHub.com, Copilot CLI, and supported IDEs, but this plan records that as a follow-up risk instead of changing schema now.

## Design
Scope is intentionally narrow: rewrite only the planner live/template, `copilot-instructions` live/template, `lessons.instructions` live/template, `agent-boundaries.instructions` live/template, and `.ai/overview.md`. The rewrite should remove stale boilerplate, shorten repeated wording, and keep one clear split: global policy in `copilot-instructions`, path-specific rules in `.github/instructions/`, role workflow in the planner prompt. Do not change `hooks:` frontmatter in this pass; the compatibility question stays documented in `.ai/docs/planner-caveman-rewrite-and-hook-risk.md` and `.ai/decisions/014-targeted-caveman-rewrite-defer-hook-cleanup.md`.

## File Map
- Modify: `.github/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `.github/copilot-instructions.md`
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `.github/instructions/lessons.instructions.md`
- Modify: `src/engaku/templates/instructions/lessons.instructions.md`
- Modify: `.github/instructions/agent-boundaries.instructions.md`
- Modify: `src/engaku/templates/instructions/agent-boundaries.instructions.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Rewrite live planner prompt**
  - Files: `.github/agents/planner.agent.md`
  - Steps:
    - Remove the stale line `Not every conversation needs all three.`
    - Tighten the body around context gathering, clarification, option comparison, incremental design, and artifact production.
    - Keep ownership limits, terminal-observation-only guidance, and the `.ai/overview.md` restriction explicit.
  - Verify: `rg -n "Not every conversation needs all three|Owns:|Does NOT:|How you work" .github/agents/planner.agent.md`

- [x] 2. **Mirror the planner rewrite into the template**
  - Files: `src/engaku/templates/agents/planner.agent.md`
  - Steps:
    - Apply the same wording changes to the generated planner template.
    - Keep template-only frontmatter differences intact while matching the live body structure.
    - Confirm the live and template planner bodies stay aligned after the rewrite.
  - Verify: `diff -u <(sed -n '19,140p' .github/agents/planner.agent.md) <(sed -n '18,139p' src/engaku/templates/agents/planner.agent.md) | cat`

- [x] 3. **Rewrite live global-policy files compactly**
  - Files: `.github/copilot-instructions.md`, `.github/instructions/lessons.instructions.md`, `.github/instructions/agent-boundaries.instructions.md`
  - Steps:
    - Tighten wording to Caveman-style compactness without changing rule intent.
    - Keep the split clear: universal policy in `copilot-instructions`, path-specific reinforcement in `.github/instructions/`.
    - Remove repeated rationale already stated elsewhere, but keep exact constraints and ownership rules.
  - Verify: `rg -n "Engaku Global Kernel|Agent Boundaries|Lessons|Lossless Compactness|Generated Artifact Style" .github/copilot-instructions.md .github/instructions/lessons.instructions.md .github/instructions/agent-boundaries.instructions.md`

- [x] 4. **Mirror the compact rewrite into templates**
  - Files: `src/engaku/templates/copilot-instructions.md`, `src/engaku/templates/instructions/lessons.instructions.md`, `src/engaku/templates/instructions/agent-boundaries.instructions.md`
  - Steps:
    - Apply the same compact wording to the matching templates.
    - Preserve template-safe wording and existing `applyTo` frontmatter.
    - Keep template and live content aligned where the files are meant to match.
  - Verify: `rg -n "Engaku Global Kernel|Agent Boundaries|Lessons|Lossless Compactness|Generated Artifact Style" src/engaku/templates/copilot-instructions.md src/engaku/templates/instructions/lessons.instructions.md src/engaku/templates/instructions/agent-boundaries.instructions.md`

- [x] 5. **Update project overview with exact new text**
  - Files: `.ai/overview.md`
  - Steps:
    - Append this exact sentence to the end of the Overview paragraph: `A follow-up cleanup rewrites the planner prompt plus the copilot-instructions, lessons, and agent-boundaries files around the same Caveman-inspired compactness rules: global policy stays in .github/copilot-instructions.md, path-specific guidance stays in .github/instructions/, and the planner prompt drops stale artifact boilerplate. Compatibility of custom-agent frontmatter hooks in Copilot CLI remains unresolved and is intentionally left to a separate plan.`
    - Do not add extra overview prose beyond this sentence unless required to keep the paragraph grammatical.
    - Leave directory structure unchanged unless the implementation actually changes generated paths.
  - Verify: `rg -n "A follow-up cleanup rewrites the planner prompt|Compatibility of custom-agent frontmatter hooks in Copilot CLI remains unresolved" .ai/overview.md`

- [x] 6. **Check scope before handoff**
  - Files: `.github/agents/planner.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `.github/copilot-instructions.md`, `src/engaku/templates/copilot-instructions.md`, `.github/instructions/lessons.instructions.md`, `src/engaku/templates/instructions/lessons.instructions.md`, `.github/instructions/agent-boundaries.instructions.md`, `src/engaku/templates/instructions/agent-boundaries.instructions.md`, `.ai/overview.md`
  - Steps:
    - Confirm no agent files other than planner changed in this pass.
    - Confirm this pass does not edit or remove any `hooks:` frontmatter.
    - Review the diff for accidental scope growth beyond the file map.
  - Verify: `git --no-pager diff --name-only -- .github/agents src/engaku/templates/agents .github/instructions src/engaku/templates/instructions .github/copilot-instructions.md src/engaku/templates/copilot-instructions.md .ai/overview.md | cat`

## Out of Scope
Changing `hooks:` frontmatter or any non-planner agent file.
Rewriting bundled skills or unrelated instruction files.
Changing generated file lists, hook command behavior, or agent schema handling in Python source.
