import json
import os
import sys

from engaku.utils import parse_frontmatter, parse_paths_from_frontmatter, read_hook_input


def _parse_paths_frontmatter(filepath):
    """Backward-compat wrapper used by existing tests."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return []
    fm, _ = parse_frontmatter(content)
    return parse_paths_from_frontmatter(fm) if fm is not None else []


def _build_module_index(cwd):
    """Scan .ai/modules/*.md and return Markdown table string, or empty string."""
    modules_dir = os.path.join(cwd, ".ai", "modules")
    if not os.path.isdir(modules_dir):
        return ""
    try:
        entries = sorted(os.listdir(modules_dir))
    except OSError:
        return ""
    md_files = [e for e in entries if e.endswith(".md")]
    if not md_files:
        return ""
    rows = []
    for filename in md_files:
        filepath = os.path.join(modules_dir, filename)
        module_name = filename[:-3]
        rel_path = ".ai/modules/" + filename
        try:
            with open(filepath, "r", encoding="utf-8") as _f:
                _content = _f.read()
        except OSError:
            _content = ""
        _fm, _ = parse_frontmatter(_content)
        paths = parse_paths_from_frontmatter(_fm) if _fm is not None else []
        paths_str = ", ".join(paths) if paths else "(unscoped)"
        rows.append((module_name, paths_str, rel_path))
    lines = [
        "## Module Knowledge Index",
        "| Module | Paths | Knowledge File |",
        "|--------|-------|----------------|",
    ]
    for module_name, paths_str, rel_path in rows:
        lines.append("| {} | {} | {} |".format(module_name, paths_str, rel_path))
    lines.append("")
    lines.append(
        "Before modifying files listed above, read the corresponding knowledge file."
    )
    return "\n".join(lines)


def run(cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    ai_dir = os.path.join(cwd, ".ai")
    rules_path = os.path.join(ai_dir, "rules.md")
    overview_path = os.path.join(ai_dir, "overview.md")

    parts = []

    if os.path.isfile(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            parts.append(content)

    if os.path.isfile(overview_path):
        with open(overview_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            parts.append(content)

    module_index = _build_module_index(cwd)
    if module_index:
        parts.append(module_index)

    additional_context = "\n\n---\n\n".join(parts)

    # Determine event from stdin so PreCompact can use a different output format.
    # PreCompact uses the common output format (systemMessage), not hookSpecificOutput.
    hook_input = read_hook_input()
    event = hook_input.get("hookEventName", "SessionStart")

    if event == "PreCompact":
        output = {"systemMessage": additional_context}
    else:
        # SessionStart (and default)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": additional_context,
            }
        }

    sys.stdout.write(json.dumps(output, ensure_ascii=False))
    sys.stdout.flush()
    return 0
