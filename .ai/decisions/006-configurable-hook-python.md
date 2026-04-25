---
id: 006
title: Configurable Python interpreter for Engaku hooks
status: accepted
date: 2026-04-25
related_task: 2026-04-25-refresh-mcp-server-config
---

## Context

Engaku agent hooks currently execute commands such as `engaku inject`, `engaku prompt-check`, and `engaku task-review` from agent frontmatter. On some machines the default/system Python installation can contain Engaku but fail to execute it because of permissions or PATH constraints, while a virtual environment Python can run Engaku successfully. Editing every generated agent file by hand would be fragile because `engaku update` overwrites managed agent templates.

## Decision

Add a top-level `python` option to `.ai/engaku.json`. When the option is missing, `null`, or empty, Engaku keeps the current default hook command form, `engaku <subcommand>`. When the option is set, `engaku apply` rewrites Engaku-managed hook commands in `.github/agents/*.agent.md` to `<configured-python> -m engaku <subcommand>`, leaving unrelated custom hook commands unchanged.

## Consequences

Users who need virtualenv-backed hooks can set `python` to a relative or absolute interpreter path such as `.venv/bin/python`, then run that interpreter with `-m engaku apply` once to rewrite hook commands. Existing projects keep their current behavior unless they opt in. Future hook command changes should flow through `engaku apply`, not manual edits to generated agent frontmatter.
