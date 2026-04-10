---
paths:
  - src/engaku/cmd_validate.py
  - src/engaku/cmd_check_update.py
  - src/engaku/cmd_stats.py
  - tests/test_validate.py
  - tests/test_check_update.py

---
## Overview
This module documents message-length validation and the CLI commands and tests that
rely on the configured `max_chars` threshold.

- `src/engaku/cmd_validate.py` implements validators that enforce the configured maximum
  message length and return structured results for CLI use.
- `src/engaku/cmd_check_update.py` loads configuration values, including the `max_chars`
  threshold used by validators.
- `src/engaku/cmd_stats.py` reports message-length statistics and related metrics.
- `tests/test_validate.py` asserts validation fails when input exceeds the configured limit.
- `tests/test_check_update.py` verifies configuration loading and that the `max_chars`
  default is present and surfaced to commands.
