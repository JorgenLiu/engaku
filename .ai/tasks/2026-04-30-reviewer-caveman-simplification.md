---
plan_id: 2026-04-30-reviewer-caveman-simplification
title: Caveman compactness — inject filler + all agent prompts
status: done
created: 2026-04-30
---

## Background
Two related Lossless Compactness violations: (1) `SubagentStart` injects a filler sentence that duplicates the `state` attribute on the `<task>` tag. (2) All four agent prompts lack an explicit ban on process narration, leading agents to write "I'm going to…", "Next I'm checking…" style updates instead of evidence-bearing output.

## Design
Two changes:
1. `cmd_inject.py`: remove the `if state == "needs-review"` branch so `needs-review` tasks inject only the title line; `state` attribute carries the signal.
2. `reviewer.agent.md`: collapse the 5-step verification protocol into one sentence + verdict definition; merge Rules into existing sections; drop parenthetical filler.

Per project convention, both the live `.github/agents/reviewer.agent.md` and the template `src/engaku/templates/agents/reviewer.agent.md` must be updated in the same operation.

## File Map
- Modify: `src/engaku/cmd_inject.py`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `src/engaku/templates/agents/coder.agent.md`
- Modify: `.github/agents/coder.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/scanner.agent.md`
- Modify: `.github/agents/scanner.agent.md`

## Tasks

- [x] 1. **Remove SubagentStart filler line from cmd_inject.py**
  - Files: `src/engaku/cmd_inject.py`
  - Steps:
    - Delete the `if state == "needs-review": inner_lines.append(...)` / `else:` block; replace with unconditional `inner_lines.extend(unchecked)` so needs-review tasks emit title only (unchecked list is empty) and needs-work tasks emit unchecked items as before.
  - Verify: `python -c "import ast, sys; ast.parse(open('src/engaku/cmd_inject.py').read()); print('OK')"`

- [x] 2. **Rewrite reviewer.agent.md (template + live) to caveman style**
  - Files: `src/engaku/templates/agents/reviewer.agent.md`, `.github/agents/reviewer.agent.md`
  - Steps:
    - Replace body content with compact version (see Design below).
    - Keep frontmatter unchanged in each file (they differ between template and live).
  - Verify: `grep -c "All tasks completed" src/engaku/templates/agents/reviewer.agent.md .github/agents/reviewer.agent.md` → both should output `0`

- [x] 3. **Run tests**
  - Files: `tests/test_inject.py`
  - Steps:
    - Run inject tests to confirm no regression.
  - Verify: `python -m unittest tests.test_inject -v 2>&1 | tail -5`

## Compact reviewer body (reference for Task 2)

```
Task verification agent. Verify `[x]` checkboxes against acceptance criteria; update `status:`.

Follow the Engaku Global Kernel in .github/copilot-instructions.md; its Lossless Compactness rules are mandatory for every reply and generated artifact.

**Owns:** `status:` in `.ai/tasks/*.md` (sole authority for `status: done`); resets `[x]` → `[ ]` on FAIL.

**Does NOT:** create/restructure plans; modify source/tests/templates; touch `.ai/decisions/` or `.ai/docs/`; `edit` outside `.ai/tasks/*.md`.

**Terminal:** verification + post-PASS commit only.

## Invocation

Scan `.ai/tasks/` for `status: in-progress`. Multiple → ask which. One → start.

## Verification

For each `[x]` task in order: read its **Verify** command, run it, check exit code and full output. Do not trust prior output or coder claims. One task at a time.

Verdict: **PASS** (evidence matches) or **FAIL** (contradicts or absent).

Report:

> Task {N}: {task title}
> Verified with: `{exact command}`
> Result: {output summary, exit code}
> Verdict: PASS | FAIL

## After verification

- **All PASS:** set `status: done`, then `git add -A && git commit -m "{concise English message}"`.
- **Any FAIL:** reset `[x]` → `[ ]`, add `<!-- verify failed: {reason} -->`, leave `status: in-progress`. Do NOT fix code.
```

- [x] 4. **Add compactness enforcement line to all four agent prompts**
  - Files: `src/engaku/templates/agents/coder.agent.md`, `.github/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `.github/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `.github/agents/reviewer.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/scanner.agent.md`
  - Steps:
    - In each agent body, append one line immediately after the "Follow the Engaku Global Kernel" sentence: `No process narration. Report what changed or was found; state the next action.`
    - Template and live files must match (frontmatter differs between them; body line is identical).
  - Verify: `grep -r 'No process narration' src/engaku/templates/agents/ .github/agents/ | wc -l` → output `8`

## Out of Scope
- Changing any agent frontmatter (tools, hooks, model)
- Changing inject behavior for SessionStart or PreCompact
- PreToolUse boundary hook (separate plan)
