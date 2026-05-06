---
name: verification-before-completion
description: "Verify evidence before claiming work is complete, fixed, or passing. Use before saying tests pass, a bug is fixed, a build succeeds, requirements are met, or before committing, opening a PR, or moving on to the next task. Requires fresh verification output before any success claim."
context: fork
argument-hint: "Describe what claim you are about to make and what command or checklist should prove it."
user-invocable: true
disable-model-invocation: false
---

# Verification Before Completion

Apply before saying work is done, fixed, passing, or ready.

## Iron Law

No completion or success claims without fresh verification evidence.

## Gate Function

Before any success claim:

1. Identify the exact command/test/checklist/inspection that proves the claim.
2. Run it now — not from memory, not from an earlier run.
3. Read the full output and exit status.
4. Confirm the output actually proves the claim.
5. State the result with evidence.

Any step skipped → claim not verified.

## When To Apply

Before: tests pass, bug fixed, build succeeds, lint clean, requirements complete, committing/opening PR, handoff to another agent or human, moving to next task.

## Common Failure Modes

| Domain | Good | Bad |
|---|---|---|
| Tests | Run the exact command, report observed pass result. | "should pass now", "looks correct". |
| Build | Run build command, confirm exit code 0. | Assume build passes because lint passes. |
| Bug fixes | Rerun original repro/regression test, confirm symptom gone. | Assume fixed because code changed. |
| Requirements | Check requirements/plan line by line. | Assume passing tests = all requirements met. |

## Red Flags

If you catch yourself using these before verifying, stop:

- "should", "probably", "seems fixed", "done", "great", "perfect", "ready".

Confidence is not evidence.

## Anti-Rationalization

| Phrase | Why it fails | What to do instead |
|---|---|---|
| "should pass now" | Prediction is not a result. | Run the test. Report the actual output. |
| "looks correct" | Visual inspection is not execution. | Execute the code and observe the result. |
| "it's probably an environment issue" | Blame-shifting. | Reproduce in clean env; confirm or rule out. |
| "I've tried everything" | Exhaustion isn't evidence. | List what was tried. Each attempt has a result. |
| "it works on my machine" | Local success doesn't prove correctness. | Run in target env. Capture the output. |
| "the change is trivial, no need to test" | Trivial changes cause real bugs. | Run the relevant test suite anyway. |

## Reporting Pattern

1. State what was verified.
2. State the exact command/check used.
3. State the observed result.
4. State the claim.

Example:

```text
Verified with: pytest tests/api/test_users.py -q
Observed result: 12 passed, exit code 0
Conclusion: the targeted tests pass.
```

## Bottom Line

Run the command. Read the output. Then make the claim.
