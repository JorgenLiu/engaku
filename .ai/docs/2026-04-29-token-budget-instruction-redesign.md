# Token Budget Instruction Redesign

Related task: `2026-04-29-token-budget-instruction-redesign`

## Why the Current Design Failed

The current token-budget implementation treats token discipline as a normal skill plus repeated sections inside every bundled skill. VS Code Copilot skills are discovered as a name, description, and file path, then loaded only when the model decides the current request matches the skill. Debug logs from the current session showed exactly that behavior: `token-budget` and `serena` were absent from the initial skill discovery, appeared only after a later rediscovery, and still entered the prompt only as skill metadata unless explicitly read.

That means `token-budget` cannot reliably govern every response. A user request such as "execute remaining tasks" or "review this task plan" does not necessarily look like a token-budget task, so the model has no reason to load the skill body. Duplicating token-budget notes into every other skill does not solve this because those skills are also conditional.

## What Caveman Gets Right

Upstream Caveman is effective because it is not only a checklist. Its important properties are behavioral:

- It declares the mode active for every response until explicitly disabled.
- It defines concrete surface style: remove filler, pleasantries, hedging, and articles where safe; allow fragments; preserve technical terms and exact code/error text.
- It provides intensity levels so the user can choose compactness instead of accepting one fixed style.
- It keeps safety and clarity escape hatches for security warnings, irreversible actions, ordered instructions, or repeated clarification requests.
- It treats style as the product, not as incidental documentation.

Engaku's earlier localization kept the cost-saving rationale but weakened the style. "Professional brevity" is too generic; models already have many competing brevity instructions. The useful part to adopt is a compact response mode with concrete language operations and explicit exceptions.

Engaku should not copy Caveman text or brand voice verbatim. It should implement an Engaku-authored compact mode inspired by the same mechanics: terse technical prose, fragments allowed, exact technical content preserved, and clear escape hatches.

## New Design

Move token-budget behavior into a generated file instruction:

`src/engaku/templates/instructions/token-budget.instructions.md`

with a live copy at:

`.github/instructions/token-budget.instructions.md`

The instruction should use `applyTo: "**"` so it is loaded by default for every conversation and file context. It should be the single default home for token-budget behavior.

The instruction should contain:

- default active compact mode
- English by default, unless the user explicitly requests another language
- compact style rules: drop filler, pleasantries, hedging, repeated summaries, avoidable articles, and long lead-ins
- preservation rules: code, paths, commands, identifiers, exact errors, verification output, security warnings, and irreversible-action confirmations stay clear and exact
- response shape: concise progress updates and final answers, with expansion only when requested or risk demands it
- context discipline: state needed context, use targeted reads, prefer Serena/symbol tools when available, bound search/tool output
- safety/clarity escape hatches: use normal clear English for risky operations, multi-step instructions where fragments could mislead, and user requests for explanation
- optional user controls: compact/lite/full/normal wording, without requiring a separate skill

## What to Remove

Remove token-budget text from places where it is not domain knowledge:

- Remove `## Token Budget` sections from bundled skills.
- Remove the `skill-authoring` requirement that every generated skill include token-budget guidance.
- Remove `Token Budget Principle` sections from generated agent bodies.
- Remove the global token-budget block from `copilot-instructions.md` once the new instruction exists.
- Remove the `token-budget` bundled skill from init/update, templates, live repo, tests, and README references.

Serena should remain a skill and MCP integration because it is domain-specific code navigation guidance, not a universal communication policy. Serena skill wording should reference the always-on token-budget instruction only if needed, but it should not own token-budget behavior.

## Expected Result

Every new Engaku workspace should load compact token discipline through `.github/instructions/token-budget.instructions.md` by default. Skills return to domain workflows only. The system becomes easier to reason about: communication policy lives in instructions, optional workflows live in skills, and MCP setup remains in MCP/Serena files.