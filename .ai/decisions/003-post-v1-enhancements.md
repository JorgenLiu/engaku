---
id: 003
title: "Post-1.0 enhancement directions: Python 3.11 and learnings/transcript system"
status: accepted
date: 2026-04-17
related_task: none
---

## Context

During the v0.5.x design review session, two significant enhancement directions
were identified that are out of scope for the v1.0 release but should be
recorded as accepted future directions. v1.0 is designated as the last release
with `requires-python = ">=3.8"` and will serve as the stable baseline for
users on older Python environments.

## Decision

### Python version strategy

- **v1.0.0** is released with `requires-python = ">=3.8"` as the final
  3.8-compatible version. This becomes the pinnable baseline for constrained
  environments.
- **The first release after v1.0** bumps to `requires-python = ">=3.11"`.
  3.11 is chosen over 3.9/3.10 because it is the realistic modern baseline
  (performance improvements, `tomllib` in stdlib, complete type system
  improvements), and the jump from 3.8 directly to 3.11 avoids a string of
  intermediate compatibility steps.
- Users on Python 3.8 environments pin with `pip install "engaku<1.1"` or
  `pip install "engaku==1.0.*"`. The README documents this.
- After the version bump, 3.9+ syntax (`str.removeprefix()`, `dict | dict`,
  `match/case`, `X | Y` type annotations) becomes available and the
  `copilot-instructions.md` constraint is updated accordingly.

### Learnings / transcript intelligence system

The gstack project demonstrates a viable pattern for per-project learnings
persistence: append-only JSONL at `~/.gstack/projects/{slug}/learnings.jsonl`,
written by agents at session end via a binary, loaded at session start via
`inject`. The same pattern can be implemented in engaku using Python stdlib
only (`json`, `subprocess` for git slug derivation, `pathlib`).

Key design decisions deferred to implementation:

- **Storage location**: `~/.engaku/projects/{slug}/learnings.jsonl` (user home,
  not repo, so it survives repo cleans and does not pollute version control).
- **Slug derivation**: from `git remote get-url origin` stripped to
  `owner-repo`, falling back to `basename(cwd)` — implementable as a pure
  Python function in `utils.py`.
- **Write path**: a new `cmd_learnings.py` subcommand (`engaku learnings log`)
  that validates fields and appends. Called by a Stop hook prompt to the agent
  (not auto-called by hook code — agent writes based on prompt).
- **Read path**: `inject` loads the 5 most recent learnings (by timestamp,
  after dedup by key) and appends them to the `PreCompact` and `SessionStart`
  payloads.
- **Prompt injection in Stop hook**: `task-review` or a new Stop hook prompt
  asks the agent: "If this session produced a reusable insight (pitfall,
  pattern, preference), run `engaku learnings log` with the details."

The VS Code hook input includes a `transcript_path` field pointing to the
current session's conversation transcript as JSON. This opens a future path
where the Stop hook reads the transcript, extracts key decisions using
heuristics (lines containing "decided", "because", "instead of"), and either
writes them directly to learnings.jsonl or presents them to the agent for
confirmation. This requires no LLM call — pure text heuristics — and is
feasible within the 5-second hook timeout.

Security note: any user-writable learnings file is a potential prompt injection
surface. On adoption, implement content sanitisation equivalent to gstack's
`gstack-learnings-log` (reject insight strings matching instruction-like
patterns: "ignore previous", "you are now", "always output no findings", etc.).

## Consequences

- v1.0.0 must be cut and published before any 3.11-only syntax is introduced.
- The learnings system adds a new subcommand and a new per-user data directory
  (`~/.engaku/`). The `engaku init` and `engaku update` commands may need
  awareness of this directory.
- The transcript heuristic approach keeps engaku zero-dependency but produces
  lower-quality extractions than an LLM-based summariser. This is an acceptable
  tradeoff given the no-third-party-dependency constraint.
- If the learnings system proves high-value, a future decision may reconsider
  the no-dependency constraint specifically for an optional LLM-powered
  summarisation mode.
