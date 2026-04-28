# Workflow-to-Skill Capability for v1.1.8

Related task: `2026-04-28-workflow-to-skill-v118`
Date: 2026-04-28

## Context

The deferred `skill-creator-agent-design.md` concluded that turning repeatable
workflows into skills should be handled by a dedicated `skill-creator` agent,
not by a skill. That conclusion was reasonable when the main expected value was
an interview, file authoring, and subagent-based evaluation loop with a distinct
tool profile and directory ownership.

The current user need is narrower: repeated working patterns should be easy to
capture as project skills. VS Code's current customization guidance also makes a
clear distinction: prompt files are for lightweight repeated tasks, agent skills
are for portable multi-step workflows, and custom agents are for persistent
personas with tool restrictions or handoffs.

A representative workflow is: ask planner to inspect selected database tables,
use those findings to inspect related code modules, then produce a module-by-
module modification plan. The repeated part is not a fixed instruction string;
it is an ordered procedure with changing inputs, intermediate discoveries, and a
structured output.

## Reassessment

The old conclusion should be softened, not discarded entirely.

A dedicated `skill-creator` agent is still the better long-term fit for a full
creation environment with isolated testing, benchmark comparisons, and explicit
ownership of `.github/skills/`. However, that is too large for a small 1.1.x
release because it adds at least two agents, subagent testing assumptions,
template registration, model config implications, and new agent-boundary text.

A bundled authoring skill gives most of the immediate value with much lower
surface area. It can teach the active implementation agent how to decide whether
a repeated workflow should become a prompt, instruction, skill, agent, hook, or
MCP integration; interview the user only when needed; draft a valid `SKILL.md`;
and verify the result against VS Code's skill-loading rules.

For the database-to-module-planning example, the default answer is **skill**, not
prompt file. It is multi-step, reusable across different tables/modules, and the
agent should adapt later steps based on earlier findings. A prompt file would be
better only if the workflow were a single manually invoked, mostly fixed prompt
with a few parameters and no reusable procedure beyond that prompt text.

## Recommendation

Ship a new unconditional bundled skill in v1.1.8:

- Name: `skill-authoring`
- Purpose: guide agents through converting repeated workflows into valid,
  reusable Copilot agent skills.
- Scope: authoring guidance only; no subagent eval harness, no new custom
  agent, no new hooks, and no automatic migration of existing workflows.
- Ownership boundary: Engaku manages only the bundled `skill-authoring` template
  and its registration. Skills produced by using `skill-authoring` are
  user-owned project or personal customizations; they must not be added to
  Engaku's bundled template inventory unless the explicit task is to ship a new
  Engaku-managed skill.

The skill should include:

1. A primitive-selection gate: prompt vs instructions vs skill vs custom agent
   vs hook vs MCP.
2. A short interview checklist: trigger phrases, expected output, tools,
   resources, risks, examples, and storage scope.
3. SKILL.md writing rules: valid lowercase hyphenated name, directory/name
   match, specific description, progressive disclosure, referenced resources,
   and frontmatter validation.
4. An ownership gate: decide whether the requested skill is user-owned or an
   Engaku-bundled release artifact. User-owned skills stay outside
   `src/engaku/templates/skills/`, `_SKILLS`, `cmd_init.py`, and `cmd_update.py`.
5. A usage model section: explain that generated skills do not remove the need
  for task-specific input; they remove the need to restate the reusable method,
  and durable run state belongs in user-owned `.ai/docs/` or `.ai/tasks/` when
  needed.
6. A test loop: inspect the generated file and do one realistic prompt dry run
   by reasoning through whether the skill would trigger. Run Engaku registration
   tests only when the explicit goal is to add a new bundled Engaku skill.
7. An escalation rule: if the workflow requires a persistent persona, restricted
   tools, handoffs, or isolated subagent evaluation, recommend a custom agent
   instead of forcing it into a skill.

## Prompt File vs Skill Boundary

Use a prompt file when the reusable asset is mainly a single command the user
intentionally invokes: a fixed request shape, a small number of variables, and a
direct expected output. Examples: "write a PR description from these commits" or
"generate a unit test skeleton for the selected function".

Use a skill when the reusable asset is a method: multiple ordered phases,
branching based on intermediate results, domain-specific checks, optional tools
or resources, and repeated judgment about what to inspect next. The
database-to-code planning example falls here because it has at least three
phases, each phase depends on the previous result, and the reusable value is the
procedure rather than one prompt.

Use a custom agent instead of either when the workflow needs a persistent role,
restricted tools, a specific model, handoffs, or subagent orchestration. A
read-only database planner with fixed MCP tools and no edit access might become a
custom agent; a reusable process for whichever agent is active remains a skill.

## How Generated Skills Are Used

A generated skill is not a background automation and not a durable state machine.
The user still needs to provide the current task inputs: which tables, which
business question, which repository area, or which output target. The skill's
job is to remove the need to re-explain the reusable procedure.

For a skill named `data-mining-n-code-digging`, normal usage should look like:

```text
/data-mining-n-code-digging
Goal: understand what must change for billing grace periods.
Tables: billing_accounts, invoices, payment_attempts.
Output: per-module modification plan only; do not edit code.
```

or by natural language if the description is specific enough to trigger it:

```text
Use data-mining-n-code-digging to inspect the billing tables, connect the
findings to the relevant code modules, and produce a module-by-module plan.
```

The difference from a prompt file is what the user no longer writes. The user no
longer needs to restate the phases, safeguards, table-to-code mapping strategy,
checkpoint format, output structure, or stopping rules. Those belong in the
skill. The prompt supplies only this run's inputs and constraints.

Within one conversation, the agent can continue through the skill phases over
multiple turns because the loaded skill and intermediate findings remain in
context. Across conversations, the skill is rediscovered by its name or
description, but its prior execution state is not automatically preserved. If a
workflow must survive session boundaries, the skill should instruct the planner
to write checkpoints into user-owned `.ai/docs/` or `.ai/tasks/` files; the
skill remains the method, while `.ai/` files hold the durable run state.

This is the real value of a skill: it compresses repeated method knowledge into
a reusable, discoverable capability. It does not eliminate prompting; it changes
the prompt from a long procedure to a short invocation plus task-specific input.

## Why This Fits 1.1.8

- It matches the user's observed pain directly: repeated workflows are currently
  re-described manually and can become reusable skills.
- It reinforces Engaku's positioning as a curated customization bundle, not a
  competitor to VS Code's one-off `/create-skill` generator.
- It is a small, testable template addition consistent with previous skill
  releases such as `brainstorming`, `proactive-initiative`, and
  `karpathy-guidelines`.
- It does not require new dependencies or changes to hook behavior.

## Rejected Alternatives

### Full `skill-creator` Agent in 1.1.8

This remains attractive, but it is too much for the immediate release. It would
need new agent templates, likely a tester subagent, `.ai/engaku.json` model
defaults, README explanation, and updated agent-boundary conventions. That work
should be reconsidered only after the simpler skill proves useful.

### Rely Only on VS Code `/create-skill`

VS Code's built-in generator is useful, but it is generic. Engaku can add value
by encoding its own conventions: template/live sync, minimal scope, skill vs
prompt vs agent routing, verification expectations, and Python 3.8/stdlib project
constraints.

### Prompt File Instead of Skill

Prompt files are good for a single manually invoked command. The target behavior
here is a reusable authoring capability that can be auto-loaded when the user
asks to turn a workflow into a skill and can include reference guidance over
time. That fits the Agent Skills model better.

## Success Criteria

- `engaku init` creates `.github/skills/skill-authoring/SKILL.md` by default,
  including with `--no-mcp`.
- `engaku update` creates or updates the same skill.
- Skills authored by using `skill-authoring` are documented as user-owned and
  are not registered in Engaku's `_SKILLS`, `cmd_init.py`, `cmd_update.py`, or
  `src/engaku/templates/skills/` unless explicitly intended for an Engaku
  release.
- The skill frontmatter is valid and follows VS Code's documented skill rules.
- README, CHANGELOG, version metadata, tests, and project overview stay in sync.
- The deferred `skill-creator` agent remains explicitly out of scope for v1.1.8.
