---
plan_id: 2026-04-16-agent-cleanup-v0.3.1
title: Agent definition cleanup & v0.3.1 release
status: done
created: 2026-04-16
---

## Background

After the v0.3.0 release, manual cleanup of agent definitions removed stale
`rules.md` references from the template files but did not sync the live
`.github/agents/` copies. The live planner and reviewer agents still reference
the removed `.ai/rules.md` and `.ai/modules/` paths. Additionally, scanner's
workflow step 1 contains an unnecessarily specific file exclusion list that
should be generalized.

## Design

Three changes, all small:
1. Sync live `.github/agents/` planner and reviewer to match their cleaned
   templates (minus model lines, which `engaku apply` manages).
2. Generalize scanner workflow step 1 in both template and live versions.
3. Bump version to 0.3.1, update CHANGELOG, tag and publish.

## File Map
- Modify: `.github/agents/planner.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `.github/agents/scanner.agent.md`
- Modify: `src/engaku/templates/agents/scanner.agent.md`
- Modify: `src/engaku/__init__.py`
- Modify: `pyproject.toml`
- Modify: `CHANGELOG.md`

## Tasks

- [x] 1. **Sync live planner agent to match template**
  - Files: `.github/agents/planner.agent.md`
  - Steps:
    - Remove the line `- Modify \`.ai/rules.md\`` from the "You do NOT" section
  - Verify: `grep -c 'rules\.md' .github/agents/planner.agent.md` → exit 1 (no match)

- [x] 2. **Sync live reviewer agent to match template**
  - Files: `.github/agents/reviewer.agent.md`
  - Steps:
    - Replace `- Modify \`.ai/modules/\`, \`.ai/rules.md\`, \`.ai/decisions/\`, or \`.ai/docs/\`` with `- Modify \`.ai/decisions/\`, or \`.ai/docs/\``
  - Verify: `grep -cE 'rules\.md|modules/' .github/agents/reviewer.agent.md` → exit 1 (no match)

- [x] 3. **Generalize scanner workflow step 1 (template + live)**
  - Files: `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/scanner.agent.md`
  - Steps:
    - Change step 1 from `list all source files and test files (e.g. \`src/**/*.py\`, \`tests/**/*.py\`), excluding \`__init__.py\`, \`__main__.py\`.` to `list all source and test files in the repository (e.g. \`src/**/*.py\`, \`tests/**/*.py\`).`
  - Verify: `grep -c 'excluding' src/engaku/templates/agents/scanner.agent.md .github/agents/scanner.agent.md` → exit 1 (no match in either)

- [x] 4. **Bump version to 0.3.1**
  - Files: `src/engaku/__init__.py`, `pyproject.toml`
  - Steps:
    - Change `__version__ = "0.3.0"` to `"0.3.1"` in `__init__.py`
    - Change `version = "0.3.0"` to `"0.3.1"` in `pyproject.toml`
  - Verify: `python -c "import engaku; print(engaku.__version__)"` → `0.3.1`

- [x] 5. **Update CHANGELOG**
  - Files: `CHANGELOG.md`
  - Steps:
    - Add `## [0.3.1] — 2026-04-16` section above the 0.3.0 entry
    - Under `### Fixed`, list: removed stale `.ai/rules.md` and `.ai/modules/` references from planner and reviewer agent definitions; generalized scanner workflow step 1
  - Verify: `head -12 CHANGELOG.md` shows the new 0.3.1 section

- [x] 6. **Run tests**
  - Files: (none)
  - Steps:
    - Run `python -m pytest tests/ -q`
  - Verify: all tests pass, exit code 0 ✓ (70 passed)

- [ ] 7. **Commit, tag, push**
  - Files: (none)
  - Steps:
    - `git add -A && git commit -m "fix: clean stale agent refs, generalize scanner — v0.3.1"`
    - `git tag v0.3.1`
    - `git push origin main --tags`
  - Verify: `git tag -l v0.3.1` returns `v0.3.1`

## Out of Scope
- Updating old task/decision files that historically mention rules.md/modules.
- Changing agent model assignments.
- Any functional code changes beyond version bump.
