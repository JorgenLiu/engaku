---
name: proactive-initiative
description: "Check for related impacts after completing a task. Use after fixing a bug, finishing a feature, or completing any task before declaring it done. Forces a sweep for similar issues, upstream/downstream effects, edge cases, and documentation gaps instead of stopping at the single instance."
context: fork
argument-hint: "Describe what you just completed and which file or module was affected."
user-invocable: true
disable-model-invocation: false
---

# Proactive Initiative

Fixing one instance without checking the category leaves the next bug hidden.

## Iron Law

Do not declare a task done without checking for related impacts.

## Post-Completion Checklist

1. **Fix verified with evidence?** Run the test/command. Don't trust prior runs.
2. **Similar issues nearby?** Scan the same file/module for the pattern.
3. **Upstream/downstream affected?** Check callers and callees.
4. **Edge cases?** Boundary values, empty inputs, error paths, concurrency.
5. **Docs/tests need updating?** Verify they still describe the system accurately.

## Scope Expansion Rule

Fix one bug, check the category. If you find a pattern, address the pattern.

Example: missing null check fixed in one function → scan the module for other call sites with the same risk; fix those if in scope.

## When NOT to Expand

- No refactoring code unrelated to the task.
- No new features while fixing bugs.
- No architectural restructuring while addressing a single defect.
- Stay within original scope. Out-of-scope findings → file a new task, don't silently expand.

## Output

- Confirmation primary fix is verified.
- Brief sweep report: similar patterns found (and fixed) or none.
- Out-of-scope findings noted for follow-up.
