"""
engaku update
Sync .github/agents/ and .github/skills/ from the latest bundled templates,
then auto-apply engaku.json model config.

Overwrites all agent and skill files managed by engaku with their latest
bundled versions. Never touches .ai/ files, .github/copilot-instructions.md,
or .github/instructions/ (those are user-owned).

Usage:
  engaku update
"""
import os
import shutil
import subprocess
import sys

_SKILLS = (
    "systematic-debugging",
    "verification-before-completion",
    "frontend-design",
    "proactive-initiative",
    "mcp-builder",
    "doc-coauthoring",
    "brainstorming",
)

_AGENTS = (
    "dev.agent.md",
    "planner.agent.md",
    "reviewer.agent.md",
    "scanner.agent.md",
)


def _templates_dir():
    return os.path.join(os.path.dirname(__file__), "templates")


def _is_git_repo(cwd):
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.returncode == 0
    except OSError:
        return False


def _force_copy(src, dst, out):
    """Copy src to dst, always overwriting. Creates parent dirs as needed.

    Reports [update] if dst already existed, [create] if it did not.
    """
    existed = os.path.exists(dst)
    dst_dir = os.path.dirname(dst)
    if dst_dir and not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    shutil.copy2(src, dst)
    action = "[update]" if existed else "[create]"
    out.append("{}  {}".format(action, dst))


def run(cwd=None):
    if cwd is None:
        cwd = os.getcwd()

    if not _is_git_repo(cwd):
        sys.stderr.write(
            "Error: {} is not a git repository.\n"
            "Run `git init` first, then re-run `engaku update`.\n".format(cwd)
        )
        return 1

    tpl = _templates_dir()
    out = []

    # ── .github/agents/ ──────────────────────────────────────────────────────
    agents_dir = os.path.join(cwd, ".github", "agents")
    for name in _AGENTS:
        _force_copy(
            os.path.join(tpl, "agents", name),
            os.path.join(agents_dir, name),
            out,
        )

    # ── .github/skills/ ──────────────────────────────────────────────────────
    skills_dir = os.path.join(cwd, ".github", "skills")
    for skill in _SKILLS:
        _force_copy(
            os.path.join(tpl, "skills", skill, "SKILL.md"),
            os.path.join(skills_dir, skill, "SKILL.md"),
            out,
        )

    # ── .vscode/settings.json ── ensure hook setting is present ─────────────
    from engaku.cmd_init import _ensure_vscode_setting
    _ensure_vscode_setting(cwd, "chat.useCustomAgentHooks", True, out)

    for line in out:
        sys.stdout.write(line + "\n")

    updated = sum(1 for l in out if l.startswith("[update]"))
    created = sum(1 for l in out if l.startswith("[create]"))
    sys.stdout.write(
        "\nDone. {} file(s) updated, {} created.\n".format(updated, created)
    )

    # ── auto-apply engaku.json model config ───────────────────────────────────
    config_path = os.path.join(cwd, ".ai", "engaku.json")
    if os.path.isfile(config_path):
        from engaku.cmd_apply import run as apply_run
        apply_run(cwd)

    return 0


def main(argv=None):
    sys.exit(run())
