---
applyTo: "tests/**"
---
Test conventions for the engaku project.

Tests use Python's stdlib `unittest` module with `sys.path.insert(0, ".../src")` for the src layout — no pytest, no third-party fixtures. Each test file covers one source module (`test_cmd_*.py` per `cmd_*.py`). Stdin is mocked with `io.StringIO(json.dumps(hook_input))`; stdout and stderr are captured by temporarily replacing `sys.stdout`/`sys.stderr` and restoring them in a `finally` block. Tests clean up temp directories in `tearDown`. Do not import engaku at module level in tests — use inline imports inside test methods when needed to avoid import errors from missing optional state.
