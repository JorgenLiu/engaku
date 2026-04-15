---
applyTo: "src/engaku/cmd_*.py"
---
Hook command conventions for the engaku project.

Each `cmd_*.py` module implements a `run()` and `main()` entry point. `run()` reads JSON from stdin via `read_hook_input()` from `engaku.utils`, and writes JSON responses to stdout. Hook commands must always exit 0 unless intentionally blocking a Stop hook (return `hookSpecificOutput` with `decision: block`). Always check `hook_input.get("stop_hook_active", False)` at the start of `run()` to prevent execution loops. `cli.py` routes to each command via lazy import — add new commands there when adding `cmd_*.py` files.
