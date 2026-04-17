import json
import os
import re
import sys

from engaku.utils import parse_frontmatter, read_hook_input


def _find_active_task(cwd):
    """Scan .ai/tasks/*.md for first file with status: in-progress.

    Returns (title, unchecked_lines) tuple or None.
    """
    tasks_dir = os.path.join(cwd, ".ai", "tasks")
    if not os.path.isdir(tasks_dir):
        return None
    try:
        entries = sorted(os.listdir(tasks_dir))
    except OSError:
        return None
    for filename in entries:
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(tasks_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        fm, body = parse_frontmatter(content)
        if fm is None:
            continue
        status = None
        title = None
        for line in fm.splitlines():
            if line.startswith("status:"):
                status = line[len("status:"):].strip()
            elif line.startswith("title:"):
                title = line[len("title:"):].strip()
        if status != "in-progress":
            continue
        if title is None:
            title = filename[:-3]
        unchecked = [l for l in body.splitlines() if l.strip().startswith("- [ ]")]
        return (title, unchecked, body)
    return None


def _extract_task_compact_body(body):
    """Extract key sections and all checkbox lines for PreCompact injection."""
    parts = []
    for heading in ("Background", "Design", "File Map"):
        m = re.search(
            r"^## {}\s*\n.*?(?=^## |\Z)".format(re.escape(heading)),
            body,
            re.MULTILINE | re.DOTALL,
        )
        if m:
            parts.append(m.group(0).rstrip())
    checkbox_lines = [
        l for l in body.splitlines()
        if re.match(r"\s*- \[[x ]\]", l)
    ]
    if checkbox_lines:
        parts.append("\n".join(checkbox_lines))
    return "\n\n".join(parts) if parts else ""


def run(cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    ai_dir = os.path.join(cwd, ".ai")
    overview_path = os.path.join(ai_dir, "overview.md")

    hook_input = read_hook_input()
    event = hook_input.get("hookEventName", "SessionStart")

    context_parts = []

    if os.path.isfile(overview_path):
        with open(overview_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            context_parts.append(content)

    inner = "\n\n---\n\n".join(context_parts)
    project_context = "<project-context>\n{}\n</project-context>".format(inner) if inner else ""

    parts = []
    if project_context:
        parts.append(project_context)

    active_task = _find_active_task(cwd)
    if active_task:
        title, unchecked, body = active_task
        if event == "PreCompact":
            compact_body = _extract_task_compact_body(body)
            task_lines = ["<active-task>", "## {}".format(title)]
            if compact_body:
                task_lines.append(compact_body)
            task_lines.append("</active-task>")
        else:
            task_lines = ["<active-task>", "## {}".format(title)]
            task_lines.extend(unchecked)
            task_lines.append("</active-task>")
        parts.append("\n".join(task_lines))

    additional_context = "\n\n".join(parts)

    if event == "PreCompact":
        output = {"systemMessage": additional_context}
    elif event == "SubagentStart":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": additional_context,
            }
        }
    else:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": additional_context,
            }
        }

    sys.stdout.write(json.dumps(output, ensure_ascii=False))
    sys.stdout.flush()
    return 0


def main(argv=None):
    sys.exit(run())
