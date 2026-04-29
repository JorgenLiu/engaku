---
name: brainstorming
description: "Brainstorm and refine ideas before implementation. Use before building features, components, workflows, pages, or behavior changes when the solution is not yet well specified. Clarifies intent, constraints, success criteria, alternative approaches, and a concrete design before coding starts."
argument-hint: "Describe the idea, problem, or feature you want to design before implementation."
user-invocable: true
disable-model-invocation: false
---

# Brainstorming

Use this skill to turn rough ideas into an explicit design before code is written.

## Hard Gate

Do not jump straight into implementation when the design is still ambiguous.

Before coding, you must understand:

- what is being built
- why it matters
- what constraints apply
- what success looks like

## When To Use

- New features.
- New components or pages.
- Behavior changes.
- Architecture decisions.
- Any request where multiple approaches are plausible.

## Process

1. Explore context first.
   Inspect the relevant project files, docs, or existing patterns before asking detailed questions.
2. Ask clarifying questions one at a time.
   Focus on purpose, constraints, and success criteria.
3. Propose 2-3 approaches.
   Include trade-offs and recommend one.
4. Present the design incrementally.
   Cover architecture, data flow, UI behavior, failure handling, and testing as needed.
5. Get approval before implementation.
   If parts are unclear, revise the design instead of coding around ambiguity.

## Design Principles

- Prefer clear boundaries and small, well-defined units.
- Keep the design proportional to the task: simple tasks can have short designs, but still need one.
- Use YAGNI aggressively.
- Avoid unrelated refactoring proposals.
- In existing codebases, follow established patterns unless there is a strong reason not to.

## Output

The output of brainstorming is a design, not implementation.

When useful, write the approved design to a markdown document in the working project.

## Token Budget

- Answer in English by default; switch language only when explicitly requested.
- Keep design summaries compact: capture decisions, trade-offs, and rejected alternatives without restating the prompt.
- Cut filler and repeated framing across revisions.
