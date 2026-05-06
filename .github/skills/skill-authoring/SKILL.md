---
name: skill-authoring
description: "Turn a repeated multi-step workflow into a reusable Copilot skill. Use when the same method, with the same phases and safeguards, is being re-explained across sessions and the workflow is genuinely reusable rather than a one-off prompt."
context: fork
argument-hint: "Describe the workflow you keep repeating: trigger, inputs, steps, outputs, and stopping rules."
user-invocable: true
disable-model-invocation: false
---

# Skill Authoring

Capture a repeated multi-step method as a Copilot **skill**. Run when you've explained the same phases, safeguards, and output format more than twice.

---

## 1. Primitive Selection Gate

Pick the **smallest** customization that fits.

| Primitive          | Fits when                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------ |
| Instruction file   | A persistent rule or fact that should always apply to a path or scope.                     |
| Prompt file        | A single fixed command or template the user invokes verbatim with small variable inputs.   |
| **Skill**          | A reusable multi-step **method** where later steps adapt to earlier findings.              |
| Custom agent       | A distinct persona with its own tool restrictions, model, or handoff protocol.             |

One fixed prompt with placeholders → prompt file. Needs separate role / tool allow-list / handoffs → custom agent. Otherwise continue.

---

## 2. Prompt File vs Skill Boundary

- **Prompt file** = single fixed command template. Small variable inputs. One artefact. No conditional branching between phases.
- **Skill** = multi-step method where step N reads state from step N-1. Phases fixed; per-run content differs.

Intermediate state influencing later steps → skill. One-shot variable substitution → prompt.

---

## 3. Interview Checklist

Before writing SKILL.md:

- **Trigger** — what request/situation activates it?
- **Non-triggers** — what looks similar but should NOT activate it?
- **Inputs** — user-provided vs. agent-gathered.
- **Phases** — ordered steps (purpose, action, output, exit criterion).
- **Safeguards** — what to verify before each phase advances.
- **Output format** — artefact and its location.
- **Stopping rules** — when does it end? when escalate?
- **Failure handling** — what to do if a phase can't complete cleanly.

---

## 4. Ownership Boundary

Skills authored here are **user-owned** — live in the user's workspace (`.github/skills/<name>/SKILL.md`) or personal Copilot profile.

- Do **not** add to Engaku's bundled template inventory.
- Do **not** register in `_SKILLS`, `cmd_init.py`, or `cmd_update.py`.
- Engaku-managed skills only ship via an explicit planner task.

Upstreaming into Engaku requires a separate task plan; this skill does not promote automatically.

---

## 5. Generated Skill Usage Model

A skill stores the **method**, not per-run inputs. The user still provides the subject (which database, feature, module) each run. The skill removes the need to restate phase sequence, safeguards, output format/location, stopping/escalation rules.

For workflows spanning sessions or needing durable intermediate state → write to user-owned `.ai/docs/<name>.md` or `.ai/tasks/<name>.md`. Don't encode run state inside the skill itself.

---

## 6. SKILL.md Drafting Rules

VS Code skill constraints — must follow exactly:

- Filename is always `SKILL.md`. Parent directory name is the skill name.
- Skill name is **lowercase, hyphenated**, matches the parent directory.
- Frontmatter `description` says **what** the skill does **and when** to use it.
- `argument-hint` describes what the user passes, in plain English.
- `user-invocable: true` allows manual invocation; `disable-model-invocation: false` allows automatic invocation when description matches.
- Referenced resources (scripts, examples, sub-docs) use **relative** links inside the skill folder so the skill stays portable.

Body structure suggestion:

1. One-paragraph purpose and trigger.
2. Numbered phases, each with action and exit criterion.
3. Safeguards / boundary section if the skill can be misapplied.
4. Output format and location.
5. Escalation note pointing to a larger primitive when the situation outgrows the skill.

---

## 7. Validation Checklist

- [ ] Parent directory name = frontmatter `name`.
- [ ] Description specific, includes a "use when" clause.
- [ ] Phases ordered, each with clear exit criterion.
- [ ] Safeguards and stopping rules explicit.
- [ ] Output format and location stated.
- [ ] No instruction relies on memory from a previous run.
- [ ] All referenced files use relative paths.
- [ ] No third-party tools required unless explicitly listed.

---

## 8. Test Loop

1. Re-read SKILL.md as if you'd never seen the workflow.
2. Walk one realistic case end-to-end against the written phases.
3. Note any improvised step → missing instruction.
4. Patch and repeat until a cold read produces the right run.

---

## 9. Escalation to Custom Agent

Convert the skill into a custom agent only when one of these is true:

- The workflow needs its own model assignment or tool allow-list.
- It must hand off to / be invoked by other agents under a fixed protocol.
- It owns artefacts that other agents must not touch.

Otherwise keep it as a skill — cheaper to maintain, easier to compose with other primitives.
