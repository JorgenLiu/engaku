# VS Code 1.116 New Features — engaku Relevance Analysis

> Research date: 2026-04-18. Release date: April 15, 2026.
> Reference: https://code.visualstudio.com/updates/v1_116

---

## 1. Agent Debug Logs Persistence ★★★

**Setting:** `github.copilot.chat.agentDebugLog.fileLogging.enabled`

**What it does:** All agent session logs (tool calls, LLM requests, discovery
events, token usage, errors) are now persisted to disk. Historical sessions can
be reviewed after they end.

**Storage path:**
```
<workspaceStorage>/<id>/GitHub.copilot-chat/debug-logs/<session-uuid>/
```
The `VSCODE_TARGET_SESSION_LOG` template variable exposed to agents already
points to the current session's directory at this path.

**Format:** OTLP JSON. Parseable with stdlib `json`. The directory currently
contains at minimum a `models.json` file; full trace files are written when
the setting is enabled.

**Opportunities for engaku:**

1. **Session summary injection in `SessionStart` hook**
   `engaku inject` runs on `SessionStart`. If the setting is enabled, a new
   optional step could read the most recently completed session log, extract
   a short summary (token usage, tool call count, error count, duration), and
   inject it into the new session's context — giving the agent cross-session
   execution feedback. No other tool in the ecosystem does this today.

2. **Skill-creator eval metrics**
   If/when the skill-creator agent (see `skill-creator-agent-design.md`) is
   built, subagent debug logs could provide token usage and tool call count
   per test run — partial replacement for Claude's quantitative benchmark
   infrastructure.

**Recommended immediate action:** Add `github.copilot.chat.agentDebugLog.fileLogging.enabled`
to the recommended settings list in `engaku init` output or README.

**Deferred action:** Investigate the full session log schema (requires the
setting to be enabled and a session to be recorded) before implementing hook
integration.

---

## 2. GitHub Copilot Now Built-in ★★

**What it does:** Copilot Chat is now a built-in VS Code extension. New users
no longer need to install it manually.

**Impact on engaku:** The README currently instructs users to install the
Copilot extension before running `engaku init`. This step is now optional for
VS Code 1.116+. The install prerequisite section can be simplified or made
version-conditional.

---

## 3. Foreground Terminal Support for Agent Tools ★

**What it does:** `send_to_terminal` and `get_terminal_output` now work with
any terminal visible in the terminal panel, not just agent-created background
terminals.

**Impact on engaku:** No direct change needed. Indirectly improves the dev
agent's ability to interact with running processes (dev servers, watch modes)
during engaku-managed task execution.

---

## 4. Background Terminal Notifications Default-on ★

**Setting:** `chat.tools.terminal.backgroundNotifications` (now default `true`)

**Impact on engaku:** The reviewer agent's verification commands now complete
more responsively. No action needed — this is a passive improvement.

---

## 5. Tool Confirmation Carousel (Experimental) —

**Setting:** `chat.tools.confirmationCarousel.enabled`

**Impact on engaku:** Pure UX improvement for batch tool approvals. No
engaku-specific action needed. Mention in user-facing docs as a quality-of-life
tip.

---

## 6. Customizations Welcome Page —

**What it does:** Chat Customizations dialog now has a guided welcome page with
a natural language input to generate agents, skills, and instructions.

**Impact on engaku:** Overlaps with `engaku init` in surface area. engaku's
differentiation is the full system (hooks, task lifecycle, agents, instructions
together). No action needed; monitor whether this feature evolves to compete
more directly with `engaku init`.

---

## 7. Subagent UI Improvements ★

**What it does:** Expanded subagent progress view is more visually distinct and
easier to follow.

**Impact on engaku:** Positive context for the planned skill-creator agent
(see `skill-creator-agent-design.md`). The multi-subagent test workflow will be
more user-friendly than previously assumed.

---

## Action Summary

| Priority | Item | Action |
|---|---|---|
| **Now** | Agent Debug Logs | Add setting recommendation to `engaku init` output / README |
| **Soon** | Copilot built-in | Simplify README install prerequisites for VS Code ≥ 1.116 |
| **Later** | Debug log schema | Investigate full log structure to plan `SessionStart` hook integration |
| **Later** | Subagent UX | Note as supporting context in skill-creator agent design |
