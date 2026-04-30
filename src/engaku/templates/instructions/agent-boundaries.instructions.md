---
applyTo: "**"
---
# Agent Boundaries

Ownership limits. Workflow details live in each `.agent.md`.

- **coder** — executes tasks and ticks checkboxes. No `status:` changes or plan rewrites.
- **planner** — owns task plans, decisions, and docs. No app code or subagents.
- **reviewer** — verifies `[x]` tasks, sets `status:`, commits after all PASS. No source or test fixes.
- **scanner** — analyzes conventions and writes `.github/instructions/` after approval. No implementation.
