"""
engaku.utils
Shared utility functions used by multiple cmd_*.py modules.
All functions are public (no leading underscore).
"""
import json
import os
import sys

from engaku.constants import CONFIG_FILE


def read_hook_input():
    """Read and parse JSON from stdin (VS Code hook input). Returns {} if none."""
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read().strip()
    except OSError:
        return {}
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    return {}


def parse_frontmatter(content):
    """Split YAML frontmatter from body content.

    Returns (frontmatter_str, body_str). If no valid frontmatter is found,
    returns (None, content). Frontmatter must begin at the first line as '---'
    and be closed by a subsequent '---' on its own line.
    """
    if not content.startswith("---\n"):
        return None, content
    close = content.find("\n---", 4)
    if close == -1:
        return None, content
    # Closing --- must be followed by a newline or end-of-string, not more text
    after_close = content[close + 4:]
    if after_close and after_close[0] not in ("\n", "\r"):
        return None, content
    fm = content[4:close]
    body = after_close.lstrip("\n\r")
    return fm, body


def parse_paths_from_frontmatter(fm_str):
    """Extract the paths: list from a YAML frontmatter string.

    Simple line-by-line parser; does not require a YAML library.
    Returns [] if no paths: key is found.
    """
    paths = []
    in_paths = False
    for line in fm_str.splitlines():
        stripped = line.strip()
        if stripped == "paths:":
            in_paths = True
            continue
        if in_paths:
            if stripped.startswith("- "):
                paths.append(stripped[2:].strip())
            elif stripped and not stripped.startswith("#"):
                in_paths = False  # another key started
    return paths


def is_ai_file(path, cwd):
    """Return True if path resolves to inside the .ai/ directory."""
    if not path:
        return False
    abs_path = os.path.normpath(
        os.path.join(cwd, path) if not os.path.isabs(path) else path
    )
    ai_dir = os.path.normpath(os.path.join(cwd, ".ai")) + os.sep
    return abs_path.startswith(ai_dir)


def relative_to_cwd(path, cwd):
    """Return path as a relative path from cwd. Falls back to original on error."""
    abs_path = os.path.normpath(
        os.path.join(cwd, path) if not os.path.isabs(path) else path
    )
    try:
        return os.path.relpath(abs_path, cwd)
    except ValueError:
        return path


def load_config(cwd):
    """Read .ai/engaku.json and return a merged config dict with defaults.

    All keys are guaranteed to be present in the returned dict.
    Missing keys in the JSON file fall back to framework defaults.
    Invalid JSON is silently ignored (all defaults used).
    """
    config_path = os.path.join(cwd, CONFIG_FILE)
    raw = {}
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw = json.loads(f.read())
        except (OSError, ValueError):
            pass
    return {
        "agents": raw.get("agents", {}),
    }

