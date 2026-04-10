"""
engaku.utils
Shared utility functions used by multiple cmd_*.py modules.
All functions are public (no leading underscore).
"""
import json
import os
import sys

from engaku.constants import (
    CONFIG_FILE,
    IGNORED_DIR_NAMES,
    IGNORED_DIR_SUFFIXES,
    IGNORED_EXTENSIONS,
    IGNORED_FILENAMES,
    MAX_CHARS,
)


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


def is_code_file(path):
    """Return True if path represents a meaningful source change worth tracking."""
    norm = path.replace(os.sep, "/")
    parts = norm.split("/")
    # Check every directory component (all but the last element, which is the filename)
    for part in parts[:-1]:
        if part in IGNORED_DIR_NAMES:
            return False
        for suffix in IGNORED_DIR_SUFFIXES:
            if part.endswith(suffix):
                return False
    basename = parts[-1]
    if basename in IGNORED_FILENAMES:
        return False
    _, ext = os.path.splitext(basename)
    return ext.lower() not in IGNORED_EXTENSIONS


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
    cu = raw.get("check_update", {})
    return {
        "agents": raw.get("agents", {}),
        "max_chars": raw.get("max_chars", MAX_CHARS),
        "check_update": {
            "ignore": cu.get("ignore", []),
            "uncovered_action": cu.get("uncovered_action", "warn"),
        },
    }


# ── transcript-based edit detection ─────────────────────────────────────────

_EDIT_TOOL_NAMES = frozenset({
    "create_file",
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "insert_edit_into_file",
    "apply_patch",
})


def _extract_paths_from_args(tool_name, args):
    """Extract file path(s) from parsed tool arguments dict.
    Returns list of path strings (may be empty on unexpected shape).
    """
    if not isinstance(args, dict):
        return []
    paths = []
    if tool_name in ("create_file", "replace_string_in_file", "insert_edit_into_file"):
        p = args.get("filePath") or args.get("path")
        if isinstance(p, str):
            paths.append(p)
    elif tool_name == "multi_replace_string_in_file":
        for r in args.get("replacements") or []:
            if isinstance(r, dict):
                fp = r.get("filePath")
                if isinstance(fp, str):
                    paths.append(fp)
    elif tool_name == "apply_patch":
        import re
        text = args.get("input", "")
        if isinstance(text, str):
            for m in re.finditer(
                r"^\*\*\* (?:Update|Add|Delete) File: (.+)$", text, re.MULTILINE
            ):
                paths.append(m.group(1).strip())
    return paths


def parse_transcript_edits(transcript_path, cwd, last_turn_only=False):
    """Parse a VS Code transcript JSONL file and return a deduplicated list of
    successfully-edited file paths, expressed as paths relative to cwd.

    Only tool calls that both (a) used an edit tool and (b) completed with
    success=true are included. Failed edits and read-only tool calls are ignored.

    If last_turn_only is True, only edits made after the last user.message event
    are returned (i.e. the current turn only).

    Returns [] on any I/O or parse error (never raises).
    """
    pending = {}   # {toolCallId: [abs_paths...]}
    result = []
    seen = set()

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                evt_type = event.get("type")

                if last_turn_only and evt_type == "user.message":
                    # Reset: discard all edits from previous turns
                    pending.clear()
                    result.clear()
                    seen.clear()
                    continue

                if evt_type == "tool.execution_start":
                    data = event.get("data", {})
                    tool_name = data.get("toolName")
                    if tool_name not in _EDIT_TOOL_NAMES:
                        continue
                    paths = _extract_paths_from_args(tool_name, data.get("arguments"))
                    if paths:
                        pending[data.get("toolCallId")] = paths

                elif evt_type == "tool.execution_complete":
                    data = event.get("data", {})
                    call_id = data.get("toolCallId")
                    if call_id not in pending:
                        continue
                    if not data.get("success", False):
                        del pending[call_id]
                        continue
                    for p in pending.pop(call_id):
                        rel = relative_to_cwd(p, cwd)
                        if rel not in seen:
                            seen.add(rel)
                            result.append(rel)
    except OSError:
        return []

    return result
