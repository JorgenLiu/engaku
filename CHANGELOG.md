# Changelog

## [1.1.1] — 2026-04-20

### Fixed
- Template `engaku.json` key `"dev"` renamed to `"coder"` so `engaku apply` correctly matches coder agent
- `@dev` references replaced with `@coder` in reviewer agent template and live version
- Output alignment standardized to 10-char left-aligned tags across `init`, `apply`, and `update`
- Removed 2-space leading indent from `cmd_apply.py` output

### Changed
- `_find_active_task` refactored to `_find_active_tasks` — returns all in-progress tasks instead of only the first
- Injection format changed from `<active-task>` to `<active-tasks>` with per-task `<task>` elements including `file` and `state` attributes
- Tasks with all checkboxes complete but `status: in-progress` are classified as `needs-review`

## [1.1.0] — 2026-04-20

### Added
- `.vscode/mcp.json` generation with three MCP servers: chrome-devtools-mcp (browser automation), context7 (live library docs), dbhub (multi-database access)
- `--no-mcp` flag for `engaku init` to skip `.vscode/mcp.json` and MCP-related skills
- Three new bundled skills: `chrome-devtools`, `context7`, `database`
- `engaku update` merges new MCP server entries into existing `.vscode/mcp.json`

### Changed
- `dev` agent renamed to `coder` across templates and live `.github/agents/`

## [1.0.0] — 2026-04-20

### Changed
- Scanner grouping heuristic is now scale-aware: hard "3–6 groups" cap replaced with a responsibility-boundary-driven heuristic (2–4 groups typical for small repos; no cap for larger repos)

### Note
- Final release with `requires-python = ">=3.8"`; Python 3.11 migration deferred; v1.1.x continues on Python 3.8

## [0.8.0] — 2026-04-18

### Added
- `lessons.instructions.md` template: auto-injected into all sessions via `applyTo: "**"`, giving agents a persistent place to record failure lessons
- `SessionStart` and `PreCompact` hooks added to planner, reviewer, and scanner agents so all agents receive project-context injection regardless of how they are invoked
- Verification principle added to planner agent: fetch documentation or source code before asserting facts about external systems

### Changed
- `copilot-instructions.md` template gains a `## Lessons` rule instructing agents to append one-line entries to `lessons.instructions.md` when they encounter errors or repeated mistakes

## [0.7.0] — 2026-04-17

### Changed
- Removed `## Release` section from task file format and reviewer protocol
- Reviewer now always runs `git add -A && git commit` after all Tasks PASS — no branching on Release section
- Removed `## Release` prohibition from dev agent

## [0.6.0] — 2026-04-17

### Added
- `PreCompact` hook now injects the full task body (Background, Design, File Map, and all checkbox lines) instead of only unchecked steps, so the compact model retains full task context
- `## Release` section in task format — irreversible operations (git push, tag, publish) are gated here; planner documents them, reviewer executes them after all Tasks PASS
- Reviewer agent now runs `git add -A && git commit` after all Tasks PASS (or executes `## Release` steps if the section exists) before setting `status: done`

### Changed
- `UserPromptSubmit` hook no longer caps injected task steps at 5 — all remaining unchecked steps are shown on every turn

### Fixed
- `__version__` in `__init__.py` was out of sync with `pyproject.toml`; both now reflect the correct release version

## [0.5.0] — 2026-04-17

### Added
- `engaku update` command — syncs `.github/agents/` and `.github/skills/` from the latest bundled templates, then auto-applies `engaku.json` model config
- `brainstorming` skill bundled by `engaku init` and `engaku update`

### Fixed
- `engaku.json` template now ships with default model assignments for all 4 agents (dev/reviewer = Sonnet, planner/scanner = Opus)

## [0.4.0] — 2026-04-16

### Removed
- Pre-installed `.github/instructions/` stubs (`hooks.instructions.md`, `tests.instructions.md`, `templates.instructions.md`) — the scanner agent handles instruction generation per-project

### Fixed
- `copilot-instructions.md` template no longer contains engaku-specific bullets (`engaku apply`, hook exit rules, live-vs-template sync rule)
- `overview.md` template no longer contains prefilled `src/`/`tests/` directory examples

## [0.3.2] — 2026-04-16

### Fixed
- Template instruction stubs (`hooks.instructions.md`, `templates.instructions.md`,
  `tests.instructions.md`) no longer contain engaku-specific conventions; replaced
  with generic placeholder stubs so target projects receive clean, fillable files
  after `engaku init`

## [0.3.1] — 2026-04-16

### Fixed
- Removed stale `.ai/rules.md` reference from planner agent "You do NOT" section
- Removed stale `.ai/modules/` and `.ai/rules.md` references from reviewer agent "You do NOT" section
- Generalized scanner workflow step 1 (removed hardcoded `__init__.py` / `__main__.py` exclusion)

## [0.3.0] — 2026-04-16

### Added
- `SubagentStart` hook support in `engaku inject` — injects overview + active-task
  context at the start of every reviewer subagent session
- `proactive-initiative` skill bundled by `engaku init`
- `mcp-builder` skill bundled by `engaku init` — adapted from anthropics/skills;
  guides building MCP servers in Python (FastMCP) or TypeScript (MCP SDK)
- `doc-coauthoring` skill bundled by `engaku init` — structured 3-stage workflow
  for co-authoring design docs, ADRs, and task plans
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) — matrix Python 3.8/3.9/3.11
- GitHub Actions publish workflow (`.github/workflows/publish.yml`) — OIDC Trusted
  Publisher, triggers on `v*.*.*` tags

### Fixed
- `pyproject.toml` package-data now bundles all template subdirectories correctly
  (was only matching top-level `templates/*.md`)
- `classifiers` list correctly placed under `[project]` (regression from CI-fix commit)

## [0.2.0] — 2026-04-15

### Added
- `engaku --version` flag
- `prompt-check` now injects active-task context (title + unchecked steps) into every agent turn
- PyPI-ready metadata: classifiers, project URLs, readme field in `pyproject.toml`
- Bundled skills (`systematic-debugging`, `verification-before-completion`, `frontend-design`) copied by `engaku init`

### Removed
- `check-update` command (was a no-op shell)
- `log-read` command (access log had no consumers)
- `Stop` hook no longer runs `engaku check-update`
- `PostToolUse` hook no longer runs `engaku log-read`
- Dead constants (`IGNORED_DIR_NAMES`, `IGNORED_EXTENSIONS`, `ACCESS_LOG`, etc.)
- Dead utilities (`is_code_file`, `parse_transcript_edits`)

### Changed
- `prompt-check` keyword matching uses phrase patterns instead of bare words to reduce false positives

## [0.1.0] — 2026-04-13

### Added
- Initial release — V4 native simplification
- `init`, `inject`, `prompt-check`, `task-review`, `apply` subcommands
- VS Code Agent Hooks: SessionStart, PreCompact, UserPromptSubmit, Stop
- `.github/instructions/` stubs and `.github/skills/` generated by `engaku init`
- Removed module-knowledge system in favour of VS Code native `.instructions.md` files
