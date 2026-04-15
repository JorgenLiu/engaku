---
applyTo: "src/**/cmd_*.py"
---
Hook command conventions for this project.

Each hook command (`cmd_*.py`) implements a `run()` and `main()` entry point. The `run()` function reads JSON from stdin via `read_hook_input()` and writes JSON responses to stdout. Hook commands must always exit 0 unless intentionally blocking a Stop hook (use `hookSpecificOutput` with `decision: block`). Always check the `stop_hook_active` guard at the start of `run()` to prevent execution loops.

<!-- Add project-specific hook command conventions here. -->
