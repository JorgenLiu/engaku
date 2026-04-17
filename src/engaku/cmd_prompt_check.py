"""
engaku prompt-check
UserPromptSubmit hook: detect if a user prompt may contain a new project
rule or constraint, and inject the current active-task unchecked steps so
the agent always knows what to do next. Always exits 0 (never blocks).
"""
import json
import os
import re
import sys

from engaku.utils import parse_frontmatter, read_hook_input

# Simple substring keywords (specific enough to not require context).
_SIMPLE_KEYWORDS = [
    "从现在开始",
    "不要用",
    "规则",
    "rule",
    "preference",
    "constraint",
    "禁止",
    "必须",
    "要求",
]

# "always/never" only match when followed by a directive verb/word.
_PHRASE_PATTERNS = [
    re.compile(
        r"\balways\s+(use|run|add|return|call|follow|keep|write|check|include"
        r"|set|ensure|prefer|apply|avoid|wrap|handle|be|import|define)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bnever\s+(use|import|add|return|call|write|include|do|put|access"
        r"|define|hardcode|push|commit)\b",
        re.IGNORECASE,
    ),
]


def _is_rule_prompt(prompt):
    prompt_lower = prompt.lower()
    if any(kw.lower() in prompt_lower for kw in _SIMPLE_KEYWORDS):
        return True
    return any(p.search(prompt) for p in _PHRASE_PATTERNS)


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

    hook_input = read_hook_input()
    prompt = hook_input.get("prompt", "")
    if not isinstance(prompt, str):
        prompt = ""

    parts = []

    if _is_rule_prompt(prompt):
        parts.append(
            "The user's prompt may contain a new project rule or constraint. "
            "If confirmed, update .github/copilot-instructions.md after completing the task."
        )

    active_task = _find_active_task(cwd)
    if active_task:
        title, unchecked = active_task
        task_lines = ["Active task: {}".format(title)]
        task_lines.extend(unchecked)
        parts.append("\n".join(task_lines))

    if parts:
        output = {"systemMessage": "\n\n".join(parts)}
    else:
        output = {}

    sys.stdout.write(json.dumps(output))
    return 0


def main(argv=None):
    sys.exit(run())

