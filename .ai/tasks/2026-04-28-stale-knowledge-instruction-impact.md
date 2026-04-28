---
plan_id: 2026-04-28-stale-knowledge-instruction-impact
title: Stale Knowledge Cleanup and Planner Instruction Impact Check
status: done
created: 2026-04-28
---

## Background

The old module-knowledge system has already been removed, but the current live project knowledge still has smaller drift: hook-command instructions over-apply to ordinary CLI commands, test instructions describe conventions the repository no longer follows, and `.ai/overview.md` / README omit the `update` subcommand. Planner should also make instruction maintenance explicit when a plan changes durable project conventions, without reintroducing the old module-maintenance burden.

## Design

Keep `.github/instructions/*.instructions.md` focused on stable conventions, not per-module state. Fix only current stale knowledge in live project files, then update planner agent instructions so future plans include instruction or overview update tasks only when a change affects durable conventions, generated structure, agent workflows, or user-stated rules. Do not require instruction-update tasks for ordinary local bug fixes or implementation details.

Because planner agent files are generated templates with a live copy, update both `src/engaku/templates/agents/planner.agent.md` and `.github/agents/planner.agent.md` in the same implementation.

## File Map

- Modify: `.github/instructions/hooks.instructions.md`
- Modify: `.github/instructions/tests.instructions.md`
- Modify: `.ai/overview.md`
- Modify: `README.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `CHANGELOG.md`

## Tasks

- [x] 1. **Correct command-module instructions**
  - Files: `.github/instructions/hooks.instructions.md`
  - Steps:
    - Replace the body with wording that applies to all `cmd_*.py` modules: every command module exposes `run()` and `main()`, and `cli.py` lazy-imports subcommands.
    - Explicitly distinguish hook-backed commands (`inject`, `prompt-check`, `task-review`) from ordinary CLI commands (`init`, `apply`, `update`).
    - State that only hook-backed commands read hook JSON via `read_hook_input()` and emit hook-compatible JSON; ordinary CLI commands may use normal stdout/stderr and non-zero exits for user-facing errors.
  - Verify: `python -c 'from pathlib import Path; text=Path(".github/instructions/hooks.instructions.md").read_text(); assert "Ordinary CLI commands" in text; assert "Always check" not in text'`

- [x] 2. **Correct test convention instructions**
  - Files: `.github/instructions/tests.instructions.md`
  - Steps:
    - Replace the body with current repository conventions: stdlib `unittest`, `sys.path.insert(0, ".../src")`, one test file per CLI subcommand using names such as `test_init.py`, `test_apply.py`, and `test_update.py`.
    - Remove the stale prohibition on module-level imports; replace it with guidance that module-level imports are acceptable when the module has no optional runtime state, while hook stdin/stdout should still be mocked inside tests.
    - Keep the existing guidance for hook tests: mock stdin with `io.StringIO(json.dumps(hook_input))`, capture stdout/stderr, and restore streams in `finally` blocks.
  - Verify: `python -c 'from pathlib import Path; text=Path(".github/instructions/tests.instructions.md").read_text(); assert "Module-level imports are acceptable" in text; assert "Do not import engaku at module level" not in text'`

- [x] 3. **Sync overview and README command knowledge**
  - Files: `.ai/overview.md`, `README.md`
  - Steps:
    - In `.ai/overview.md`, change the subcommand summary from five commands to six commands and include `update`.
    - In `README.md`, add `update` to the Subcommands table with a description matching the current CLI behavior: sync generated agents and skills from bundled templates, merge MCP server additions, and apply `.ai/engaku.json` config.
    - Confirm existing README hook descriptions stay unchanged unless directly needed for accuracy.
  - Verify: `python -c 'from pathlib import Path; overview=Path(".ai/overview.md").read_text(); readme=Path("README.md").read_text(); assert "Six subcommands" in overview; assert "Sync generated agents" in readme'`

- [x] 4. **Add planner instruction impact check**
  - Files: `.github/agents/planner.agent.md`, `src/engaku/templates/agents/planner.agent.md`
  - Steps:
    - Add this bullet to the planner workflow rules in both files:
      ```markdown
      - **Instruction impact check.** When a plan changes durable project conventions, agent workflows, generated file structure, or user-stated rules, include a task to update the relevant `.github/instructions/*.instructions.md`, `.github/copilot-instructions.md`, or `.ai/overview.md` file with exact new text. Do not add instruction-update tasks for ordinary local bug fixes or implementation details.
      ```
    - Keep live and template planner bodies identical except for generated frontmatter differences such as `model:` and MCP tool entries.
    - Do not give planner permission to edit source code, tests, templates outside agent definitions, or `.ai/overview.md` directly.
  - Verify: `grep -n "Instruction impact check" .github/agents/planner.agent.md src/engaku/templates/agents/planner.agent.md`

- [x] 5. **Record the user-visible change**
  - Files: `CHANGELOG.md`
  - Steps:
    - Add an `[Unreleased]` section at the top if one does not already exist.
    - Under `### Fixed`, mention stale project instruction cleanup for command and test conventions.
    - Under `### Changed`, mention planner now includes instruction-impact tasks when plans affect durable conventions or generated structure.
  - Verify: `grep -n "\[Unreleased\]\|Instruction impact\|stale project instruction" CHANGELOG.md`

- [x] 6. **Run regression checks**
  - Files: none
  - Steps:
    - Run the full unittest suite to confirm instruction and agent text changes did not disturb packaging or template tests.
    - Run the targeted grep checks from Tasks 1-5 and confirm stale phrases are gone while the new planner phrase is present.
  - Verify: `python -m unittest discover -s tests`

## Out of Scope

- Reintroducing `.ai/modules/`, knowledge-keeper, scanner-update, stale-module detection, or any module-state maintenance system.
- Changing scanner workflow beyond the planner impact-check rule.
- Automatically enforcing instruction freshness with a new hook or blocker.
- Editing historical design docs, completed task plans, or project-history entries that intentionally describe past architectures.
