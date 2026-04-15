import json
import os
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
        return (title, unchecked)
    return None


def run(cwd=None):
    if cwd is None:
        cwd = os.getcwd()
    ai_dir = os.path.join(cwd, ".ai")
    overview_path = os.path.join(ai_dir, "overview.md")

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
        title, unchecked = active_task
        task_lines = ["<active-task>", "## {}".format(title)]
        task_lines.extend(unchecked)
        task_lines.append("</active-task>")
        parts.append("\n".join(task_lines))

    additional_context = "\n\n".join(parts)

    # Determine event from stdin so PreCompact can use a different output format.
    # PreCompact uses the common output format (systemMessage), not hookSpecificOutput.
    hook_input = read_hook_input()
    event = hook_input.get("hookEventName", "SessionStart")

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


def main(argv=None):
    sys.exit(run())
