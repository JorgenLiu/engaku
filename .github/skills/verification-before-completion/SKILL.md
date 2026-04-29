---
name: verification-before-completion
description: "Verify evidence before claiming work is complete, fixed, or passing. Use before saying tests pass, a bug is fixed, a build succeeds, requirements are met, or before committing, opening a PR, or moving on to the next task. Requires fresh verification output before any success claim."
argument-hint: "Describe what claim you are about to make and what command or checklist should prove it."
user-invocable: true
disable-model-invocation: false
---

# Verification Before Completion

Use this skill whenever you are about to say that work is done, fixed, passing, or ready.

## Iron Law

Do not make completion or success claims without fresh verification evidence.

## Gate Function

Before making any success claim:

1. Identify the exact command, test, checklist, or inspection that proves the claim.
2. Run it now, not based on memory or an earlier run.
3. Read the full output and check the exit status.
4. Confirm whether the output actually proves the claim.
5. Only then state the result, with evidence.

If any step is skipped, the claim is not verified.

## When To Apply

Apply this before:

- Saying tests pass.
- Saying a bug is fixed.
- Saying a build succeeds.
- Saying lint is clean.
- Saying requirements are complete.
- Committing or opening a PR.
- Handing work off to another agent or human.
- Moving to the next task.

## Common Failure Modes

### Tests

- Good: run the exact test command and report the observed pass result.
- Bad: "should pass now" or "looks correct".

### Build

- Good: run the build command and confirm exit code 0.
- Bad: assume build passes because lint passes.

### Bug Fixes

- Good: rerun the original reproduction or regression test and confirm the symptom is gone.
- Bad: assume the bug is fixed because code changed.

### Requirements

- Good: check the requirements or plan line by line.
- Bad: assume passing tests means all requirements are satisfied.

## Red Flags

If you catch yourself using wording like these before verifying, stop:

- "should"
- "probably"
- "seems fixed"
- "done"
- "great"
- "perfect"
- "ready"

Confidence is not evidence.

## Anti-Rationalization

Common evasion phrases that are not evidence. Stop when you hear yourself using them.

| Phrase | Why it fails | What to do instead |
|---|---|---|
| "should pass now" | Prediction is not a test result. | Run the test. Report the actual output. |
| "looks correct" | Visual inspection is not execution. | Execute the code and observe the result. |
| "it's probably an environment issue" | Blame-shifting without investigation. | Reproduce in a clean environment; confirm or rule out the environment. |
| "I've tried everything" | Implies exhaustion, not evidence. | List what was actually tried. Each attempt should have a result. |
| "it works on my machine" | Local success does not prove correctness everywhere. | Run in the target environment. Capture the output. |
| "the change is trivial, no need to test" | Trivial changes cause real bugs. | Run the relevant test suite regardless of perceived risk. |

## Practical Pattern

Use this shape when reporting status:

1. State what was verified.
2. State the exact command or check used.
3. State the observed result.
4. Then state the claim.

Example:

```text
Verified with: pytest tests/api/test_users.py -q
Observed result: 12 passed, exit code 0
Conclusion: the targeted tests pass.
```

## Bottom Line

Run the command. Read the output. Then make the claim.
