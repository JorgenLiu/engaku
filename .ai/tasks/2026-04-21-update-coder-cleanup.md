---
plan_id: 2026-04-21-update-coder-cleanup
title: Fix update karpathy sync and remaining dev-to-coder remnants
status: done
created: 2026-04-21
version: 1.1.3
---

## Background

Current `engaku update` behavior has drifted from the repo's current agent and
skill set. It does not sync the bundled `karpathy-guidelines` skill even though
`engaku init` now installs it, and the synced reviewer agent still contains
`dev agent` wording. Separately, `tests/test_apply.py` still uses `dev` as the
example agent name in several cases even though the active agent name is now
`coder`.

## Design

Use the smallest change set that restores consistency with the current naming
and template set.

1. Keep `cmd_update.py`'s explicit managed-file lists and add
   `karpathy-guidelines` to `_SKILLS` so `update` matches `init`.
2. Treat the reviewer `dev agent` wording as a template bug: update both the
   template and live copies so future `update` runs and this repo stay aligned.
3. Treat `tests/test_apply.py`'s `dev` fixtures as stale sample names, not a
   compatibility requirement. Rename those cases to `coder` so the tests reflect
   current defaults.
4. Strengthen `tests/test_update.py` so it fails if `karpathy-guidelines` is not
   synced or if `update` regenerates reviewer content with `dev agent` wording.

## File Map

- Modify: `src/engaku/cmd_update.py`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `tests/test_update.py`
- Modify: `tests/test_apply.py`
- Modify: `pyproject.toml`
- Modify: `src/engaku/__init__.py`
- Modify: `CHANGELOG.md`

## Tasks

- [x] 1. **Add update regression coverage**
  - Files: `tests/test_update.py`
  - Steps:
    - Add an assertion that `_SKILLS` includes `karpathy-guidelines`.
    - Add or rename the skill-creation regression so it checks that `update`
      creates `.github/skills/karpathy-guidelines/SKILL.md` in a fresh repo.
    - Add a regression that runs `update` and asserts the generated reviewer
      agent does not contain `dev agent` wording.
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -m unittest tests.test_update -v`

- [x] 2. **Fix update-managed skill and reviewer template output**
  - Files: `src/engaku/cmd_update.py`, `src/engaku/templates/agents/reviewer.agent.md`, `.github/agents/reviewer.agent.md`
  - Steps:
    - Add `karpathy-guidelines` to `cmd_update.py`'s `_SKILLS` tuple.
    - Replace the two `dev agent` references in the reviewer template with
      `coder agent`.
    - Mirror the same reviewer wording change into the live `.github` copy to
      satisfy the template-sync rule.
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -m unittest tests.test_update -v`

- [x] 3. **Rename apply test fixtures from dev to coder**
  - Files: `tests/test_apply.py`
  - Steps:
    - Update the four `dev`-named fixtures and expected strings to use
      `coder` instead.
    - Keep the test intent unchanged: these remain generic model/frontmatter
      behavior tests, only the sample agent name changes.
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -m unittest tests.test_apply -v`

- [x] 4. **Bump version to 1.1.3**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - Set `version = "1.1.3"` in `pyproject.toml`.
    - Set `__version__ = "1.1.3"` in `src/engaku/__init__.py`.
    - Prepend a `## [1.1.3] — 2026-04-21` section to `CHANGELOG.md` summarising the karpathy sync, reviewer wording fix, and test fixture rename.
  - Verify: `grep '1.1.3' pyproject.toml src/engaku/__init__.py CHANGELOG.md`

- [x] 5. **Run focused regression suite**
  - Files: `src/engaku/cmd_update.py`, `src/engaku/templates/agents/reviewer.agent.md`, `.github/agents/reviewer.agent.md`, `tests/test_update.py`, `tests/test_apply.py`
  - Steps:
    - Run the update test module and confirm the new karpathy/reviewer regressions pass.
    - Run the apply test module and confirm the renamed `coder` fixtures still pass.
    - Spot-check that no `dev agent` wording remains in the update-managed reviewer files.
  - Verify: `cd /Users/jordan.liu/dev/engaku && python -m unittest tests.test_update tests.test_apply -v && ! grep -n 'dev agent' src/engaku/templates/agents/reviewer.agent.md .github/agents/reviewer.agent.md`

## Out of Scope

- Rewriting historical docs, completed task files, or design notes that mention
  `dev`; those are archival records, not active runtime assets.
- Refactoring `cmd_update.py` to auto-discover managed skills from the template
  directory instead of using an explicit tuple.
- Any changes to `cmd_init.py` or `cmd_apply.py` beyond what is required for the targeted cleanup above.