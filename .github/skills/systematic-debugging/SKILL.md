---
name: systematic-debugging
description: "Debug technical issues systematically before proposing fixes. Use when facing bugs, test failures, build failures, performance regressions, flaky behavior, or confusing runtime errors. Forces root-cause investigation, pattern comparison, hypothesis testing, and minimal verified fixes instead of guess-and-check patches."
argument-hint: "Describe the bug, failure, symptoms, reproduction steps, and any error output you have."
user-invocable: true
disable-model-invocation: false
---

# Systematic Debugging

Random fixes waste time. Symptom fixes create rework.

## Iron Law

Do not propose fixes before investigating the root cause.

## When To Use

Test failures, unexpected behavior, build/CI failures, integration bugs, performance problems, regressions, cases where previous fixes did not work.

## The Five Phases

### Phase 0: Spin Detection

If you've already attempted a fix:

1. List every approach tried.
2. Identify the common assumption across them.
3. Determine: superficial (values, ordering) or structural (mechanism, root cause)?

Superficial variations on the same approach → stop. You're spinning. Move to Phase 1 fresh.

### Phase 1: Root Cause Investigation

1. Read the full error output.
2. Reproduce consistently.
3. Check recent changes that could explain it.
4. Gather evidence at the failing boundaries.
5. Trace the bad state/value back to its source.

### Phase 2: Pattern Analysis

1. Find similar working code or known-good examples.
2. Compare broken vs. working.
3. Identify all meaningful differences.
4. Understand dependencies, assumptions, configuration.

### Phase 3: Hypothesis and Testing

1. State one clear hypothesis.
2. Make the smallest possible change to test it.
3. Verify the result before doing anything else.
4. If it fails, form a new hypothesis — don't stack changes.
5. Invert your primary assumption — if you assumed bug is in X, investigate as if X is correct and the problem is elsewhere.

### Phase 4: Implementation

1. Create the simplest failing reproduction or test case.
2. Implement one fix for the identified root cause.
3. Verify the issue is resolved and nothing else regressed.
4. If multiple fix attempts fail, stop and question the architecture or assumptions.
5. Post-fix sweep — check the same module for similar patterns; fix one bug, check the category.

## Red Flags

Stop and return to Phase 1 if you catch yourself thinking:

- "Let me just try a quick fix."
- "I'll change several things at once."
- "I probably know what this is."
- "I'll test after I patch it."
- "One more guess."
- "Repeating the same approach with minor variations."

## Practical Rules

- One hypothesis at a time.
- One meaningful change at a time.
- Read stack traces fully.
- Evidence over intuition.
- Fix at the source, not the symptom.

## Output

- Suspected root cause.
- Evidence supporting it.
- Minimal change set.
- Verification the fix worked.
