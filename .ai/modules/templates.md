---
paths:
  - src/engaku/templates/
  - src/engaku/templates/copilot-instructions.md
  - src/engaku/templates/ai/rules.md
  - src/engaku/templates/ai/overview.md
  - src/engaku/templates/ai/engaku.json
  - src/engaku/templates/agents/dev.agent.md
  - src/engaku/templates/agents/knowledge-keeper.agent.md
  - src/engaku/templates/agents/scanner.agent.md
  - src/engaku/templates/agents/scanner-update.agent.md
  - src/engaku/templates/agents/planner.agent.md
  - src/engaku/templates/hooks/session.json
  - src/engaku/templates/hooks/access-log.json
  - src/engaku/templates/hooks/precompact.json
  - .github/agents/planner.agent.md
---
## Overview
Snapshot templates copied by `cmd_init.py`.

Defaults: `agents: {}`, `max_chars: 1500`, `check_update: {ignore: [], uncovered_action: "warn"}` (`warn|block|ignore`).

Key agent templates live under `src/engaku/templates/agents/` and `.github/agents/`:
- `dev.agent.md`: developer agent. For each unclaimed source file the developer must choose either `assign-to-existing: <module-name>` or `create-new-module: <module-name>` and pass those decisions verbatim to `scanner-update`. If uncertain, obtain clarification before calling `scanner-update`.
- `scanner-update.agent.md`: incremental module-coverage executor. It applies the dev agent's explicit instructions: on `assign-to-existing` it adds file paths to the target module's `paths:` (ensuring a one-sentence `## Overview`), and on `create-new-module` it creates `.ai/modules/{name}.md` with `paths:` and a `## Overview` sentence. It must not infer structure or guess for undecided files; it requests clarification instead.
- `knowledge-keeper.agent.md`: edits only `.ai/modules/*.md`. Module files require `paths:` frontmatter and a `## Overview` heading. Bodies must be concise and ≤ MAX_CHARS; avoid vague or time-relative wording.

Hook templates: `session.json` (SessionStart), `access-log.json` (PostToolUse), `precompact.json` (PreCompact).
