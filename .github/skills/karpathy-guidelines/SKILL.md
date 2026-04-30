---
name: karpathy-guidelines
description: "Apply Karpathy's four core coding principles: think before coding, simplicity first, surgical changes, and goal-driven execution. Use when writing, reviewing, or refactoring code to keep changes minimal, purposeful, and verifiable."
argument-hint: "Describe the code change or review task you are about to perform."
user-invocable: true
disable-model-invocation: false
---

# Karpathy's Coding Principles

Four principles for high-quality engineering. Apply at the start of every non-trivial coding task.

---

## 1. Think Before Coding

Plan before typing. Understand the problem fully.

- Re-read the spec/task/error message carefully.
- Clarify ambiguities before touching code.
- Identify the minimal change that satisfies the requirement.
- Pseudo-code or brief plan for non-trivial logic.
- **Don't type until you know what success looks like.**

> Full design-before-build workflow → invoke `brainstorming` skill.

---

## 2. Simplicity First

The best code is the code you didn't write.

- Fewer lines over more.
- Standard library over a new dependency.
- Readable names over clever tricks.
- Remove code when the feature can be dropped without loss.
- Equal options → choose what your team understands without a comment.
- **Ask: "What is the simplest thing that could possibly work?"**

---

## 3. Surgical Changes

Touch only what the task requires.

- Match the surrounding code's style and idioms exactly.
- No refactor/rename/reformat outside scope.
- No features/tests/error-handling that weren't asked for.
- One logical change per commit; no bundled unrelated fixes.
- Out-of-scope improvement → file a note (comment/issue/task), don't fix now.
- **Before saving: diff your changes; question every line not directly required.**

---

## 4. Goal-Driven Execution

Every change must be verifiable against its goal.

- Identify the acceptance criterion before writing code.
- Run the verification command from the task spec — don't assume it passes.
- No verification command? Define one before starting.
- Don't declare done until you've observed the expected output.

> Full verification protocol → invoke `verification-before-completion` skill.

---

*Adapted from [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT, © Forrest Chang), derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876).*
