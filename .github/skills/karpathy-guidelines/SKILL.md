---
name: karpathy-guidelines
description: "Apply Karpathy's four core coding principles: think before coding, simplicity first, surgical changes, and goal-driven execution. Use when writing, reviewing, or refactoring code to keep changes minimal, purposeful, and verifiable."
argument-hint: "Describe the code change or review task you are about to perform."
user-invocable: true
disable-model-invocation: false
---

# Karpathy's Coding Principles

Four principles distilled from Andrej Karpathy's observations on high-quality
engineering. Apply them at the start of every non-trivial coding task.

---

## 1. Think Before Coding

Plan before you write a single line. Understand the problem fully.

- Re-read the spec, task, or error message carefully.
- Clarify ambiguities before touching code, not after.
- Identify the minimal change that satisfies the requirement.
- Write pseudo-code or a brief plan when the logic is non-trivial.
- **Do not type until you know what success looks like.**

> For full design-before-build workflow, invoke the `brainstorming` skill.

---

## 2. Simplicity First

The best code is the code you did not write.

- Prefer fewer lines over more lines.
- Prefer standard library over new dependency.
- Prefer readable names over clever tricks.
- Remove code when the feature can be dropped without loss.
- When two approaches work equally well, choose the one your team will understand
  without a comment.
- **Ask: "What is the simplest thing that could possibly work?"**

---

## 3. Surgical Changes

Touch only what the task requires. Leave the rest alone.

- Match the style and idioms of surrounding code exactly.
- Do not refactor, rename, or reformat files outside the task scope.
- Do not add features, tests, or error handling that were not asked for.
- One logical change per commit. Do not bundle unrelated fixes.
- If you notice something that should be improved but is out of scope, file a
  note (comment, issue, or task) rather than fixing it now.
- **Before saving: diff your changes and question every line that is not
  directly required.**

---

## 4. Goal-Driven Execution

Every change must be verifiable against its stated goal.

- Identify the acceptance criterion before writing code.
- Run the verification command from the task spec — do not assume it passes.
- If no verification command exists, define one before you start.
- Do not declare done until you have observed the expected output yourself.

> For the full verification-before-completion protocol, invoke the
> `verification-before-completion` skill.

---

*Adapted from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)
(MIT, Copyright © Forrest Chang), itself derived from
[Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876).*

## Token Budget

- Answer in English by default; switch language only when explicitly requested.
- Surgical principle applies to writing as well: minimal change, minimal explanation.
- Cut hedging and restated requirements; let the diff speak.
