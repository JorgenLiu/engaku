# 2026-05-14 Copilot, GitHub MCP, Office Skill, and Lesson Research

Related task: `2026-05-14-github-mcp-office-lessons`

## Current Engaku Baseline

- Default MCP servers in `src/engaku/templates/mcp.json`: `chrome-devtools`, `context7`, `dbhub`.
- Default MCP tool grants in `src/engaku/templates/ai/engaku.json`: coder/planner get `chrome-devtools/*`, `context7/*`, `dbhub/*`; reviewer gets `chrome-devtools/*`, `dbhub/*`; scanner gets none.
- `engaku update` merges missing MCP `servers` and `inputs` into existing `.vscode/mcp.json` without replacing customized server entries.
- MCP-related bundled skills are skipped by `engaku init --no-mcp`; non-MCP Office skills are still installed.
- Office skills are bundled as whole directories with scripts and Python 3.8.4-pinned `requirements-py38.txt` files.

## Copilot / VS Code 1.120 Features Worth Tracking

Source: VS Code 1.120 release notes, release date 2026-05-13.

| Feature | Evidence | Engaku relevance | Recommendation |
| --- | --- | --- | --- |
| Agents window in Stable preview | Agents-first multi-project window, preferences persisted, extension opt-in via `extensions.supportAgentsWindow` | Engaku emits workspace customizations; Agents window changes where users run agents, not the file contract | Document compatibility later; no code change now |
| Copilot CLI plugin auto-discovery | VS Code now discovers Copilot CLI plugins installed with `copilot plugin install` | Engaku could eventually ship as an agent plugin bundling agents, hooks, skills, and MCP | Defer to separate plugin-packaging plan; current file templates remain simpler and stable |
| Agent plugins preview | Plugins can bundle slash commands, skills, custom agents, hooks, and MCP servers; plugin MCP uses top-level `mcpServers`, not workspace `servers` | A future Engaku plugin could reduce per-repo generated files, but plugin trust/update semantics differ | Research separately before changing init/update |
| Terminal output compression | Setting `chat.tools.compressOutput.enabled`; compresses large diffs, lockfiles, `ls -l`, `npm install` noise | Direct fit for Engaku's compactness goals | Add README optional recommendation, not default setting until preview stabilizes |
| Terminal risk assessment | Setting `chat.tools.riskAssessment.enabled`; adds AI-generated risk badge for terminal confirmations | Useful safety layer for coder/reviewer commands | Add README optional recommendation, not default setting |
| Plan mode inline editor | Setting `chat.planWidget.inlineEditor.enabled`; affects Claude/Copilot CLI plan editing | Planner already writes `.ai/tasks`; this is UI flow, not template contract | No Engaku change |
| BYOK token usage/thinking effort/model picker | Better UI for BYOK models | Engaku stores model names but not BYOK settings | No change |
| Markdown preview for diffs | Rendered Markdown diffs in Source Control | Helpful for reviewing `.ai/tasks`, README, changelog | Mention as optional reviewer workflow only |
| MCP resources/prompts/apps | VS Code MCP docs list resources, prompts, apps; apps need `chat.mcp.apps.enabled` | GitHub MCP has MCP Apps behind feature flag/insiders; could become useful | Do not enable by default; avoid experimental UI apps for now |
| MCP sandboxing | `sandboxEnabled` for local stdio MCP on macOS/Linux; not for HTTP servers | Current default local stdio servers: `chrome-devtools`, `dbhub`; remote GitHub/GitLab not sandboxable | Consider later for local stdio servers; not part of forge MCP work |
| Tool sets | VS Code supports `.jsonc` tool sets grouping built-in/MCP tools | Could reduce tool overload from GitHub | Defer; custom agent frontmatter already manages tool access |

## GitHub Default MCP

Recommended default server entry:

```json
"github": {
  "type": "http",
  "url": "https://api.githubcopilot.com/mcp/readonly"
}
```

Rationale:

- Official GitHub remote MCP endpoint: `https://api.githubcopilot.com/mcp/`.
- Remote server needs no local runtime; VS Code 1.101+ supports remote MCP and OAuth.
- GitHub docs also support PAT through an `Authorization` header with `${input:github_mcp_pat}`, but OAuth is safer as the default because Engaku should not prompt users into PAT setup.
- Default GitHub MCP toolsets when no configuration is supplied: `context`, `issues`, `pull_requests`, `repos`, `users`.
- Read-only mode is available for remote MCP via `/readonly` URL or `X-MCP-Readonly: true`; it disables write tools even if a write-capable toolset is requested.
- Additional remote-only toolsets include `copilot`, `copilot_spaces`, and `github_support_docs_search`; leave them out by default to control tool count and blast radius.

Agent grants:

- Add `github/*` to coder, planner, and reviewer when MCP is enabled.
- Keep scanner empty.
- Read-only default makes reviewer access acceptable for issue/PR/repo context.

Skill need:

- Add a bundled MCP skill, preferably `github`, because the server has many tools and multiple safety modes.
- The skill should state: prefer read-only default; never create/update/merge/close without explicit user request; inspect repo/issue/PR context before acting; use owner/repo identifiers; avoid leaking private repo content into unrelated prompts; use write-capable configuration only as an explicit local customization.

## GitLab MCP Decision

Do not add GitLab in this iteration.

Evidence kept for later:

- Official GitLab MCP server is Beta and available for Premium/Ultimate on GitLab.com, Self-Managed, and Dedicated.
- GitLab documents GitHub Copilot in VS Code explicitly with HTTP URL `https://<gitlab.example.com>/api/v4/mcp` and OAuth 2.0 Dynamic Client Registration.
- GitLab docs do not show a read-only header equivalent to GitHub MCP.
- Server availability depends on GitLab Duo / beta / experimental feature enablement and plan tier.

Reason to exclude now:

- User preference changed to keep only GitHub.
- GitLab has more tier/beta/setup variability than GitHub's hosted read-only MCP.
- Without documented read-only mode, default reviewer access would need extra policy decisions.

Follow-up option:

- Add GitLab later as an optional MCP recipe or a separate task, not as a default server.

## Lesson Memory Design Review

Current generated rules:

- `.github/copilot-instructions.md`: `When an environment issue, command failure, or repeated mistake teaches something reusable, append one line to .github/instructions/lessons.instructions.md under ## Lessons. Do not duplicate entries.`
- `.github/instructions/lessons.instructions.md`: same condition, scoped to the file itself.
- Template copies in `src/engaku/templates/copilot-instructions.md` and `src/engaku/templates/instructions/lessons.instructions.md` contain the same condition.

Observed behavior risk:

- The current rule frames lessons around problems: environment issue, command failure, repeated mistake.
- That frame invites entries like “X happened because Y,” which become local diagnosis notes instead of reusable operating method.
- The useful artifact should be method-level: what to do next time, what check to run first, what sequence prevents wasted work.
- It lacks a stable-vs-evolving split: global repo rules and constraints belong in `copilot-instructions.md`; learned operating methods can live in `lessons.instructions.md` until they become stable enough to promote.
- It lacks an expiry/update rule: a lesson that becomes wrong should be edited or removed, not duplicated with a correction.

Recommended split:

- `copilot-instructions.md`: stable, repo-wide policy and invariants. Examples: Python version constraints, zero dependencies, agent boundaries, template/live sync rules, release rules, external-doc verification rule.
- `.github/instructions/lessons.instructions.md`: small method memories discovered through work. Examples: command sequencing, verification heuristics, environment-specific recovery methods, repeated agent workflow corrections.
- Promotion path: if the same lesson keeps mattering across tasks and has become durable policy, move it into `copilot-instructions.md` or a path-specific `.instructions.md`, then remove or rewrite the lesson entry.

Recommended tuned rule for lesson files:

```markdown
Record lessons as reusable methods, not incident explanations. A good lesson says what to do differently next time: a check to run, sequence to follow, constraint to remember, or recovery step that prevents repeated wasted work. Do not record one-off task facts, guesses, root-cause trivia, user preferences, secrets, transient service failures, or unverified theories. Promote durable repo-wide rules to `.github/copilot-instructions.md` or a path-specific instruction file; update or remove stale lessons instead of adding duplicates.
```

Implementation impact:

- Update both live and template `lessons.instructions.md`.
- Update both live and template `copilot-instructions.md` with the lesson policy and promotion rule, not with the lessons list itself.
- No change needed to hook logic: hooks inject the same files; the rule wording controls behavior.

## Office Skill Extension Opportunities

### `docx-read`

Current coverage:

- `inspect_docx.py`: paragraph/headings/table/image/section/header/footer counts plus limited core properties.
- `extract_text.py`: ordered paragraphs/headings/tables; optional tables; heading-only mode.
- `docx_to_html.py`: Mammoth HTML or raw text conversion.

High-value extensions:

- Add comments inspection: parse `word/comments.xml`, output comment id, author, date, text, and anchor presence when available.
- Add tracked-change inspection: parse `w:ins` and `w:del` elements from document XML and summarize inserted/deleted text without accepting/rejecting changes.
- Add hyperlinks, footnotes, and endnotes extraction via relationships and `word/footnotes.xml` / `word/endnotes.xml`.
- Improve table extraction with merged-cell metadata (`gridSpan`, `vMerge`) and stable cell coordinates.
- Expand metadata: subject, keywords, category, last modified by, modified timestamp, custom properties when XML exists.
- Optional image export script with `--output-dir`, writing extracted media files without modifying source DOCX.

Keep out of scope:

- `.doc` legacy support, exact layout reproduction, editing/generating DOCX, accepting/rejecting changes.

### `xlsx-analyze`

Current coverage:

- `inspect_workbook.py`: sheets, dimensions, merged cells, formula count/sample formulas; CSV/TSV basic headers/row count.
- `profile_sheet.py`: pandas dtype/missing/unique/numeric/date-like/sample rows.
- `formula_graph.py`: formula operand reference extraction for one sheet; focus direct dependencies/dependents only.

High-value extensions:

- Fix `formula_graph.py` contract drift: `--max-depth` is currently reserved but advertised; `_MAX_RANGE_EXPAND` exists but is unused; named ranges are advertised but unsupported; cross-sheet references are marked unresolved even when the referenced sheet exists.
- Scan workbook-wide formulas so `--focus` dependents can find references from other sheets.
- Expand small ranges up to the existing cap, preserve large ranges with truncation warnings, and mark only external workbook refs as unresolved.
- Resolve workbook defined names where openpyxl exposes destinations.
- Add workbook inspection for hidden sheets, workbook defined names, Excel tables, charts/images, data validations, conditional formatting, frozen panes, filters, and external links.
- Make CSV/TSV inspection streaming instead of `list(reader)` so huge files do not load fully into memory.
- Add profile fields: top values, string length min/max/mean, boolean-like flag, duplicate row count, blank/duplicate header warnings.
- Optional `diff_workbooks.py`: compare sheet names, headers, dimensions, formulas, and defined names across two workbooks.

Keep out of scope:

- Formula evaluation/recalculation, `.xls`/`.xlsb` support unless a new optional dependency plan is approved, spreadsheet editing/generation, Google Sheets API.

## Recommended Implementation Path

1. Add GitHub MCP with read-only remote URL; it is stable, official, no local runtime, and aligns with the updated request.
2. Add a `github` skill because GitHub MCP is a broad external-tool surface with authentication, scope, and write-action risks.
3. Tune lesson-memory wording so entries are reusable methods, with stable repo-wide rules promoted to `copilot-instructions.md` or path-specific instructions.
4. Fix `xlsx-analyze` formula graph drift before adding new XLSX features; the current skill advertises behavior that is only partially implemented.
5. Extend DOCX read support with comments/tracked-change visibility and richer references before adding image export.
6. Treat GitLab MCP, Agent Plugins, and Copilot CLI plugin packaging as separate future plans.
