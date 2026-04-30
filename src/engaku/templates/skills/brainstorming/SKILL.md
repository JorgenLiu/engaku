---
name: brainstorming
description: "Brainstorm and refine ideas before implementation. Use before building features, components, workflows, pages, or behavior changes when the solution is not yet well specified. Clarifies intent, constraints, success criteria, alternative approaches, and a concrete design before coding starts."
argument-hint: "Describe the idea, problem, or feature you want to design before implementation."
user-invocable: true
disable-model-invocation: false
---

# Brainstorming

Turn rough ideas into an explicit design before code is written.

## Hard Gate

Do not jump to implementation while the design is ambiguous. Before coding you must understand: **what** is being built, **why** it matters, **what constraints** apply, **what success** looks like.

## When To Use

New features, components/pages, behavior changes, architecture decisions, or any request where multiple approaches are plausible.

## Process

1. **Explore context** — inspect relevant files, docs, existing patterns first.
2. **Ask clarifying questions** one at a time. Focus on purpose, constraints, success criteria.
3. **Propose 2–3 approaches** with trade-offs; recommend one.
4. **Present design incrementally** — architecture, data flow, UI behavior, failure handling, testing as needed.
5. **Get approval** before implementation. Revise the design when parts are unclear; don't code around ambiguity.

## Design Principles

- Clear boundaries; small, well-defined units.
- Design proportional to task; simple tasks → short designs (still required).
- YAGNI aggressively.
- No unrelated refactoring proposals.
- In existing codebases, follow established patterns unless there's a strong reason not to.

## Output

A design, not implementation. When useful, write the approved design to a markdown doc in the project.
