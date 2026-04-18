# Skill Creator Agent — Design Reference

> Status: Deferred — not yet planned or scheduled.
> Reference: conversation on 2026-04-18.

## Background

Anthropic ships a `skill-creator` skill for Claude Code that helps users turn
repeatable workflows into SKILL.md files through an interview → draft → test →
refine loop. We explored whether engaku should have an equivalent, and whether
it should be implemented as a skill or an agent.

Reference: https://github.com/anthropics/skills/tree/main/skills/skill-creator

---

## Decision: Agent, not Skill

**Reasons:**

- Tool requirements don't fit any existing agent. The workflow needs `web`
  (research best practices), `edit` (write SKILL.md), `agent` (dispatch
  subagents for testing), plus `read`/`search`. No existing agent has this
  combination.
- Directory ownership follows the existing pattern:
  - `planner` → `.ai/tasks/`, `.ai/decisions/`, `.ai/docs/`
  - `scanner` → `.github/instructions/`
  - `reviewer` → task `status:` field
  - **`skill-creator`** → `.github/skills/`
- Creating a skill is a standalone work mode (interview → draft → test →
  refine), not something done while executing another task. An agent models
  this better than an embedded skill.
- VS Code subagents (experimental) allow parallel test execution, which
  partially replaces Claude Code's eval infrastructure.

---

## Architecture

### Main agent: `skill-creator.agent.md`

```yaml
---
name: skill-creator
description: >-
  Workflow-to-skill agent. Interviews the user to capture a repeatable
  workflow, then writes a .github/skills/ SKILL.md file, and tests it
  via subagents. Use when the user wants to turn a process, checklist,
  or methodology into a reusable Copilot skill.
user-invocable: true
tools: ['agent', 'read', 'search', 'edit', 'web']
agents: ['dev', 'skill-tester']
handoffs:
  - label: "Use the new skill in dev"
    agent: dev
    prompt: "Try using the newly created skill."
    send: false
---
```

### Subagent: `skill-tester.agent.md`

A lightweight test runner that executes a task prompt as if it were a developer
using the target skill. Only skill-creator should be able to invoke it.

```yaml
---
name: skill-tester
user-invocable: false
disable-model-invocation: true
tools: ['read', 'search', 'execute']
model: ['Claude Haiku 4.5 (copilot)', 'Gemini 3 Flash (Preview) (copilot)']
---
```

---

## Workflow

```
User → @skill-creator "turn my code review process into a skill"

  Phase 1 — Interview (skill-creator itself)
    Ask: what does this skill do? when should it trigger?
    what's the expected output? any edge cases?
    Extract answers from conversation history first if available.

  Phase 2 — Draft (skill-creator itself)
    Write .github/skills/{name}/SKILL.md following VS Code conventions.
    Also write to src/engaku/templates/skills/{name}/SKILL.md (template copy).

  Phase 3 — Test (via subagents)
    Spawn 2–3 skill-tester subagents in parallel:
      - subagent A: test prompt 1, loads new skill
      - subagent B: test prompt 2, loads new skill
      - subagent C: test prompt 1 or 2, no skill (baseline)
    Recommend keeping test cases to 2–3 to manage cost.

  Phase 4 — Evaluate (skill-creator itself)
    Compare subagent outputs qualitatively.
    Present with/without comparison inline in chat.
    Ask user for feedback.

  Phase 5 — Refine (loop back to Phase 2 if needed)
    Update SKILL.md based on feedback.
    Rerun affected test cases.

  Done → handoff to @dev
```

---

## SKILL.md Writing Guidelines

Distilled from Anthropic's skill-creator:

1. **Frontmatter** — required fields: `name`, `description`. Optional but
   useful: `argument-hint`, `user-invocable`, `disable-model-invocation`.

2. **Description is the trigger** — it must be specific enough that the model
   knows when to activate the skill. Too vague = undertriggering. Make it
   slightly "pushy": include the domains, workflows, and phrasings that should
   trigger it.

3. **Progressive disclosure** — keep SKILL.md under 500 lines. Move reference
   material to `references/` subdirectory and point to it from the body.

4. **Explain the why** — prefer explaining reasoning over issuing directives.
   Avoid `ALWAYS` / `NEVER` in all caps; if you find yourself writing them,
   reframe as rationale.

5. **Bundled resources** structure:
   ```
   skills/{name}/
   ├── SKILL.md          (required)
   ├── references/       (long docs, loaded on demand)
   └── assets/           (templates, icons, etc.)
   ```

6. **Test with realistic prompts** — 2–3 prompts that a real user would type,
   not abstract descriptions of the skill.

---

## Capability Gap vs Claude's Skill-Creator

| Feature | Claude | VS Code agent + subagents | Gap |
|---|---|---|---|
| Interview + draft | ✅ | ✅ | None |
| Parallel subagent tests | ✅ | ✅ (experimental) | None |
| Qualitative comparison | ✅ HTML viewer | ⚠️ inline chat only | Minor |
| Quantitative benchmark | ✅ numeric aggregation | ❌ | Medium; low priority |
| Description optimization loop | ✅ `claude -p` CLI | ❌ | Not portable to VS Code |
| .skill packaging | ✅ | ❌ / not needed | N/A — VS Code uses directories |

We cover ~80% of the core value.

---

## Risks and Constraints

- **Subagents are experimental** — requires `chat.subagents.allowInvocationsFromSubagents`
  setting and VS Code ≥ the version that shipped this feature. Note this in
  the agent body and make Phase 3 optional if subagents are unavailable.
- **Baseline isolation** — subagents share the filesystem, so a "no-skill"
  baseline subagent can still technically read `.github/skills/`. True
  isolation isn't possible; document this limitation.
- **Cost** — each test round uses 3+ subagent turns. Keep test cases tight.
- **Template sync** — same rule as other agents: edit both
  `src/engaku/templates/agents/` and `.github/agents/` in one operation.

---

## Files to Create When Implemented

| File | Purpose |
|---|---|
| `src/engaku/templates/agents/skill-creator.agent.md` | Template copy |
| `.github/agents/skill-creator.agent.md` | Live copy |
| `src/engaku/templates/agents/skill-tester.agent.md` | Template copy |
| `.github/agents/skill-tester.agent.md` | Live copy |
| `.ai/decisions/004-skill-creator-agent.md` | ADR recording the agent-vs-skill decision |

The agent body should be ~150 lines covering the five phases above.
