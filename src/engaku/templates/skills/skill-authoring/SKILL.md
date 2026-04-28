---
name: skill-authoring
description: "Turn a repeated multi-step workflow into a reusable Copilot skill. Use when the same method, with the same phases and safeguards, is being re-explained across sessions and the workflow is genuinely reusable rather than a one-off prompt."
argument-hint: "Describe the workflow you keep repeating: trigger, inputs, steps, outputs, and stopping rules."
user-invocable: true
disable-model-invocation: false
---

# Skill Authoring

A workflow for capturing a repeated multi-step method as a Copilot **skill**.
Run this when you notice you are explaining the same phases, safeguards, and
output format more than twice.

---

## 1. Primitive Selection Gate

Before drafting a skill, confirm a skill is the right primitive. Pick the
**smallest** customization that fits.

| Primitive          | Fits when                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------ |
| Instruction file   | A persistent rule or fact that should always apply to a path or scope.                     |
| Prompt file        | A single fixed command or template the user invokes verbatim with small variable inputs.   |
| **Skill**          | A reusable multi-step **method** where later steps adapt to earlier findings.              |
| Custom agent       | A distinct persona with its own tool restrictions, model, or handoff protocol.             |

If the workflow is one fixed prompt with a placeholder, prefer a prompt file.
If it needs a separate role, tool allow-list, or handoffs, escalate to a
custom agent. Only proceed below when a skill is the right answer.

---

## 2. Prompt File vs Skill Boundary

- **Prompt file** = a single fixed command template. Inputs are small variables
  inserted into one fixed instruction. Output is one artefact. No conditional
  branching between phases.
- **Skill** = a reusable multi-step method where later steps depend on what
  earlier steps found. Example: read selected database tables, use those
  findings to identify affected code modules, then produce a per-module
  modification plan. The phases are fixed but each run's content is different
  because step N reads state from step N-1.

If the procedure has intermediate state that influences later steps, it is a
skill. If it is one shot with variable substitution, it is a prompt file.

---

## 3. Interview Checklist

Collect these before writing the SKILL.md. Ask the user when missing.

- **Trigger**: what user request or situation should activate this skill?
- **Non-triggers**: what looks similar but should NOT activate it?
- **Inputs**: what does the user provide each run? what does the agent gather?
- **Phases**: ordered steps. For each: purpose, action, output, exit criterion.
- **Safeguards**: what must the agent verify before each phase advances?
- **Output format**: what artefact is produced? where does it land?
- **Stopping rules**: when does the skill end? when should it escalate?
- **Failure handling**: what to do if a phase cannot complete cleanly?

---

## 4. Ownership Boundary

Skills authored with this workflow are **user-owned**. They live in the user's
workspace (`.github/skills/<name>/SKILL.md`) or personal Copilot profile.

- Do **not** add user-authored skills to Engaku's bundled template inventory.
- Do **not** register them in `_SKILLS`, `cmd_init.py`, or `cmd_update.py`.
- Engaku-managed skills are only those explicitly shipped as part of Engaku
  via a planner task that says so.

If the user later decides to upstream a skill into Engaku, that requires a
separate task plan; this skill does not perform that promotion automatically.

---

## 5. Generated Skill Usage Model

A skill stores the **method**, not the per-run inputs. Each run, the user still
provides the task-specific subject (which database, which feature, which
module). What the skill removes is the need to restate:

- the phase sequence
- the safeguards between phases
- the output format and location
- the stopping and escalation rules

For workflows that span multiple sessions or need durable intermediate state,
write that state to user-owned `.ai/docs/<name>.md` or `.ai/tasks/<name>.md`
files; do not try to encode run state inside the skill itself.

---

## 6. SKILL.md Drafting Rules

VS Code skill constraints — must follow exactly:

- Filename is always `SKILL.md`. Parent directory name is the skill name.
- Skill name is **lowercase, hyphenated**, and matches the parent directory.
- Frontmatter `description` says **what** the skill does **and when** to use it.
- `argument-hint` describes what the user should pass in plain English.
- `user-invocable: true` allows manual invocation; `disable-model-invocation:
  false` allows automatic invocation when the description matches.
- Any referenced resources (scripts, examples, sub-docs) must use **relative**
  links inside the skill folder so the skill stays portable.

Body structure suggestion:

1. One-paragraph purpose and trigger.
2. Numbered phases, each with action and exit criterion.
3. Safeguards or boundary section if the skill can be misapplied.
4. Output format and location.
5. Escalation note pointing to a larger primitive if the situation outgrows
   the skill.

---

## 7. Validation Checklist

Before declaring the skill ready, confirm every item:

- [ ] Parent directory name equals frontmatter `name`.
- [ ] Description is specific and includes a "use when" clause.
- [ ] Phases are ordered, each has a clear exit criterion.
- [ ] Safeguards and stopping rules are explicit.
- [ ] Output format and location are stated.
- [ ] No instruction relies on memory from a previous run.
- [ ] All referenced files use relative paths.
- [ ] No third-party tools required unless explicitly listed.

---

## 8. Test Loop

1. Re-read the SKILL.md as if you had never seen the workflow before.
2. Walk through one realistic case end-to-end against the written phases.
3. Note any step you had to improvise — that is a missing instruction.
4. Patch the SKILL.md and repeat until a cold read produces the right run.

---

## 9. Escalation to Custom Agent

Convert the skill into a custom agent only when one of these is true:

- The workflow needs its own model assignment or tool allow-list.
- It must hand off to or be invoked by other agents under a fixed protocol.
- It owns artefacts that other agents must not touch.

Otherwise keep it as a skill — skills are cheaper to maintain and easier to
combine with other primitives.
