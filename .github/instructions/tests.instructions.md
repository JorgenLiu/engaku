---
applyTo: "tests/**"
---
# Tests

Stdlib `unittest` only. One test file per `cmd_*.py`, named `test_init.py`, `test_apply.py`, `test_update.py`, etc. (NOT `test_cmd_*.py`).

- Use `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))` for the src layout.
- No pytest, no third-party fixtures.
- Clean up temp dirs in `tearDown`.
- Module-level imports are OK when the module has no optional runtime state at import.
- For hook-backed commands (`inject`, `prompt-check`, `task-review`): mock stdin with `io.StringIO(json.dumps(hook_input))`, capture stdout/stderr by replacing `sys.stdout`/`sys.stderr`, and restore in a `finally` block.
