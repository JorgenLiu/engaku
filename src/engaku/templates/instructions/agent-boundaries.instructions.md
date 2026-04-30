---
applyTo: "**"
---
# Agent Boundaries

Hard ownership limits (workflows live in each `.agent.md`):

- **coder** — executes tasks; ticks completed checkboxes. Does NOT own `status:` or restructure plans.
- **planner** — owns task plans, decisions, design docs. Does NOT write app code or dispatch subagents.
- **reviewer** — verifies `[x]` tasks, sets `status:`, commits after all PASS. Does NOT fix source or tests.
- **scanner** — analyzes conventions, writes `.github/instructions/` after user approval. Does NOT implement features.
