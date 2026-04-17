---
plan_id: 2026-04-17-v050-update-command
title: "v0.5.0: engaku update + engaku.json defaults + brainstorming skill"
status: done
created: 2026-04-17
---

## Background

`engaku init` never overwrites existing files, so users who installed v0.3
or v0.4 cannot receive updated agent definitions, new skills, or bug
fixes to bundled templates without manually deleting and re-running init.
Additionally, the `engaku.json` template ships empty (`{"agents": {}}`),
making `engaku apply` a no-op for new users. Finally, the `brainstorming`
skill currently lives only in the maintainer's personal `~/.copilot/skills/`
and is not available to other engaku users.

## Design

### `engaku update`

A new subcommand that syncs engaku-managed template files into the target
repo, then auto-runs `engaku apply` to restore user model assignments.

| File category | Behaviour | Rationale |
|---|---|---|
| `.github/agents/*.agent.md` | **Overwrite** from template | Agent logic is engaku-managed; model customization lives in `engaku.json` and is re-applied |
| `.github/skills/*/SKILL.md` | **Overwrite existing + add new** | Skill content is engaku-managed |
| `.vscode/settings.json` | **Merge** single key | Same as init |
| `.ai/engaku.json` | **Skip** | User config |
| `.ai/overview.md` | **Skip** | User content |
| `.github/copilot-instructions.md` | **Skip** | User content |
| `.github/instructions/*` | **Skip** | User / scanner content |

After file sync, automatically call `cmd_apply.run(cwd)` to write
`engaku.json` model assignments back into the freshly-overwritten agent
frontmatter.

### `engaku.json` template fix

Populate the template with default model assignments:

```json
{
  "agents": {
    "dev": "Claude Sonnet 4.6 (copilot)",
    "planner": "Claude Opus 4.6 (copilot)",
    "reviewer": "Claude Sonnet 4.6 (copilot)",
    "scanner": "Claude Opus 4.6 (copilot)"
  }
}
```

Also update this project's own `.ai/engaku.json` to match.

### `brainstorming` skill

Adapt from `~/.copilot/skills/brainstorming/SKILL.md`:
- Remove reference to `planning-with-files` skill (not bundled)
- Keep language-/framework-agnostic
- Place under `src/engaku/templates/skills/brainstorming/SKILL.md`

## File Map

- Create: `src/engaku/cmd_update.py`
- Create: `tests/test_update.py`
- Create: `src/engaku/templates/skills/brainstorming/SKILL.md`
- Modify: `src/engaku/cli.py` (add `update` subcommand)
- Modify: `src/engaku/templates/ai/engaku.json` (fill defaults)
- Modify: `.ai/engaku.json` (fill defaults for this project)
- Modify: `src/engaku/cmd_init.py` (add brainstorming to skill list)
- Modify: `tests/test_init.py` (add brainstorming to EXPECTED_FILES)
- Modify: `src/engaku/__init__.py` (bump to 0.5.0)
- Modify: `pyproject.toml` (bump to 0.5.0)
- Modify: `CHANGELOG.md` (add 0.5.0 entry)

## Tasks

- [x] 1. **Fix engaku.json template and project config**
  - Files: `src/engaku/templates/ai/engaku.json`, `.ai/engaku.json`
  - Steps:
    - Replace `{"agents": {}}` with the 4-agent default config (dev=Sonnet,
      planner=Opus, reviewer=Sonnet, scanner=Opus) in both files
  - Verify: `python -c "import json; d=json.load(open('src/engaku/templates/ai/engaku.json')); assert len(d['agents']) == 4; print('PASS')"`

- [x] 2. **Create brainstorming skill template**
  - Files: `src/engaku/templates/skills/brainstorming/SKILL.md`
  - Steps:
    - Adapt from `~/.copilot/skills/brainstorming/SKILL.md`
    - Remove the last sentence referencing `planning-with-files` skill
    - Keep all other content (Hard Gate, When To Use, Process, Design
      Principles, Output sections)
  - Verify: `test -f src/engaku/templates/skills/brainstorming/SKILL.md && ! grep -q 'planning-with-files' src/engaku/templates/skills/brainstorming/SKILL.md && echo PASS`

- [x] 3. **Add brainstorming to cmd_init.py skill list**
  - Files: `src/engaku/cmd_init.py`
  - Steps:
    - Add `"brainstorming"` to the skills tuple in the `.github/skills/`
      loop (after `"doc-coauthoring"`)
    - Add `brainstorming/SKILL.md` to the docstring file listing
  - Verify: `python -c "import ast; ast.parse(open('src/engaku/cmd_init.py').read()); print('PASS')"`

- [x] 4. **Add brainstorming to test_init.py EXPECTED_FILES**
  - Files: `tests/test_init.py`
  - Steps:
    - Add `os.path.join(".github", "skills", "brainstorming", "SKILL.md")`
      to EXPECTED_FILES list
  - Verify: `python -m unittest tests.test_init -v 2>&1 | tail -3`

- [x] 5. **Create cmd_update.py**
  - Files: `src/engaku/cmd_update.py`
  - Steps:
    - Implement `run(cwd=None)` with the following logic:
      a. Require git repo (reuse `_is_git_repo` pattern from cmd_init)
      b. Define `_force_copy(src, dst, out)` — always overwrites, prints
         `[update]` if file existed or `[create]` if new
      c. Force-copy all 4 agent templates to `.github/agents/`
      d. Force-copy all 7 skill templates to `.github/skills/`
         (systematic-debugging, verification-before-completion,
         frontend-design, proactive-initiative, mcp-builder,
         doc-coauthoring, brainstorming)
      e. Call `_ensure_vscode_setting` for `chat.useCustomAgentHooks`
         (import from cmd_init or duplicate the helper)
      f. Import and call `cmd_apply.run(cwd)` to re-apply model config
      g. Print summary line
    - Implement `main()` entry point calling `sys.exit(run())`
  - Verify: `python -c "import ast; ast.parse(open('src/engaku/cmd_update.py').read()); print('PASS')"`

- [x] 6. **Register update subcommand in cli.py**
  - Files: `src/engaku/cli.py`
  - Steps:
    - Add `subparsers.add_parser("update", help="...")` after the
      `apply` parser
    - Add `elif args.command == "update":` dispatch block importing
      `from engaku.cmd_update import run`
  - Verify: `engaku update --help 2>&1 | head -1`

- [x] 7. **Create test_update.py**
  - Files: `tests/test_update.py`
  - Steps:
    - Follow test_init.py patterns (tmpdir, git init, _capture_run)
    - Test cases:
      a. `test_updates_agents_and_skills_in_existing_repo` — run init,
         corrupt an agent file, run update, verify agent restored
      b. `test_creates_new_skills_added_in_update` — run init (simulating
         old version without brainstorming), run update, verify
         brainstorming/SKILL.md exists
      c. `test_preserves_user_files` — run init, write custom content to
         `copilot-instructions.md` and `overview.md`, run update, verify
         those files unchanged
      d. `test_auto_applies_model_config` — run init, write engaku.json
         with model config, run update, verify agent frontmatter has
         model field
      e. `test_non_git_repo_returns_error` — no git init, returns 1
  - Verify: `python -m unittest tests.test_update -v 2>&1 | tail -5`

- [x] 8. **Bump version to 0.5.0 and update CHANGELOG**
  - Files: `src/engaku/__init__.py`, `pyproject.toml`, `CHANGELOG.md`
  - Steps:
    - `__init__.py`: `"0.4.0"` → `"0.5.0"`
    - `pyproject.toml`: `"0.4.0"` → `"0.5.0"`
    - `CHANGELOG.md`: Add `## [0.5.0]` entry:
      - Added: `engaku update` command — syncs agents and skills from
        latest engaku version, auto-applies model config
      - Added: `brainstorming` skill bundled by `engaku init`
      - Fixed: `engaku.json` template now ships with default model
        assignments for all 4 agents
  - Verify: `python -c "from engaku import __version__; assert __version__ == '0.5.0'; print('PASS')"`

- [x] 9. **Run full test suite**
  - Steps:
    - `python -m unittest discover -s tests -v`
  - Verify: all tests pass, exit 0

- [x] 10. **Commit, tag v0.5.0, push**
  - Steps:
    - `git add -A && git commit -m "feat: engaku update command, engaku.json defaults, brainstorming skill (v0.5.0)"`
    - `git tag v0.5.0`
    - `git push origin main --tags`
  - Verify: `git log --oneline -1` shows the commit

## Out of Scope

- Modifying planner agent definition (no-placeholder rules etc. — separate task)
- `writing-plans` or `test-driven-development` skills — decided against bundling
- Opt-out mechanism for skills the user doesn't want — accept "deleted skills return on update"
- Modifying live `.github/` files for this repo beyond what `engaku apply` handles
