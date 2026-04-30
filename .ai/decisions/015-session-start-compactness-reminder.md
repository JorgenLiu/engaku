---
id: 015
title: Hook compactness reminders in existing inject hook
status: accepted
date: 2026-04-30
related_task: 2026-04-30-session-start-compactness-hook
---

## Context
The global kernel already defines Caveman-inspired lossless compactness, but a resumed, compacted, or delegated context can still drift into verbose process narration before the agent re-anchors on those rules. Engaku already installs `SessionStart`, `PreCompact`, and `SubagentStart` hooks through `engaku inject`, so the missing piece is not hook registration. The need is a small dynamic reminder that appears even when `.ai/overview.md` and active tasks are empty.

## Decision
Add a compact reminder block to `engaku inject` for `SessionStart`, `PreCompact`, and `SubagentStart`. Reuse the existing hook command and agent frontmatter instead of adding a new subcommand, new hook command, or extra agent schema surface. Preserve each event's output shape: `SessionStart` and `SubagentStart` return `additionalContext`; `PreCompact` returns `systemMessage`.

## Consequences
Every generated agent with existing `engaku inject` hooks receives the same short behavioral anchor at startup, before compaction, and when subagents start. Empty repos no longer produce empty context for those hook events. Tests must update the previous empty-context expectations while proving task/project context is still preserved.
