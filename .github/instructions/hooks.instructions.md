---
applyTo: "src/engaku/cmd_*.py"
---
# Command Modules

Every `cmd_*.py` exposes `run()` and `main()`. `cli.py` lazy-imports each subcommand and routes the call — register new commands there.

**Hook-backed commands** (`inject`, `prompt-check`, `task-review`):
- Invoked by VS Code Agent Hooks.
- Read JSON from stdin via `read_hook_input()` from `engaku.utils`.
- Write JSON responses to stdout.
- Always exit 0 unless intentionally blocking a Stop hook (return `hookSpecificOutput` with `decision: block`).
- Check `hook_input.get("stop_hook_active", False)` at the start of `run()` to prevent loops.

**Ordinary CLI commands** (`init`, `apply`, `update`):
- Invoked directly by users.
- May use stdout/stderr for user-facing output and exit non-zero on errors.
- Do NOT call `read_hook_input()` or emit hook-compatible JSON.
