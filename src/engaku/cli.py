import argparse
import sys

from engaku import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="engaku",
        description="AI persistent memory layer for VS Code Copilot",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # engaku init
    subparsers.add_parser(
        "init",
        help="Initialize .ai/ knowledge structure and .github/ hooks/agents in target repo",
    )

    # engaku inject
    subparsers.add_parser(
        "inject",
        help="Inject .ai/overview.md + active-task context (SessionStart/PreCompact/SubagentStart hook)",
    )

    # engaku prompt-check
    subparsers.add_parser(
        "prompt-check",
        help="Detect potential rule/constraint in user prompt (UserPromptSubmit hook)",
    )

    # engaku task-review
    subparsers.add_parser(
        "task-review",
        help="Detect all-complete task plans and emit handoff reminder (Stop hook)",
    )

    # engaku apply
    subparsers.add_parser(
        "apply",
        help="Apply .ai/engaku.json model config to .github/agents/ frontmatter",
    )

    # engaku update
    subparsers.add_parser(
        "update",
        help="Update .github/skills/ from bundled templates (overwrites existing)",
    )

    args = parser.parse_args()

    if args.command == "init":
        from engaku.cmd_init import run
        sys.exit(run())
    elif args.command == "inject":
        from engaku.cmd_inject import run
        sys.exit(run())
    elif args.command == "prompt-check":
        from engaku.cmd_prompt_check import run
        sys.exit(run())
    elif args.command == "task-review":
        from engaku.cmd_task_review import run
        sys.exit(run())
    elif args.command == "apply":
        from engaku.cmd_apply import run
        sys.exit(run())
    elif args.command == "update":
        from engaku.cmd_update import run
        sys.exit(run())
