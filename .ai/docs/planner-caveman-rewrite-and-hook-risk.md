Related plan: `2026-04-30-planner-caveman-rewrite-audit`

# Problem

Three issues surfaced together:

1. `planner.agent.md` still contains `Not every conversation needs all three.`
2. The requested live/template instruction surfaces are not fully rewritten into the current Caveman-style compact form.
3. `hooks:` in custom-agent frontmatter looks incompatible with Copilot CLI, but the user chose not to expand this round into schema cleanup.

# Findings

## Confirmed repository state

- `.github/agents/planner.agent.md` and `src/engaku/templates/agents/planner.agent.md` both still include `Not every conversation needs all three.`
- `.github/copilot-instructions.md` already carries the global kernel: agent boundaries, lossless compactness, and generated-artifact style.
- `.github/instructions/agent-boundaries.instructions.md` and `.github/instructions/lessons.instructions.md` still exist as reinforcing path-specific files; matching templates also exist.
- `.ai/overview.md` already says global policy moved into `.github/copilot-instructions.md`, but it does not yet reflect the narrower cleanup requested here.

## External compatibility evidence

GitHub's `Custom agents configuration` reference states that the YAML frontmatter properties supported across GitHub.com, Copilot CLI, and supported IDEs are:

- `name`
- `description`
- `target`
- `tools`
- `model`
- `disable-model-invocation`
- `user-invocable`
- `infer` (retired)
- `mcp-servers`
- `metadata`

The same reference does not list `hooks:`. That is enough to treat current hook frontmatter as a compatibility risk. It is not enough, on its own, to decide the replacement mechanism, so this plan leaves that issue open.

# Options

| Option | What it changes | Pros | Cons |
| --- | --- | --- | --- |
| A. Planner-only cleanup | Only rewrite planner live/template and remove the stale sentence | Smallest diff | Leaves requested instruction drift untouched |
| B. Targeted rewrite + deferred hooks | Rewrite planner + `copilot-instructions` + `lessons` + `agent-boundaries` + `overview`; record `hooks:` as risk only | Matches the user's chosen scope; keeps work reviewable | Leaves issue 3 unresolved |
| C. Full agent schema cleanup now | Rewrite all agents and remove or redesign `hooks:` immediately | Most complete compatibility pass | Reopens broader architecture and exceeds requested scope |

Recommended and chosen: **Option B**.

# File Map

## Files to modify in implementation

- `.github/agents/planner.agent.md`
- `src/engaku/templates/agents/planner.agent.md`
- `.github/copilot-instructions.md`
- `src/engaku/templates/copilot-instructions.md`
- `.github/instructions/lessons.instructions.md`
- `src/engaku/templates/instructions/lessons.instructions.md`
- `.github/instructions/agent-boundaries.instructions.md`
- `src/engaku/templates/instructions/agent-boundaries.instructions.md`
- `.ai/overview.md`

## Files created by planning

- `.ai/tasks/2026-04-30-planner-caveman-rewrite-audit.md`
- `.ai/decisions/014-targeted-caveman-rewrite-defer-hook-cleanup.md`
- `.ai/docs/planner-caveman-rewrite-and-hook-risk.md`

# Rewrite targets

## Planner prompt

- Remove `Not every conversation needs all three.`
- Keep the body role-specific.
- Keep ownership boundaries and `.ai/overview.md` restriction explicit.
- Shorten wording around questioning, alternatives, and staged drafting.

## Copilot instructions

- Keep this as the single universal policy surface.
- Tighten wording; do not duplicate agent-specific workflow.
- Preserve the kernel sections already in place.

## Agent boundaries / lessons

- Keep them as reinforcement files, not competing sources of truth.
- Compress repeated rationale.
- Preserve exact operational rules.

## Overview

Append one short sentence that reflects this cleanup and explicitly says `hooks:` compatibility remains a separate issue.

# Deferred issue

`hooks:` remains open. A follow-up plan should answer three questions before implementation:

1. Remove `hooks:` entirely from generated agent frontmatter?
2. Move hook behavior to a different configuration surface?
3. Keep a compatibility split between VS Code-specific generation and stricter Copilot CLI generation?
