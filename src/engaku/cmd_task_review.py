"""
engaku task-review
Stop hook: detect when all tasks in an in-progress plan are checked,
emit systemMessage to use the Verify Tasks handoff.
"""
import json
import os
import re
import sys

from engaku.utils import parse_frontmatter, read_hook_input


def _extract_tasks_section(body):
    """Extract content of ## Tasks section (up to next ## heading or EOF)."""
    match = re.search(
        r'^## Tasks\s*\n(.*?)(?=^## |\Z)', body, re.MULTILINE | re.DOTALL
    )
    return match.group(1) if match else ""


def _all_tasks_checked(tasks_section):
    """Return True if tasks_section has at least one [x] and no [ ] entries."""
    checked = re.findall(r'^- \[x\]', tasks_section, re.MULTILINE)
    unchecked = re.findall(r'^- \[ \]', tasks_section, re.MULTILINE)
    return bool(checked) and not unchecked


def _get_frontmatter_status(fm_str):
    """Return the value of the status: key from a raw YAML frontmatter string."""
    for line in fm_str.splitlines():
        stripped = line.strip()
        if stripped.startswith("status:"):
            return stripped[len("status:"):].strip()
    return None


def _find_completed_task_file(cwd):
    """Return relative path of first in-progress task file with all tasks checked.

    Scans .ai/tasks/*.md sorted descending by filename. Returns None if none found.
    """
    tasks_dir = os.path.join(cwd, ".ai", "tasks")
    if not os.path.isdir(tasks_dir):
        return None

    filenames = sorted(
        [f for f in os.listdir(tasks_dir) if f.endswith(".md")],
        reverse=True,
    )

    for filename in filenames:
        path = os.path.join(tasks_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue

        fm, body = parse_frontmatter(content)
        if fm is None or _get_frontmatter_status(fm) != "in-progress":
            continue

        tasks_section = _extract_tasks_section(body)
        if _all_tasks_checked(tasks_section):
            return os.path.join(".ai", "tasks", filename)

    return None


def run():
    hook_input = read_hook_input()

    if hook_input.get("stop_hook_active", False):
        return 0

    cwd = os.getcwd()
    task_file = _find_completed_task_file(cwd)
    if task_file is None:
        return 0

    output = {
        "systemMessage": (
            "All tasks in {} are marked complete. "
            "Click 'Verify Tasks (1 premium request)' to run verification."
        ).format(task_file)
    }
    sys.stdout.write(json.dumps(output))
    return 0


def main(argv=None):
    sys.exit(run())
