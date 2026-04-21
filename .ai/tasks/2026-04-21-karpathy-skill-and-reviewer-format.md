---
plan_id: 2026-04-21-karpathy-skill-and-reviewer-format
title: Add karpathy-guidelines skill, surgical/simplicity globals, reviewer task-id format
status: done
created: 2026-04-21
---

## Background

User reviewed `forrestchang/andrej-karpathy-skills` (MIT) and wants its strongest
points folded into engaku. After mapping the four Karpathy principles against
existing assets:

- **Think Before Coding** — partly covered by `brainstorming`, but only as a
  user-invoked design skill. No in-loop reminder during coding.
- **Simplicity First** — present in this repo's own
  `.github/copilot-instructions.md` (`<implementationDiscipline>`), but **absent
  from the template** copied by `engaku init`. Bootstrapped repos get nothing.
- **Surgical Changes** — only a side bullet in `proactive-initiative`. No
  standalone doctrine on style-matching or no-drive-by-refactor.
- **Goal-Driven Execution** — covered by `verification-before-completion` and
  the planner's per-task `Verify:` field.

The strongest gaps are #2 and #3. Plan: ship one consolidated `karpathy-guidelines`
skill (concise, MIT-attributed, cross-references existing skills) AND promote a
short Simplicity + Surgical-Changes block into the template
`copilot-instructions.md` so every bootstrapped repo benefits globally.

Separately, the user wants reviewer's per-task verification block to include the
task number and title for traceability.

## Design

**1. New skill: `karpathy-guidelines`**

- Path: `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`
- Concise (~60 lines), four principles, with explicit cross-refs:
  - Think Before Coding → see `brainstorming` skill for full design flow
  - Goal-Driven Execution → see `verification-before-completion` skill
- MIT attribution to `forrestchang/andrej-karpathy-skills` and Karpathy's tweet
  in a footer.
- `disable-model-invocation: false`, `user-invocable: true`.
- Description triggers on writing/reviewing/refactoring code.

**2. Promote Simplicity + Surgical into template `copilot-instructions.md`**

- The template currently has only Lessons + boilerplate. Add a small
  `## Code Discipline` section with two subsections (Simplicity First, Surgical
  Changes) — 6–10 bullet points total. Keep it global (applies to all agents).
- Do NOT duplicate Goal-Driven (already enforced by per-task `Verify:` and the
  verification-before-completion skill) or Think (already enforced by planner
  + brainstorming).
- Mirror change into the live `.github/copilot-instructions.md` per repo convention
  (both files updated in same operation).

**3. Reviewer verification report format**

Current format in `reviewer.agent.md`:
```
> Verified with: `{exact command}`
> Result: {observed output summary, exit code}
> Verdict: PASS | FAIL
```

New format (adds task number + title from the task's `## Tasks` numbered list):
```
> Task {N}: {task title}
> Verified with: `{exact command}`
> Result: {observed output summary, exit code}
> Verdict: PASS | FAIL
```

Update both live (`.github/agents/reviewer.agent.md`) and template
(`src/engaku/templates/agents/reviewer.agent.md`).

**4. Wire new skill into init flow**

- Add the skill to the iterated SKILL_DIRS list in
  `src/engaku/cmd_init.py` (the non-MCP skills block, lines around 175–197).
- Add the corresponding expected path entry to the test fixture in
  `tests/test_init.py` (`EXPECTED_FILES`).
- Skill is unconditional — not MCP-related, so it ships even with `--no-mcp`.

## File Map

- Create: `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`
- Create: `LICENSE`
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `.github/copilot-instructions.md`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `src/engaku/cmd_init.py`
- Modify: `tests/test_init.py`
- Modify: `README.md` (add Credits section)
- Modify: `pyproject.toml` (version bump 1.1.1 → 1.1.2)
- Modify: `CHANGELOG.md` (add v1.1.2 entry)

## Tasks

- [x] 1. **Author `karpathy-guidelines` skill template**
  - Files: `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`
  - Steps:
    - Create the directory and `SKILL.md` with frontmatter (`name`,
      `description`, `argument-hint`, `user-invocable: true`,
      `disable-model-invocation: false`).
    - Body: short intro + four numbered principles (Think / Simplicity /
      Surgical / Goal-Driven), each ≤8 bullets, mirroring the upstream wording
      but trimmed.
    - Cross-reference `brainstorming` (Think) and
      `verification-before-completion` (Goal-Driven) instead of duplicating.
    - Footer: "Adapted from forrestchang/andrej-karpathy-skills (MIT)" with URL.
  - Verify: `test -f src/engaku/templates/skills/karpathy-guidelines/SKILL.md && head -12 src/engaku/templates/skills/karpathy-guidelines/SKILL.md`

- [x] 2. **Add Simplicity + Surgical block to template `copilot-instructions.md`**
  - Files: `src/engaku/templates/copilot-instructions.md`
  - Steps:
    - Append a new `## Code Discipline` section with two subsections:
      `### Simplicity First` (4–5 bullets) and `### Surgical Changes`
      (4–5 bullets). Keep it global — no agent-specific wording.
    - Match existing tone/style of the file.
  - Verify: `grep -E '^## Code Discipline|^### Simplicity First|^### Surgical Changes' src/engaku/templates/copilot-instructions.md | wc -l` → expect `3`

- [x] 3. **Mirror Code Discipline block into live `.github/copilot-instructions.md`**
  - Files: `.github/copilot-instructions.md`
  - Steps:
    - Insert the same `## Code Discipline` section, placed near the existing
      `## Code Style` section so related guidance lives together.
    - Verify it does not duplicate or contradict existing
      `<implementationDiscipline>` rules — if duplication, prefer to keep the
      richer existing rules and only add Surgical Changes guidance that is
      genuinely new.
  - Verify: `grep -c '## Code Discipline' .github/copilot-instructions.md` → expect `1`

- [x] 4. **Update reviewer template verification format**
  - Files: `src/engaku/templates/agents/reviewer.agent.md`
  - Steps:
    - In the "Report format per task:" block, prepend a new line:
      `> Task {N}: {task title}` above `> Verified with:`.
    - Update the surrounding prose to instruct reviewer to extract the task
      number and title from the task document's `## Tasks` numbered headings
      (e.g. `1. **Author skill template**` → `Task 1: Author skill template`).
  - Verify: `grep -A4 'Report format per task' src/engaku/templates/agents/reviewer.agent.md | grep '> Task {N}: {task title}'`

- [x] 5. **Mirror reviewer format change to live `.github/agents/reviewer.agent.md`**
  - Files: `.github/agents/reviewer.agent.md`
  - Steps:
    - Apply the identical edit from task 4 to the live agent file.
  - Verify: `grep '> Task {N}: {task title}' .github/agents/reviewer.agent.md`

- [x] 6. **Register new skill in `cmd_init.py`**
  - Files: `src/engaku/cmd_init.py`
  - Steps:
    - Locate the `# ── .github/skills/ ──` block (around line 175) listing
      non-MCP skills.
    - Add `karpathy-guidelines` to that iteration list (alongside
      `systematic-debugging`, `verification-before-completion`,
      `proactive-initiative`, etc.).
    - Update the docstring at top of file (lines 13–34) to include
      `karpathy-guidelines/SKILL.md` in the listed files.
  - Verify: `python -c "import ast,sys; src=open('src/engaku/cmd_init.py').read(); assert 'karpathy-guidelines' in src" && echo OK`

- [x] 7. **Update `test_init.py` expected files**
  - Files: `tests/test_init.py`
  - Steps:
    - Add `os.path.join(".github", "skills", "karpathy-guidelines", "SKILL.md")`
      to the `EXPECTED_FILES` tuple/list (around lines 22–31).
    - Also add a check inside the `--no-mcp` test that this skill is still
      created (it is unconditional).
  - Verify: `python -m unittest tests.test_init -v`

- [x] 8. **Full test suite + smoke init**
  - Files: none (verification only)
  - Steps:
    - Run `python -m unittest discover -s tests -v`.
    - Run `engaku init` in a throwaway temp git repo and confirm
      `.github/skills/karpathy-guidelines/SKILL.md` exists and reviewer agent
      contains the new format string.
  - Verify: `python -m unittest discover -s tests` exits 0

- [x] 9. **Add MIT `LICENSE` file**
  - Files: `LICENSE`
  - Steps:
    - Create a standard MIT `LICENSE` file with `Copyright (c) 2026 Jordan Liu`.
    - Confirm `pyproject.toml` already declares `license = {text = "MIT"}` — no
      change needed there.
  - Verify: `test -f LICENSE && grep -q 'Jordan Liu' LICENSE && echo OK`

- [x] 10. **Add Credits section to `README.md`**
  - Files: `README.md`
  - Steps:
    - Append a `## Credits` section at the end of the file with two subsections:
      - `karpathy-guidelines` skill: "Adapted from
        [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)
        (MIT, Copyright © Forrest Chang), itself derived from
        [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876)."
      - MCP servers: one-line acknowledgement for chrome-devtools-mcp,
        context7, and dbhub (repos already linked in the MCP section above;
        repeat URLs here for consolidated credit).
    - Keep the section concise (≤15 lines total).
  - Verify: `grep -c '## Credits' README.md` → expect `1`

- [x] 11. **Bump version and update CHANGELOG**
  - Files: `pyproject.toml`, `CHANGELOG.md`
  - Steps:
    - In `pyproject.toml`, change `version = "1.1.1"` → `version = "1.1.2"`.
    - Prepend a `## [1.1.2] — 2026-04-21` entry to `CHANGELOG.md` with the
      following items under **Added** and **Changed**:
      - Added: `karpathy-guidelines` bundled skill (Simplicity First, Surgical
        Changes, Think Before Coding, Goal-Driven Execution)
      - Added: `## Code Discipline` section (Simplicity First + Surgical
        Changes) in template `copilot-instructions.md`
      - Added: `LICENSE` file (MIT, Jordan Liu)
      - Added: `## Credits` section to `README.md`
      - Changed: Reviewer verification format now prefixes each task block with
        `Task {N}: {task title}`
  - Verify: `grep -m1 'version' pyproject.toml | grep -q '1.1.2' && grep -m1 '\[1.1.2\]' CHANGELOG.md && echo OK`

## Out of Scope

- Adding `Think Before Coding` or `Surgical Changes` as **separate** standalone
  skills — bundled into the single `karpathy-guidelines` skill instead.
- Re-writing `brainstorming` or `verification-before-completion` to merge with
  Karpathy content — they remain independent and are cross-referenced.
- Translating the skill into Chinese — English only per repo convention.
- Adding a separate `NOTICE` or `CREDITS` file — `LICENSE` + README credits +
  SKILL.md footer satisfies MIT attribution requirements.
- Modifying `coder.agent.md` or `planner.agent.md` to explicitly cite the new
  skill — model-invocable skill discovery already handles surfacing it.
- Adding license notices for MCP servers — we redistribute no MCP source code;
  only JSON configuration pointers are bundled.
