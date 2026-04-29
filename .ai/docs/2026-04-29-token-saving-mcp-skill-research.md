# Token-Saving MCP and Skill Research - 2026-04-29

Related task: `2026-04-29-token-saving-integrations`

## Background

GitHub Copilot usage-based billing makes context discipline a product feature, not just an agent hygiene issue. This research scans community Copilot skills and MCP servers for options that can materially reduce token waste in Engaku-generated projects. The goal is not to add every popular server; it is to identify integrations that replace large context dumps with targeted, structured retrieval.

## Sources Checked

- GitHub `github/awesome-copilot` repository and its machine-readable `llms.txt` listing.
- Official `modelcontextprotocol/servers` reference server README.
- Official MCP registry API documentation and PulseMCP sub-registry documentation.
- `oraios/serena` README and VS Code client setup docs.
- Astral `uv` installation and tool-running documentation.
- `yamadashy/repomix` README and MCP tool docs.
- `JuliusBrussee/caveman` README, `caveman-compress` README, skill snippets, benchmark/eval docs, and implementation snippets.
- `upstash/context7` README.
- Microsoft MCP catalog README.
- Selected Awesome Copilot skill files: `context-map`, `what-context-needed`, `lsp-setup`, `suggest-awesome-github-copilot-skills`, `suggest-awesome-github-copilot-instructions`, `mcp-security-audit`, and `model-recommendation`.

## Evaluation Criteria

Use these criteria before adding anything to Engaku defaults. The billing constraint changes the threshold: high-impact token reducers should become defaults when they can degrade gracefully and do not require Engaku to install third-party runtimes itself.

- **Token impact:** Does it reduce context size or prevent broad file/doc reads?
- **Token direction:** Does it reduce input tokens, output tokens, or both?
- **Default safety:** Can it run without secrets, broad write permissions, or network surprises?
- **Setup weight:** Does it require language runtimes, local services, API keys, OAuth, or per-project initialization?
- **Overlap:** Does VS Code Copilot already provide a similar native tool?
- **Skill fit:** Can a lightweight skill guide good behavior without adding always-on context?

## High-Impact Candidates

### 1. Serena MCP

Serena is the strongest token-saving candidate for coding work. It exposes IDE-like semantic code retrieval, editing, refactoring, and memory over MCP, backed by LSP or a JetBrains plugin. Its docs explicitly position it as symbol-level tooling that helps agents operate faster and more efficiently in large codebases.

Relevant verified details:

- Supports MCP clients including VS Code/Copilot.
- For VS Code workspace setup, docs recommend `serena start-mcp-server --context=vscode --project ${workspaceFolder}`.
- Uses LSP-backed symbolic tooling and supports many languages.
- Setup requires `uv`, installing `serena-agent`, then running `serena init`.
- Serena's docs warn marketplace install commands may be outdated and recommend official quick-start instructions.

Recommendation: **Default generated MCP entry plus default setup flow.** Serena should be added to generated `.vscode/mcp.json` and `.ai/engaku.json` MCP tool assignments because it is the strongest candidate for reducing broad code reads. Add `engaku setup-serena` and run it by default from `engaku init` when MCP is enabled. The setup flow should detect `serena`; detect `uv`; install `uv` with `python -m pip install uv` as a fallback when absent; run `uv tool install -p 3.13 serena-agent@latest --prerelease=allow`; run `serena init`; then write the discovered absolute `serena` executable path into `.vscode/mcp.json`. If any step fails, initialization must continue and print exact recovery commands.

Setup feasibility notes:

- `pip install uv` is supported by official uv docs, but it may fail on externally managed Python installations or permission-restricted environments.
- A successful pip install does not guarantee `uv` appears on the shell PATH that VS Code MCP later sees. The setup implementation must locate `uv` and `serena` by absolute path when possible.
- Use `shutil.which("uv")`, Python script directories, and uv tool directories rather than assuming PATH mutation.
- Use subprocess timeouts for `pip`, `uv tool install`, and `serena init`; `engaku init` must warn and continue on any failure.
- `engaku setup-serena` run directly may return non-zero on setup failure, but the `engaku init` caller must treat failure as non-blocking.

### 2. Repomix MCP

Repomix packs local or remote repositories into AI-friendly files, counts tokens, can compress code with Tree-sitter, and can run as an MCP server. Its MCP tools include `pack_codebase`, `pack_remote_repository`, `read_repomix_output`, and `grep_repomix_output`. The docs state Tree-sitter compression can reduce token usage by about 70% while preserving semantic structure, and note that incremental search through packed output is usually better than reading the entire pack.

Relevant verified details:

- MCP command: `npx -y repomix --mcp`.
- `pack_codebase` / `pack_remote_repository` support `compress`, include patterns, ignore patterns, and largest-file summaries.
- `grep_repomix_output` supports regexp search with context lines.
- Security scanning is built in through Secretlint.
- The tool is excellent for remote repositories or one-time architecture snapshots, but can create huge intermediate files if used carelessly.

Recommendation: **Opt-in recipe, not default.** Pair it with guardrails: use include patterns, compression for large repos, `grep_repomix_output` before `read_repomix_output`, and never attach full output unless explicitly needed.

### 3. Context7 MCP

Engaku already bundles Context7. It remains a good default because it replaces stale model memory or pasted documentation with focused, version-specific documentation snippets. Context7 supports MCP and CLI+Skills modes, and its tools are simple: resolve a library ID, then query docs.

Recommendation: **Keep default.** Add a small token-saving note to the skill/README: provide the exact Context7 library ID when known to skip the resolve step, and ask narrow API questions instead of broad documentation dumps.

### 4. Caveman Skill And Caveman Compress

Caveman is a high-signal token-saving skill/plugin focused on output compression. It makes coding agents answer in a deliberately terse style and reports about 65% average output-token savings across its benchmark table, with individual tasks ranging from 22% to 87%. The README is explicit that Caveman mostly affects output tokens: "Caveman only affects output tokens — thinking/reasoning tokens are untouched." Its separate `caveman-compress` workflow targets input tokens by rewriting recurring natural-language memory files into shorter prose while preserving technical structures.

Relevant verified details:

- GitHub Copilot install path is documented as `npx skills add JuliusBrussee/caveman -a github-copilot`.
- Caveman auto-activation works for some clients, but Copilot installs the skill only; always-on behavior requires adding a rule or prompt snippet manually.
- `caveman-compress` is designed for natural-language memory files such as `CLAUDE.md`, todos, and preferences.
- The compression docs report about 46% average input-token reduction for memory files.
- The compressor preserves code blocks, inline code, URLs, file paths, commands, headings, technical terms, dates, version numbers, and table structure.
- The compressor writes a human-readable backup at `<filename>.original.md` and refuses to overwrite an existing backup.
- The compressor requires Python 3.10+ and calls Claude to perform compression, then validates and retries targeted fixes.

Recommendation: **Mandatory principle, Engaku-native implementation.** Caveman's token-saving principle should become a required Engaku rule across agents and skills: preserve substance, remove filler. Engaku should not adopt the branded caveman voice as its default, but every generated agent and skill should follow professional brevity: concise status updates, compact final answers, no repeated summaries, no unnecessary hedging, and no long explanations unless the user asks. `caveman-compress` should be documented for manually reviewed natural-language memory files; Engaku should not automatically rewrite generated files during `init` or `update`.

Language recommendation: **English by default.** Caveman full mode's strongest rule set is English-specific: drop articles, filler, pleasantries, and hedging while keeping technical terms exact. Engaku already requires user-facing strings in English, and most code/library/API terminology is English. Generated agents should therefore answer in English by default with professional Caveman-full-inspired brevity. Chinese can be allowed only when the user explicitly requests Chinese output; Wenyan/Chinese compression is interesting, but it is less safe as a default for technical precision and cross-team maintainability.

Skill-authoring implication: generated skills must inherit the same English token-budget rule. The `skill-authoring` skill should require a compact `Token Budget` section in every new SKILL.md it drafts, and its validation checklist should fail if that section is missing.

### 5. Context Selection Skills

Awesome Copilot includes `context-map` and `what-context-needed` skills. They are tiny but useful: both force the agent to identify required files before reading or editing. They do not need MCP, secrets, or new runtime dependencies.

Recommendation: **Bundle an Engaku-native `token-budget` skill inspired by these patterns, not copied verbatim.** The skill should enforce: map before reading, prefer Serena/symbol/usages tools before broad reads, request only needed files, cap tool output, summarize before expanding, use concise output by default, and choose cheaper models for simple read-only work.

### 6. Model Recommendation Skill

Awesome Copilot's `model-recommendation` skill is cost-oriented rather than token-oriented. It analyzes `.agent.md` or `.prompt.md` files and recommends lower-multiplier models where appropriate. The skill's model table may age quickly, so Engaku should not copy that data into defaults without a maintenance plan.

Recommendation: **Do not bundle as-is.** Add a small model-cost checklist to the token-budget skill and optionally document that teams can use model assignment in `.ai/engaku.json` to avoid expensive models for routine roles.

## Lower-Priority Candidates

### Fetch MCP

The official Fetch server extracts web pages as markdown and supports `max_length` plus `start_index` for chunked reading. It is explicitly useful for efficient LLM consumption, but it has a caution: it can access local/internal IP addresses.

Recommendation: optional recipe only if Engaku adds a `web-research` profile. Not a default.

### Microsoft Learn MCP

Microsoft Learn MCP provides real-time official Microsoft documentation at `https://learn.microsoft.com/api/mcp`. It is excellent for Azure/.NET/Microsoft-heavy projects, but too domain-specific for Engaku defaults.

Recommendation: optional recipe in a future docs/Microsoft profile, not part of the token-saving baseline.

### Playwright MCP

Microsoft's Playwright MCP uses structured accessibility snapshots and can bypass screenshot or vision-heavy workflows. Engaku already bundles Chrome DevTools MCP, so this would mainly be a browser-tooling preference change.

Recommendation: not now. Re-evaluate if Engaku decides to replace Chrome DevTools with Playwright or add browser profiles.

### Memory MCP

The official Memory server provides a local knowledge graph. Engaku already has `.ai/overview.md`, `.ai/decisions/`, `.ai/tasks/`, and `lessons.instructions.md`. Adding another memory system risks duplicate or always-on context rather than savings.

Recommendation: do not add by default. Keep memory file-based and explicit.

### Awesome Copilot Suggestion Skills

`suggest-awesome-github-copilot-skills` and `suggest-awesome-github-copilot-instructions` are useful for discovering relevant community customizations and avoiding duplicates. They are not direct token savers, but they can support future curation.

Recommendation: do not bundle now; use them as a reference for a future `engaku discover` command if desired.

### MCP Registry / PulseMCP / Glama

The official registry and PulseMCP API are useful discovery data sources. PulseMCP's public docs show a registry API with search, pagination, version filtering, popularity metadata, and premium tool/auth enrichments, but the API requires partner credentials. Glama and other directories are useful manually, but not stable enough to wire into Engaku without a cache and trust policy.

Recommendation: no direct integration yet. For future automation, prefer a local cached registry and an allowlist reviewed by Engaku maintainers.

## Recommended Engaku Direction

### Short Term

1. Add a bundled `token-budget` skill that teaches agents to minimize context, output, and premium requests.
2. Add short mandatory token-budget rules to global instructions, all generated agents, and all generated skills.
3. Add Serena to default `.vscode/mcp.json` and default `.ai/engaku.json` MCP tool assignments.
4. Add an idempotent `engaku setup-serena` command and have `engaku init` run it by default when MCP is enabled.
5. Make English the default response language for generated agents and skills, using Caveman-full-inspired professional brevity.
6. Add README setup docs for Serena, including uv installation options, `serena init`, verification, and fallback behavior.
7. Add README guidance for Caveman principles and optional upstream Caveman/`caveman-compress` usage for teams that want the exact external skill.
8. Add README guidance for using existing `.ai/engaku.json` model assignments to reserve expensive models for planning/review and use cheaper models for routine execution when acceptable.
9. Update Context7 guidance to prefer exact library IDs and focused queries.
10. Add tests that ensure the new skill is generated by `engaku init`, refreshed by `engaku update`, and Serena is present in generated/merged MCP configuration.

### Default Boundary

- Do add Serena to default `.vscode/mcp.json` and provide a default `engaku setup-serena` bootstrap. Do not fail `engaku init` if installation fails.
- Do not add Repomix to default `.vscode/mcp.json` because it can generate very large context unless guided carefully.
- Do make Caveman-inspired brevity mandatory, but do not auto-install the upstream Caveman plugin or auto-run `caveman-compress`.
- Do make English the generated-agent default language. Allow non-English only by explicit user request.
- Do not add Fetch MCP by default because of local/internal network access concerns.
- Do not add broad SaaS/cloud MCP servers by default because they require auth and introduce write-capable tool surfaces.

### Future Option

If optional integrations keep growing, add `engaku init --mcp-profile token-saving` or `engaku recipe token-saving`. That should be a separate design because it changes CLI surface area and template structure.

## Candidate Optional Config Snippets

### Serena Workspace MCP

```json
{
  "servers": {
    "serena": {
      "type": "stdio",
      "command": "serena",
      "args": [
        "start-mcp-server",
        "--context=vscode",
        "--project",
        "${workspaceFolder}"
      ]
    }
  }
}
```

Setup notes: `uv` can be installed with `pip install uv`, though official docs prefer isolated methods such as `pipx` or the standalone installer. Engaku should use `python -m pip install uv` only as a fallback during `engaku setup-serena`, then install Serena with `uv tool install -p 3.13 serena-agent@latest --prerelease=allow`, run `serena init`, and update `.vscode/mcp.json` to the absolute `serena` executable path when possible.

### Repomix MCP

```json
{
  "servers": {
    "repomix": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "repomix", "--mcp"]
    }
  }
}
```

Usage guardrails: pack specific directories or globs, use compression for large repositories, search packed output before reading it, and avoid attaching full packed output unless the task explicitly needs whole-repository analysis.

### Caveman Skill

```bash
npx skills add JuliusBrussee/caveman -a github-copilot
```

Usage guardrails: Engaku should make Caveman's professional brevity principle mandatory, but teams can still install upstream Caveman if they want its exact modes and commands. For recurring input-token savings, consider `caveman-compress` only on reviewed natural-language memory files, keep the `.original.md` backup, and do not compress code, config, task plans, ADRs, or legal/security-critical policy text automatically.

## Final Recommendation

The highest-value Engaku change is to make token budgeting a default behavior, not an optional recipe. Add a mandatory token-budget rule across agents and skills, add Serena as a default best-effort MCP server, and document Caveman/`caveman-compress` as the source pattern for professional brevity and reviewed memory compression. Repomix remains optional because it can create large intermediate context when misused.