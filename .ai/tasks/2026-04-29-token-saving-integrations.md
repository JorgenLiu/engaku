---
plan_id: 2026-04-29-token-saving-integrations
title: Mandatory English token budget and default Serena setup
status: done
created: 2026-04-29
---

## Background

Copilot usage-based billing makes token discipline a hard Engaku constraint. Caveman demonstrates large output-token savings from terse, substance-preserving communication, while `caveman-compress` demonstrates recurring input-token savings for reviewed memory files. Serena is the strongest MCP candidate for reducing broad code reads because it provides symbol-level navigation through a language-server-backed MCP server.

## Design

Make token-budget behavior mandatory across Engaku-generated agents and skills. Engaku should internalize Caveman full mode as English professional brevity: preserve technical substance, evidence, code, commands, paths, decisions, and verification results, but remove filler, repeated summaries, throat-clearing, avoidable hedging, and long explanations unless the user asks. Default generated agents should answer in English. Chinese or other languages are allowed only when the user explicitly requests that output language. Do not copy Caveman's branded voice into Engaku defaults.

Add a bundled `token-budget` skill for the full workflow: context map first, Serena/symbol tools before broad file reads, bounded tool output, narrow Context7 queries, concise output mode, recurring-memory compression caution, and model-cost strategy. Add a short always-on version of the same principle to global instructions, agent templates, and every generated skill so the rule is present even when the skill is not explicitly invoked.

Make Serena a default MCP with a default bootstrap path. Generated `.vscode/mcp.json` should include a `serena` stdio server using `serena start-mcp-server --context=vscode --project ${workspaceFolder}`. Default `.ai/engaku.json` MCP tool assignments should include `serena/*` for agents that inspect or modify code. Add `engaku setup-serena` and run it by default from `engaku init` when MCP is enabled; failures must warn but never block initialization. The setup command should detect or install `uv`, install Serena, run `serena init`, discover the concrete `serena` executable, and patch `.vscode/mcp.json` to use that absolute command when possible.

Serena setup must be robust against the normal failure modes: `uv` absent, pip blocked by permissions or externally managed Python, pip installing scripts outside PATH, `uv tool install` placing `serena` outside PATH, `serena init` failing or hanging, and VS Code MCP not inheriting the user's shell PATH. Use absolute executable paths when discovered and never rely on shell profile changes.

Longer analysis is recorded in `.ai/docs/2026-04-29-token-saving-mcp-skill-research.md`. The superseding decision is `.ai/decisions/010-default-serena-bootstrap-and-english-budget.md`.

## File Map

- Create: `src/engaku/templates/skills/token-budget/SKILL.md`
- Create: `.github/skills/token-budget/SKILL.md`
- Create: `src/engaku/templates/skills/serena/SKILL.md`
- Create: `.github/skills/serena/SKILL.md`
- Create: `src/engaku/cmd_setup_serena.py`
- Modify: `src/engaku/templates/copilot-instructions.md`
- Modify: `.github/copilot-instructions.md`
- Modify: `src/engaku/templates/agents/coder.agent.md`
- Modify: `src/engaku/templates/agents/planner.agent.md`
- Modify: `src/engaku/templates/agents/reviewer.agent.md`
- Modify: `src/engaku/templates/agents/scanner.agent.md`
- Modify: `.github/agents/coder.agent.md`
- Modify: `.github/agents/planner.agent.md`
- Modify: `.github/agents/reviewer.agent.md`
- Modify: `.github/agents/scanner.agent.md`
- Modify: `src/engaku/templates/skills/brainstorming/SKILL.md`
- Modify: `src/engaku/templates/skills/chrome-devtools/SKILL.md`
- Modify: `src/engaku/templates/skills/context7/SKILL.md`
- Modify: `src/engaku/templates/skills/database/SKILL.md`
- Modify: `src/engaku/templates/skills/doc-coauthoring/SKILL.md`
- Modify: `src/engaku/templates/skills/frontend-design/SKILL.md`
- Modify: `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`
- Modify: `src/engaku/templates/skills/mcp-builder/SKILL.md`
- Modify: `src/engaku/templates/skills/proactive-initiative/SKILL.md`
- Modify: `src/engaku/templates/skills/skill-authoring/SKILL.md`
- Modify: `src/engaku/templates/skills/systematic-debugging/SKILL.md`
- Modify: `src/engaku/templates/skills/verification-before-completion/SKILL.md`
- Modify: `.github/skills/brainstorming/SKILL.md`
- Modify: `.github/skills/chrome-devtools/SKILL.md`
- Modify: `.github/skills/context7/SKILL.md`
- Modify: `.github/skills/database/SKILL.md`
- Modify: `.github/skills/doc-coauthoring/SKILL.md`
- Modify: `.github/skills/frontend-design/SKILL.md`
- Modify: `.github/skills/karpathy-guidelines/SKILL.md`
- Modify: `.github/skills/mcp-builder/SKILL.md`
- Modify: `.github/skills/proactive-initiative/SKILL.md`
- Modify: `.github/skills/skill-authoring/SKILL.md`
- Modify: `.github/skills/systematic-debugging/SKILL.md`
- Modify: `.github/skills/verification-before-completion/SKILL.md`
- Modify: `src/engaku/templates/mcp.json`
- Modify: `.vscode/mcp.json`
- Modify: `src/engaku/templates/ai/engaku.json`
- Modify: `.ai/engaku.json`
- Modify: `src/engaku/cmd_init.py`
- Modify: `src/engaku/cmd_update.py`
- Modify: `src/engaku/cli.py`
- Modify: `tests/test_init.py`
- Modify: `tests/test_update.py`
- Modify: `tests/test_apply.py`
- Create: `tests/test_setup_serena.py`
- Modify: `README.md`
- Modify: `.ai/overview.md`

## Tasks

- [x] 1. **Author English token-budget skill**
  - Files: `src/engaku/templates/skills/token-budget/SKILL.md`, `.github/skills/token-budget/SKILL.md`
  - Steps:
    - Create both files with identical Engaku-authored content.
    - Add frontmatter with `name: token-budget`, a description that triggers on saving tokens, usage-based billing, minimizing context, context budgeting, large codebase analysis, reducing broad reads, and reducing verbose output, plus `user-invocable: true` and `disable-model-invocation: false`.
    - Add sections for: English by default, Caveman-full-inspired professional brevity, context map first, Serena/symbol tools before broad file reads, bounded tool output, narrow external docs, recurring-memory compression caution, model-cost check, and when broader context is justified.
    - State explicitly that Engaku preserves technical substance, code, paths, commands, and exact error text, and does not use Caveman's branded voice by default.
  - Verify: `cmp src/engaku/templates/skills/token-budget/SKILL.md .github/skills/token-budget/SKILL.md && grep -n "English by default\|professional brevity\|Serena\|context map\|Context7\|model-cost" src/engaku/templates/skills/token-budget/SKILL.md`

- [x] 2. **Add Serena skill guidance**
  - Files: `src/engaku/templates/skills/serena/SKILL.md`, `.github/skills/serena/SKILL.md`
  - Steps:
    - Create both files with identical Engaku-authored content.
    - Add frontmatter with `name: serena`, a description that triggers on semantic code navigation, symbol lookup, references, renames, large codebase exploration, and token-saving code reads.
    - Explain the default MCP command: `serena start-mcp-server --context=vscode --project ${workspaceFolder}`.
    - Document setup requirements: run `engaku setup-serena`, or manually install `uv`, run `uv tool install -p 3.13 serena-agent@latest --prerelease=allow`, then run `serena init`.
    - Add fallback behavior: if Serena tools are unavailable, continue with VS Code/search tools and tell the user how to finish setup.
  - Verify: `cmp src/engaku/templates/skills/serena/SKILL.md .github/skills/serena/SKILL.md && grep -n "serena start-mcp-server\|uv tool install\|serena init\|fallback" src/engaku/templates/skills/serena/SKILL.md`

- [x] 3. **Register new skills**
  - Files: `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Add `token-budget` to the always-copied skill list used by `engaku init`.
    - Add `serena` to the MCP-related skill list copied when `--no-mcp` is not set.
    - Add both skills to the `_SKILLS` tuple used by `engaku update`.
    - Extend init tests so a fresh project contains `.github/skills/token-budget/SKILL.md` and `.github/skills/serena/SKILL.md` by default.
    - Extend `--no-mcp` tests so `serena` is skipped with other MCP skills while `token-budget` still exists.
    - Extend update tests so missing generated skill folders are restored.
  - Verify: `python -m unittest tests.test_init tests.test_update`

- [x] 4. **Add Serena setup command**
  - Files: `src/engaku/cmd_setup_serena.py`, `src/engaku/cli.py`, `tests/test_setup_serena.py`
  - Steps:
    - Add a new `engaku setup-serena` subcommand routed from `cli.py` via lazy import.
    - Implement idempotent detection in stdlib only: first find `serena`, then find `uv`, then install `uv` with `[sys.executable, "-m", "pip", "install", "uv"]` only if `uv` is missing.
    - If pip installation succeeds but `uv` is still not on PATH, search `sysconfig.get_path("scripts")`, user script directories, and platform script names such as `uv` or `uv.exe` before giving up.
    - Install or upgrade Serena with `uv tool install -p 3.13 serena-agent@latest --prerelease=allow`.
    - After installation, discover the concrete `serena` executable via `shutil.which("serena")`, uv tool directory inspection, or platform script directories; validate candidates with `serena --help` or `serena --version` under a timeout.
    - Run `serena init` under a timeout; if it fails or prompts unexpectedly, print exact manual recovery commands and return non-zero only when the user ran `setup-serena` directly.
    - Update `.vscode/mcp.json` to use the absolute `serena` command when found; leave `command: serena` only as a last fallback with a warning.
    - Use `subprocess.run(..., shell=False, timeout=...)` for every external command.
    - Add tests with mocked subprocess/path discovery; never install uv or Serena during tests.
  - Verify: `python -m unittest tests.test_setup_serena`

- [x] 5. **Run Serena setup from init**
  - Files: `src/engaku/cmd_init.py`, `tests/test_init.py`
  - Steps:
    - Run Serena setup by default at the end of `engaku init` when MCP is enabled.
    - Add a `--skip-serena-setup` flag for offline/no-network environments.
    - Never fail `engaku init` because Serena setup failed; print a concise warning and manual `engaku setup-serena` command instead.
    - Ensure `engaku init --no-mcp` skips Serena setup.
    - Add tests for default invocation, skip flag, `--no-mcp`, and non-blocking setup failure.
  - Verify: `python -m unittest tests.test_init tests.test_setup_serena`

- [x] 6. **Make English token budget globally mandatory**
  - Files: `src/engaku/templates/copilot-instructions.md`, `.github/copilot-instructions.md`, `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`
  - Steps:
    - Update both template and live global instructions with a short mandatory Token Budget Principle: answer in English by default, preserve substance, remove filler, prefer concise progress/final responses, and expand only when asked or when risk demands it.
    - Update all four template agent files and live agent files with the same short principle, adapted to each role without changing role boundaries.
    - Add a Serena-first code exploration instruction for coder/reviewer/scanner: prefer Serena/symbol tools before broad file reads when available.
    - Keep wording compact so mandatory context does not erase the token savings it is meant to create.
  - Verify: `grep -n "Token Budget\|English by default\|professional brevity\|Serena" src/engaku/templates/copilot-instructions.md .github/copilot-instructions.md src/engaku/templates/agents/*.agent.md .github/agents/*.agent.md`

- [x] 7. **Update all bundled skills for token budget**
  - Files: `src/engaku/templates/skills/brainstorming/SKILL.md`, `src/engaku/templates/skills/chrome-devtools/SKILL.md`, `src/engaku/templates/skills/context7/SKILL.md`, `src/engaku/templates/skills/database/SKILL.md`, `src/engaku/templates/skills/doc-coauthoring/SKILL.md`, `src/engaku/templates/skills/frontend-design/SKILL.md`, `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`, `src/engaku/templates/skills/mcp-builder/SKILL.md`, `src/engaku/templates/skills/proactive-initiative/SKILL.md`, `src/engaku/templates/skills/skill-authoring/SKILL.md`, `src/engaku/templates/skills/systematic-debugging/SKILL.md`, `src/engaku/templates/skills/verification-before-completion/SKILL.md`, `.github/skills/brainstorming/SKILL.md`, `.github/skills/chrome-devtools/SKILL.md`, `.github/skills/context7/SKILL.md`, `.github/skills/database/SKILL.md`, `.github/skills/doc-coauthoring/SKILL.md`, `.github/skills/frontend-design/SKILL.md`, `.github/skills/karpathy-guidelines/SKILL.md`, `.github/skills/mcp-builder/SKILL.md`, `.github/skills/proactive-initiative/SKILL.md`, `.github/skills/skill-authoring/SKILL.md`, `.github/skills/systematic-debugging/SKILL.md`, `.github/skills/verification-before-completion/SKILL.md`
  - Steps:
    - Add a compact Token Budget note to each skill, tailored to the skill's workflow, requiring English output by default.
    - For context-heavy skills, require bounded searches/queries before broad reads.
    - For output-heavy skills, require concise summaries and avoid repeated explanations.
    - In `skill-authoring`, update the drafting rules so every generated skill must include its own compact `Token Budget` section with English-by-default professional brevity and bounded-context guidance.
    - In `skill-authoring`, update the validation checklist so missing `Token Budget` guidance is a validation failure for generated skills.
    - Keep every live/template skill pair identical after editing.
  - Verify: `for skill in brainstorming chrome-devtools context7 database doc-coauthoring frontend-design karpathy-guidelines mcp-builder proactive-initiative skill-authoring systematic-debugging verification-before-completion; do cmp "src/engaku/templates/skills/$skill/SKILL.md" ".github/skills/$skill/SKILL.md" || exit 1; done && grep -R "Token Budget" src/engaku/templates/skills .github/skills && grep -n "generated skill" src/engaku/templates/skills/skill-authoring/SKILL.md`

- [x] 8. **Add Serena default MCP server**
  - Files: `src/engaku/templates/mcp.json`, `.vscode/mcp.json`, `tests/test_init.py`, `tests/test_update.py`
  - Steps:
    - Add a `serena` server with `type: stdio`, `command: serena`, and args `start-mcp-server`, `--context=vscode`, `--project`, `${workspaceFolder}` to the template MCP JSON.
    - Add the same server to this repo's live `.vscode/mcp.json` without changing existing DBHub/Context7/Chrome DevTools entries.
    - Extend init tests so generated MCP JSON contains Serena with the expected command and args.
    - Extend update tests so existing `.vscode/mcp.json` files merge a missing Serena server without overwriting user-edited servers.
  - Verify: `python -m unittest tests.test_init tests.test_update && python -c 'import json; data=json.load(open("src/engaku/templates/mcp.json")); s=data["servers"]["serena"]; assert s["type"]=="stdio"; assert s["command"]=="serena"; assert "--context=vscode" in s["args"]; assert "${workspaceFolder}" in s["args"]'`

- [x] 9. **Assign Serena tools by default**
  - Files: `src/engaku/templates/ai/engaku.json`, `.ai/engaku.json`, `src/engaku/cmd_init.py`, `tests/test_init.py`, `tests/test_apply.py`, `tests/test_update.py`
  - Steps:
    - Add `serena/*` to default MCP tool assignments for coder, planner, reviewer, and scanner where those agents inspect or modify code.
    - Update `_write_engaku_json()` so fresh `engaku init` output includes the same Serena tool assignment when MCP is enabled.
    - Update this repo's `.ai/engaku.json` to include `serena/*` without changing model choices.
    - Extend apply tests to ensure existing MCP wildcard replacement preserves non-MCP tools and appends Serena with the configured list.
    - Extend update tests so `engaku update` plus `engaku apply` restores Serena tool assignments from `.ai/engaku.json`.
  - Verify: `python -m unittest tests.test_init tests.test_apply tests.test_update && grep -n "serena/\*" src/engaku/templates/ai/engaku.json .ai/engaku.json`

- [x] 10. **Document setup and fallback**
  - Files: `README.md`
  - Steps:
    - Add a `Token budget` section explaining English-by-default professional brevity and the difference between input tokens, output tokens, and model cost.
    - Add Serena default setup instructions: `engaku init` runs setup by default; users can rerun `engaku setup-serena`; offline users can use `engaku init --skip-serena-setup`.
    - Document the underlying commands: `pip install uv` is supported, `python -m pip install uv` is Engaku's fallback, then `uv tool install -p 3.13 serena-agent@latest --prerelease=allow`, then `serena init`.
    - Explain that Engaku may install uv/Serena as user tools, but does not install language-specific dependencies or user-level Serena hooks.
    - Add Caveman guidance: Engaku follows Caveman full mode's substance-preserving English brevity principle by default; teams may install upstream Caveman with `npx skills add JuliusBrussee/caveman -a github-copilot` if they want its exact modes.
    - Add `caveman-compress` caution for manually reviewed natural-language memory files only.
    - Keep Repomix as optional, with include/compress/search-before-read guardrails.
  - Verify: `grep -n "Token budget\|setup-serena\|pip install uv\|serena-agent\|serena init\|JuliusBrussee/caveman\|caveman-compress\|Repomix" README.md`

- [x] 11. **Update project overview**
  - Files: `.ai/overview.md`
  - Steps:
    - Add this exact sentence to the end of the Overview paragraph: `v1.1.10 makes English token budgeting mandatory across generated agents and skills, adds a bundled token-budget skill, and runs default Serena setup for symbol-level code navigation.`
  - Verify: `grep -n "token budgeting mandatory" .ai/overview.md`

- [x] 12. **Run full verification**
  - Files: `src/engaku/templates/skills/token-budget/SKILL.md`, `.github/skills/token-budget/SKILL.md`, `src/engaku/templates/skills/serena/SKILL.md`, `.github/skills/serena/SKILL.md`, `src/engaku/templates/copilot-instructions.md`, `.github/copilot-instructions.md`, `src/engaku/templates/agents/coder.agent.md`, `src/engaku/templates/agents/planner.agent.md`, `src/engaku/templates/agents/reviewer.agent.md`, `src/engaku/templates/agents/scanner.agent.md`, `.github/agents/coder.agent.md`, `.github/agents/planner.agent.md`, `.github/agents/reviewer.agent.md`, `.github/agents/scanner.agent.md`, `src/engaku/templates/skills/brainstorming/SKILL.md`, `src/engaku/templates/skills/chrome-devtools/SKILL.md`, `src/engaku/templates/skills/context7/SKILL.md`, `src/engaku/templates/skills/database/SKILL.md`, `src/engaku/templates/skills/doc-coauthoring/SKILL.md`, `src/engaku/templates/skills/frontend-design/SKILL.md`, `src/engaku/templates/skills/karpathy-guidelines/SKILL.md`, `src/engaku/templates/skills/mcp-builder/SKILL.md`, `src/engaku/templates/skills/proactive-initiative/SKILL.md`, `src/engaku/templates/skills/skill-authoring/SKILL.md`, `src/engaku/templates/skills/systematic-debugging/SKILL.md`, `src/engaku/templates/skills/verification-before-completion/SKILL.md`, `.github/skills/brainstorming/SKILL.md`, `.github/skills/chrome-devtools/SKILL.md`, `.github/skills/context7/SKILL.md`, `.github/skills/database/SKILL.md`, `.github/skills/doc-coauthoring/SKILL.md`, `.github/skills/frontend-design/SKILL.md`, `.github/skills/karpathy-guidelines/SKILL.md`, `.github/skills/mcp-builder/SKILL.md`, `.github/skills/proactive-initiative/SKILL.md`, `.github/skills/skill-authoring/SKILL.md`, `.github/skills/systematic-debugging/SKILL.md`, `.github/skills/verification-before-completion/SKILL.md`, `src/engaku/templates/mcp.json`, `.vscode/mcp.json`, `src/engaku/templates/ai/engaku.json`, `.ai/engaku.json`, `src/engaku/cmd_init.py`, `src/engaku/cmd_update.py`, `tests/test_init.py`, `tests/test_update.py`, `tests/test_apply.py`, `README.md`, `.ai/overview.md`
  - Steps:
    - Run the full stdlib unittest suite.
    - Parse all JSON files touched by the change.
    - Compare every live/template skill pair that was edited.
    - Inspect the diff for unrelated edits.
  - Verify: `python -m unittest discover -s tests && python -c 'import json; [json.load(open(p)) for p in ("src/engaku/templates/mcp.json", ".vscode/mcp.json", "src/engaku/templates/ai/engaku.json", ".ai/engaku.json")]' && for skill in token-budget serena brainstorming chrome-devtools context7 database doc-coauthoring frontend-design karpathy-guidelines mcp-builder proactive-initiative skill-authoring systematic-debugging verification-before-completion; do cmp "src/engaku/templates/skills/$skill/SKILL.md" ".github/skills/$skill/SKILL.md" || exit 1; done && git diff -- src/engaku/templates/skills .github/skills src/engaku/templates/copilot-instructions.md .github/copilot-instructions.md src/engaku/templates/agents .github/agents src/engaku/templates/mcp.json .vscode/mcp.json src/engaku/templates/ai/engaku.json .ai/engaku.json src/engaku/cmd_init.py src/engaku/cmd_update.py src/engaku/cmd_setup_serena.py src/engaku/cli.py tests/test_init.py tests/test_update.py tests/test_apply.py tests/test_setup_serena.py README.md .ai/overview.md`

## Out of Scope

- Installing language-specific Serena dependencies, upstream Caveman, or Repomix.
- Writing user-level Serena hooks under `~/.copilot/hooks/` automatically.
- Auto-running `caveman-compress` or rewriting generated Engaku files during `init` or `update`.
- Adding Repomix, Fetch MCP, Microsoft Learn MCP, GitHub MCP, or SaaS/cloud MCPs to the default generated `.vscode/mcp.json`.
- Adding `engaku init --mcp-profile`, `engaku discover`, or a registry-backed MCP marketplace command.
- Copying third-party skill content verbatim.
- Changing generated agent model names in `.ai/engaku.json`.
- Implementing automatic token accounting or billing telemetry.
- Adding new Python or JavaScript runtime dependencies to the Engaku CLI.