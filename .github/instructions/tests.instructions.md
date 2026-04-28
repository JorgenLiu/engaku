---
applyTo: "tests/**"
---
Test conventions for the engaku project.

Tests use Python's stdlib `unittest` module. Each test file covers one CLI subcommand — one test file per `cmd_*.py`, named `test_init.py`, `test_apply.py`, `test_update.py`, etc. (not `test_cmd_*.py`). The test files use `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))` for the src layout; no pytest, no third-party fixtures. Tests clean up temp directories in `tearDown`.

Module-level imports are acceptable when the module has no optional runtime state at import time. For hook-backed commands (`inject`, `prompt-check`, `task-review`), mock stdin with `io.StringIO(json.dumps(hook_input))`, capture stdout and stderr by temporarily replacing `sys.stdout`/`sys.stderr`, and restore streams in a `finally` block.
