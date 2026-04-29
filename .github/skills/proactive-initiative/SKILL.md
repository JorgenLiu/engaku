---
name: proactive-initiative
description: "Check for related impacts after completing a task. Use after fixing a bug, finishing a feature, or completing any task before declaring it done. Forces a sweep for similar issues, upstream/downstream effects, edge cases, and documentation gaps instead of stopping at the single instance."
argument-hint: "Describe what you just completed and which file or module was affected."
user-invocable: true
disable-model-invocation: false
---

# Proactive Initiative

Fixing one instance without checking the category leaves the next bug hidden.

## Iron Law

Do not declare a task done without checking for related impacts.

## Post-Completion Checklist

After completing any task, work through this list before claiming done:

1. **Has the fix been verified with evidence?** Run the test or command. Do not rely on a prior run.
2. **Are there similar issues in the same file or module?** Scan for the same pattern in the surrounding code.
3. **Are upstream or downstream dependencies affected?** Check callers and callees of the changed code.
4. **Are there uncovered edge cases?** Consider boundary values, empty inputs, error paths, and concurrent access.
5. **Should any documentation or tests be updated?** If behavior changed, check whether existing tests or docs still accurately describe the system.

## Scope Expansion Rule

Fix one bug, check the category. If you find a pattern, address the pattern — not just the instance.

Example: if you fix a missing null check in one function, scan the same module for other call sites with the same risk. Fix those too if they are within scope.

## When NOT to Expand

Proactive initiative does not mean refactoring everything you touch.

- Do not refactor code unrelated to the current task.
- Do not add new features while fixing bugs.
- Do not restructure architecture while addressing a single defect.
- Stay within the original task scope. If sweep reveals issues outside scope, file a new task instead of silently expanding.

## Expected Output

- Confirmation that the primary fix is verified.
- Brief report on sweep results: similar patterns found (and fixed) or none found.
- List of any out-of-scope issues discovered, noted for follow-up.

## Token Budget

- Answer in English by default; switch language only when explicitly requested.
- Sweep with bounded queries; do not re-read whole modules when a targeted grep answers the question.
- Report only similar patterns and out-of-scope notes; skip the full investigation log.
