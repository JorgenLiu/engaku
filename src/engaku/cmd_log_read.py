"""
engaku log-read
PostToolUse Hook: when a .ai/ file is read, append an entry to .ai/access.log.

VS Code passes hook JSON to stdin. Shape (subset we care about):
{
    "tool_input": {"filePath": "..."} | {"path": "..."},
    "session_id": "abc123"
}

Usage (in .vscode/agents.json hooks section):
  "command": "engaku log-read",
  "hookEvent": "PostToolUse",
  "toolNames": ["read_file"]
"""
import datetime
import os
import sys

from engaku.constants import ACCESS_LOG
from engaku.utils import is_ai_file, read_hook_input, relative_to_cwd

# Backward-compat alias used by existing tests.
_is_ai_file = is_ai_file


def _extract_file_path(data):
    """Extract the file path from hook JSON tool_input."""
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return None
    return tool_input.get("filePath") or tool_input.get("path")


def _append_access_log(cwd, rel_path, session_id):
    log_path = os.path.join(cwd, ACCESS_LOG)
    log_dir = os.path.dirname(log_path)
    if not os.path.isdir(log_dir):
        return  # .ai/ dir doesn't exist, bail silently
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = "{}\t{}\t{}\n".format(ts, rel_path, session_id or "")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


def run(argv=None, cwd=None, stdin_data=None):
    if cwd is None:
        cwd = os.getcwd()

    if stdin_data is None:
        data = read_hook_input()
    else:
        data = stdin_data

    file_path = _extract_file_path(data)

    if file_path and is_ai_file(file_path, cwd):
        rel_path = relative_to_cwd(file_path, cwd)
        session_id = data.get("session_id", "")
        try:
            _append_access_log(cwd, rel_path, session_id)
        except OSError:
            pass  # Never block; log failure is non-fatal

    return 0


def main(argv=None):
    sys.exit(run(argv))
