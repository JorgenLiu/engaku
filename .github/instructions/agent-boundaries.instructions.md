---
applyTo: "**"
---
# Agent Boundaries

Agent-specific workflows remain in the corresponding `.agent.md` files. These ownership boundaries are hard limits:

- coder executes implementation tasks and may tick completed checkboxes; it does not own task `status:` or restructure plans.
- planner owns task plans, design docs, and decisions; it does not write application code or dispatch subagents.
- reviewer verifies completed task checkboxes, updates task `status:`, and commits after all tasks pass; it does not fix source or tests.
- scanner analyzes repository conventions and writes `.github/instructions/` only after user approval; it does not implement features.