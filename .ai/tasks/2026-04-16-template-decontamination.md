---
plan_id: 2026-04-16-template-decontamination
title: Remove engaku-specific content from all template files
status: in-progress
created: 2026-04-16
---

## Background

`engaku init` copies template files verbatim into target repos. Several
templates currently contain engaku-specific conventions, directory examples,
or CLI references that only make sense for the engaku project itself. The
previous v0.3.2 fix only addressed the 3 instruction stubs but missed the
same class of problem in `copilot-instructions.md` and `overview.md`. In
addition, the 3 instruction stubs themselves (`hooks`, `templates`, `tests`)
are opinionated about what *kinds* of instruction files a project needs —
other projects may not have hooks or templates at all. The scanner agent is
already designed to discover and propose instruction groupings per-project,
so pre-installing fixed instruction stubs is redundant and potentially
confusing.

## Design

1. **Remove template instruction stubs entirely.** Delete the 3 files under
   `src/engaku/templates/instructions/` and remove the init code that copies
   them. The scanner agent handles instruction generation. The init tip
   message already tells users to run scanner.

2. **Clean `copilot-instructions.md` template.** Remove the two engaku-
   specific bullets:
   - "Model assignments per agent: see `.ai/engaku.json`. Run `engaku apply`…"
   - "Do not let any hook command exit non-zero unless it is intentionally blocking."
   - "When updating any agent or hook file, always update BOTH the live version (`.github/`) AND the template version in the same operation."
   Keep only truly universal bullets.

3. **Clean `overview.md` template.** Remove the prefilled directory example
   (`src/` / `tests/`) — leave just the heading and a comment telling the
   user to fill it in.

4. **Update `cmd_init.py`** — remove the instructions loop and docstring
   references.

5. **Update `test_init.py`** — remove the 3 instruction paths from
   `EXPECTED_FILES`.

6. **Bump version to 0.4.0** (minor bump because the init output changes —
   3 fewer files created). Update `__init__.py`, `pyproject.toml`, and
   `CHANGELOG.md`.

## File Map

- Delete: `src/engaku/templates/instructions/hooks.instructions.md`
- Delete: `src/engaku/templates/instructions/templates.instructions.md`
- Delete: `src/engaku/templates/instructions/tests.instructions.md`
- Delete: `src/engaku/templates/instructions/` (directory, after files removed)
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `src/engaku/templates/ai/overview.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `tests/test_init.py`
- Modify: `src/engaku/__init__.py`
- Modify: `pyproject.toml`
- Modify: `CHANGELOG.md`

## Tasks

- [ ] 1. **Delete template instruction stubs**
  - Files: `src/engaku/templates/instructions/hooks.instructions.md`,
    `src/engaku/templates/instructions/templates.instructions.md`,
    `src/engaku/templates/instructions/tests.instructions.md`
  - Steps:
    - `rm src/engaku/templates/instructions/hooks.instructions.md`
    - `rm src/engaku/templates/instructions/templates.instructions.md`
    - `rm src/engaku/templates/instructions/tests.instructions.md`
    - `rmdir src/engaku/templates/instructions`  (or `rm -r` if .gitkeep exists)
  - Verify: `! test -d src/engaku/templates/instructions && echo PASS`

- [ ] 2. **Remove instructions copy loop from cmd_init.py**
  - Files: `src/engaku/cmd_init.py`
  - Steps:
    - Delete the `# ── .github/instructions/` block (lines ~148-155) that
      iterates over the 3 instruction file names and calls `_copy_template`
    - Remove the 3 instruction filenames from the module docstring at the top
  - Verify: `python -c "import ast; ast.parse(open('src/engaku/cmd_init.py').read()); print('PASS')"`

- [ ] 3. **Remove instruction paths from test_init.py EXPECTED_FILES**
  - Files: `tests/test_init.py`
  - Steps:
    - Delete the 3 lines referencing `hooks.instructions.md`,
      `tests.instructions.md`, and `templates.instructions.md` from
      `EXPECTED_FILES`
  - Verify: `python -m pytest tests/test_init.py -v 2>&1 | tail -5`
    (or `python -m unittest tests.test_init -v`)

- [ ] 4. **Clean copilot-instructions.md template**
  - Files: `src/engaku/templates/copilot-instructions.md`
  - Steps:
    - Remove bullet: "When updating any agent or hook file, always update
      BOTH the live version…"
    - Remove bullet: "Model assignments per agent: see `.ai/engaku.json`…"
    - Remove bullet: "Do not let any hook command exit non-zero…"
  - Verify: `! grep -q 'engaku' src/engaku/templates/copilot-instructions.md && echo PASS`

- [ ] 5. **Clean overview.md template**
  - Files: `src/engaku/templates/ai/overview.md`
  - Steps:
    - Replace the prefilled `src/` and `tests/` directory lines with a
      comment placeholder like
      `<!-- List key directories and their roles (one line each). -->`
    - Keep the `## Directory Structure` heading
  - Verify: `! grep -q 'Application source code' src/engaku/templates/ai/overview.md && echo PASS`

- [ ] 6. **Bump version to 0.4.0 and update CHANGELOG**
  - Files: `pyproject.toml`, `src/engaku/__init__.py`, `CHANGELOG.md`
  - Steps:
    - `pyproject.toml`: `version = "0.3.2"` → `"0.4.0"`
    - `__init__.py`: `__version__ = "0.3.2"` → `"0.4.0"`
    - `CHANGELOG.md`: Add `## [0.4.0]` entry describing:
      - Removed: pre-installed `.github/instructions/` stubs (scanner agent
        handles this per-project)
      - Fixed: `copilot-instructions.md` and `overview.md` templates no
        longer contain engaku-specific content
  - Verify: `python -c "from engaku import __version__; assert __version__ == '0.4.0'; print('PASS')"`

- [ ] 7. **Run full test suite**
  - Steps:
    - `cd /Users/jordan.liu/dev/engaku && python -m pytest tests/ -v`
  - Verify: all tests pass (exit 0)

- [ ] 8. **Commit, tag v0.4.0, push**
  - Steps:
    - `git add -A && git commit -m "feat: remove engaku-specific content from templates"`
    - `git tag v0.4.0`
    - `git push origin main --tags`
  - Verify: `git log --oneline -1` shows the commit;
    `git tag -l v0.4.0` shows the tag

## Out of Scope

- Modifying the live `.github/` files for this repo (those are correct as-is).
- Changing agent templates — they are already generic.
- Changing skill templates — those are standalone skill docs, not project-specific.
- Modifying scanner agent behaviour.
