---
name: token-budget
description: "Save tokens under usage-based billing. Use when minimizing context, budgeting tokens, analyzing large codebases, reducing broad reads, or trimming verbose output while preserving technical substance."
argument-hint: "Describe the task and the parts of the codebase or documentation that are actually relevant."
user-invocable: true
disable-model-invocation: false
---

# Token Budget

Engaku is built for usage-based billing. Both input and output tokens cost
real money. This skill captures the discipline that keeps cost low without
losing technical substance.

Engaku does **not** copy Caveman's branded voice. We borrow only the principle:
preserve substance, remove filler.

---

## 1. English by default

- Answer in English. Switch language only when the user explicitly requests it.
- Identifiers, code, paths, commands, and exact error text always stay verbatim.

## 2. Professional brevity (Caveman-full inspired)

Preserve:

- code, commands, file paths, identifiers
- exact error text and verification output
- decisions, constraints, trade-offs

Remove:

- restating the task back to the user
- repeated summaries of what was just done
- hedging, throat-clearing, mood-setting phrases
- long explanations the user did not request

Default to terse progress updates and terse final answers. Expand only when
the user asks or when risk demands it.

## 3. Context map first

Before reading code:

1. State what you actually need (symbol, route, config key, error string).
2. List the few files most likely to contain it.
3. Read those targeted files. Do not pre-load whole modules "for context".

## 4. Serena / symbol tools before broad file reads

When Serena (or another symbol-aware tool) is available:

- Use symbol lookup, references, and definitions instead of reading whole files.
- Read whole files only when symbol-level access is unavailable or insufficient.
- See the `serena` skill for command details and fallback behavior.

## 5. Bounded tool output

- Pass narrow globs and includes to grep/search.
- Cap output: prefer `head`, `tail`, `wc -l`, or pipelines that summarize.
- Avoid commands that dump entire trees or full file contents when a slice
  would do.

## 6. Narrow external docs (Context7, web)

- Resolve the exact library + version first, then query a single topic.
- Do not pull general overviews when a specific API question is the goal.

## 7. Recurring-memory compression caution

For natural-language memory files reviewed by humans (e.g. long agent rules):

- Compression tools like `caveman-compress` can shrink recurring input cost,
  but only over reviewed text the user controls.
- Never compress code, configuration, or templates.

## 8. Model-cost check

- Cheaper models for routine edits, drafts, and summaries.
- Reserve expensive models for design, ambiguous reasoning, or risky changes.
- See `.ai/engaku.json` for per-agent model assignments.

## 9. When broader context is justified

Wider reads or longer answers are appropriate when:

- the user explicitly asks for depth
- a change crosses several files and silent assumptions would break things
- safety, security, or data integrity is at stake

In these cases, still prefer targeted reads first, then expand only as needed.
