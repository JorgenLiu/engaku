---
applyTo: "tests/**"
---
Test conventions for this project.

Tests use Python's stdlib `unittest` module with `sys.path.insert` for the src layout — no pytest fixtures. Each test file corresponds to one source module. Stdin is mocked with `io.StringIO`; stdout and stderr are captured by temporarily replacing `sys.stdout`/`sys.stderr`. Tests are self-contained and clean up any temp directories in `tearDown`.

<!-- Add project-specific test conventions here. -->
