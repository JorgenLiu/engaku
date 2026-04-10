import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="engaku",
        description="AI persistent memory layer for VS Code Copilot",
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
        help="Output rules.md + overview.md as SessionStart hook JSON",
    )

    # engaku check-update
    subparsers.add_parser(
        "check-update",
        help="Check if code changed but knowledge files not updated (Stop hook)",
    )

    # engaku validate
    p_validate = subparsers.add_parser(
        "validate",
        help="Validate .ai/modules/*.md content quality",
    )
    p_validate.add_argument(
        "--recent",
        action="store_true",
        help="Only check files modified in the last 10 minutes",
    )

    # engaku log-read
    subparsers.add_parser(
        "log-read",
        help="Log .ai/ file access for PostToolUse hook metrics",
    )

    # engaku prompt-check
    subparsers.add_parser(
        "prompt-check",
        help="Detect potential rule/constraint in user prompt (UserPromptSubmit hook)",
    )

    # engaku apply
    subparsers.add_parser(
        "apply",
        help="Apply .ai/engaku.json model config to .github/agents/ frontmatter",
    )

    # engaku stats
    p_stats = subparsers.add_parser(
        "stats",
        help="Show knowledge coverage, freshness, and access log summary",
    )
    p_stats.add_argument(
        "--history",
        action="store_true",
        help="Show recent git commit history for each knowledge file",
    )

    args = parser.parse_args()

    if args.command == "init":
        from engaku.cmd_init import run
        sys.exit(run())
    elif args.command == "inject":
        from engaku.cmd_inject import run
        sys.exit(run())
    elif args.command == "check-update":
        from engaku.cmd_check_update import run
        sys.exit(run())
    elif args.command == "validate":
        from engaku.cmd_validate import run
        sys.exit(run(recent=args.recent))
    elif args.command == "log-read":
        from engaku.cmd_log_read import run
        sys.exit(run())
    elif args.command == "prompt-check":
        from engaku.cmd_prompt_check import run
        sys.exit(run())
    elif args.command == "apply":
        from engaku.cmd_apply import run
        sys.exit(run())
    elif args.command == "stats":
        from engaku.cmd_stats import run
        sys.exit(run(history=args.history))
