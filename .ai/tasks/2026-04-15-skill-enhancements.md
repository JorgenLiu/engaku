---
plan_id: 2026-04-15-skill-enhancements
title: Skill enhancements and new proactive-initiative skill
status: done
created: 2026-04-15
---

## Background

Research into tanweai/pua revealed practical patterns that can strengthen
engaku's existing skills. The `systematic-debugging` skill lacks guidance on
detecting spinning behavior and inverting assumptions. The
`verification-before-completion` skill lacks an anti-rationalization table for
common evasion patterns. There is no skill addressing proactive initiative
(checking for related issues after fixing one). See
`.ai/docs/skills-and-features-research.md` §2 for source analysis.

## Design

Three changes, all to SKILL.md template files (+ their live `.github/` copies):

1. **systematic-debugging** — add a "Phase 0: Spin Detection" section before
   Phase 1, add an "Assumption Inversion" step to Phase 3, and add a
   "Post-Fix Sweep" step to Phase 4.
2. **verification-before-completion** — add an "Anti-Rationalization" section
   listing common evasion phrases with why each is insufficient.
3. **proactive-initiative** (new) — a skill that triggers after task
   completion, enforcing a checklist: verify fix, scan for similar issues,
   check upstream/downstream, assess edge cases.

All three are pure Markdown — no Python code changes, no CLI changes, no new
dependencies.

## File Map

- Modify: `src/engaku/templates/skills/systematic-debugging/SKILL.md`
- Modify: `.github/skills/systematic-debugging/SKILL.md`
- Modify: `src/engaku/templates/skills/verification-before-completion/SKILL.md`
- Modify: `.github/skills/verification-before-completion/SKILL.md`
- Create: `src/engaku/templates/skills/proactive-initiative/SKILL.md`
- Create: `.github/skills/proactive-initiative/SKILL.md`
- Modify: `src/engaku/cmd_init.py` (docstring + init mapping for new skill)

## Tasks

- [x] 1. **Add spin detection and assumption inversion to systematic-debugging**
  - Files: `src/engaku/templates/skills/systematic-debugging/SKILL.md`, `.github/skills/systematic-debugging/SKILL.md`
  - Steps:
    - Add "Phase 0: Spin Detection" before Phase 1 with 3 checks: list all prior attempts, identify the common pattern, determine if you are making superficial vs structural changes
    - Add step 5 to Phase 3: "Invert your primary assumption — if you assumed the bug is in X, investigate as if X is correct and the problem is elsewhere"
    - Add step 5 to Phase 4: "Post-fix sweep — check the same module for similar patterns; fix one bug, check the category"
    - Add "Repeating the same approach with minor variations" to Red Flags
    - Both files must be identical after editing
  - Verify: `diff src/engaku/templates/skills/systematic-debugging/SKILL.md .github/skills/systematic-debugging/SKILL.md && echo IDENTICAL`

- [x] 2. **Add anti-rationalization section to verification-before-completion**
  - Files: `src/engaku/templates/skills/verification-before-completion/SKILL.md`, `.github/skills/verification-before-completion/SKILL.md`
  - Steps:
    - Add "## Anti-Rationalization" section after "Red Flags", with a table: phrase | why it fails | what to do instead
    - Include at least: "should pass now", "looks correct", "it's probably an environment issue", "I've tried everything", "it works on my machine", "the change is trivial, no need to test"
    - For each, explain why it is not evidence and what the correct verification action is
    - Both files must be identical after editing
  - Verify: `diff src/engaku/templates/skills/verification-before-completion/SKILL.md .github/skills/verification-before-completion/SKILL.md && echo IDENTICAL`

- [x] 3. **Create proactive-initiative skill**
  - Files: `src/engaku/templates/skills/proactive-initiative/SKILL.md`, `.github/skills/proactive-initiative/SKILL.md`
  - Steps:
    - Create SKILL.md with frontmatter: `name: proactive-initiative`, `description` targeting post-task-completion self-check, `user-invocable: true`, `disable-model-invocation: false`
    - Write body with Iron Law: "Do not declare a task done without checking for related impacts"
    - Add "Post-Completion Checklist" section with 5 items: (1) has the fix been verified with evidence? (2) are there similar issues in the same file/module? (3) are upstream/downstream dependencies affected? (4) are there uncovered edge cases? (5) should any documentation or tests be updated?
    - Add "Scope Expansion Rule" section: "Fix one bug, check the category. If you find a pattern, address the pattern — not just the instance."
    - Add "When NOT to expand" section to prevent over-engineering: don't refactor unrelated code, don't add features, stay within the original task scope
    - Both files must be identical
  - Verify: `diff src/engaku/templates/skills/proactive-initiative/SKILL.md .github/skills/proactive-initiative/SKILL.md && echo IDENTICAL`

- [x] 4. **Register new skill in cmd_init.py**
  - Files: `src/engaku/cmd_init.py`
  - Steps:
    - Add `proactive-initiative/SKILL.md` to the docstring's skill listing
    - Add the skill copy entry in the `run()` function's skill-copy loop (follow the existing pattern for `systematic-debugging` and `verification-before-completion`)
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -m pytest tests/test_init.py -q`

- [x] 5. **Add test coverage for new skill in test_init.py**
  - Files: `tests/test_init.py`
  - Steps:
    - Add `proactive-initiative/SKILL.md` to any assertions that check the list of created skills
    - Run the full init test to confirm the new skill is created in the output directory
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -m pytest tests/test_init.py -q`

## Out of Scope

- PUA-style pressure rhetoric or escalation levels.
- Methodology routing or "flavor" systems.
- State persistence across sessions (failure counters etc).
- Changes to any hook commands or agent definitions.
- PDF/Excel document skills (separate task).
