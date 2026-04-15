# Copilot Instructions
<!-- GLOBAL ONLY. Add project-wide coding standards and constraints here.
     Path-specific conventions belong in .github/instructions/*.instructions.md -->

- If the user expressed a new constraint or preference, update this file.
- If a significant architecture decision was made, record it in `.ai/decisions/`.
- When updating any agent or hook file, always update BOTH the live version (`.github/`) AND the template version in the same operation.
- Model assignments per agent: see `.ai/engaku.json`. Run `engaku apply` to push changes into agent frontmatter.
- Do not let any hook command exit non-zero unless it is intentionally blocking.
- Do not add agent-specific rules here — this file is global and applies to all agents. Agent-specific behaviour belongs in the agent's own `.agent.md` file.
