---
applyTo: "src/engaku/cmd_*.py"
---
Command-module conventions for the engaku project.

Every `cmd_*.py` module exposes a `run()` and a `main()` entry point. `cli.py` lazy-imports each subcommand and routes the call — add new commands there when adding a `cmd_*.py` file.

**Hook-backed commands** (`inject`, `prompt-check`, `task-review`) are invoked by VS Code Agent Hooks. They read JSON from stdin via `read_hook_input()` from `engaku.utils` and write JSON responses to stdout. They must always exit 0 unless intentionally blocking a Stop hook (return `hookSpecificOutput` with `decision: block`). Check `hook_input.get("stop_hook_active", False)` at the start of `run()` to prevent execution loops.

**Ordinary CLI commands** (`init`, `apply`, `update`) are invoked directly by users. They may use normal stdout/stderr for user-facing output and may exit non-zero to signal errors to the user. They do not call `read_hook_input()` and do not need to emit hook-compatible JSON.
