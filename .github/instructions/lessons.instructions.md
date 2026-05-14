---
applyTo: "**"
---
# Lessons

Record lessons as reusable methods, not incident explanations. A good lesson says what to do differently next time: a check to run, sequence to follow, constraint to remember, or recovery step that prevents repeated wasted work. Do not record one-off task facts, guesses, root-cause trivia, user preferences, secrets, transient service failures, or unverified theories. Promote durable repo-wide rules to `.github/copilot-instructions.md` or a path-specific instruction file; update or remove stale lessons instead of adding duplicates.

Append lessons under `## Lessons` in this file.

## Lessons
- If `python -m unittest` exits 130 with no output, rerun from the explicit repo cwd before diagnosing code.
