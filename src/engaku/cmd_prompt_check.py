"""
engaku prompt-check
UserPromptSubmit hook: detect if a user prompt may contain a new project
rule or constraint. Outputs a systemMessage reminder when keywords match.
Always exits 0 (informational only, never blocks).
"""
import json
import sys

from engaku.utils import read_hook_input

_KEYWORDS = [
    "从现在开始",
    "不要用",
    "always",
    "never",
    "规则",
    "rule",
    "preference",
    "constraint",
    "禁止",
    "必须",
    "要求",
]


def run():
    hook_input = read_hook_input()
    prompt = hook_input.get("prompt", "")
    if not isinstance(prompt, str):
        prompt = ""

    prompt_lower = prompt.lower()
    matched = any(kw.lower() in prompt_lower for kw in _KEYWORDS)

    if matched:
        output = {
            "systemMessage": (
                "The user's prompt may contain a new project rule or constraint. "
                "If confirmed, update .ai/rules.md after completing the task."
            )
        }
    else:
        output = {}

    sys.stdout.write(json.dumps(output))
    return 0
