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
    "chrome-devtools",
    "context7",
    "database",
)

_AGENTS = (
    "coder.agent.md",
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

    # ── .github/instructions/ ── create lessons stub if missing ──────────────
    from engaku.cmd_init import _copy_template
    _copy_template(
        os.path.join(tpl, "instructions", "lessons.instructions.md"),
        os.path.join(cwd, ".github", "instructions", "lessons.instructions.md"),
        out,
    )

    # ── .vscode/settings.json ── ensure hook setting is present ─────────────
    from engaku.cmd_init import _ensure_vscode_setting
    _ensure_vscode_setting(cwd, "chat.useCustomAgentHooks", True, out)

    # ── .vscode/mcp.json ── merge new server entries if file exists ──────────
    import json
    mcp_path = os.path.join(cwd, ".vscode", "mcp.json")
    if os.path.isfile(mcp_path):
        tpl_mcp_path = os.path.join(tpl, "mcp.json")
        try:
            with open(mcp_path, "r", encoding="utf-8") as f:
                user_mcp = json.load(f)
            with open(tpl_mcp_path, "r", encoding="utf-8") as f:
                tpl_mcp = json.load(f)
        except (ValueError, OSError):
            user_mcp = None
            tpl_mcp = None

        if user_mcp is not None and tpl_mcp is not None:
            changed = False
            # Merge servers
            user_servers = user_mcp.setdefault("servers", {})
            for key, val in tpl_mcp.get("servers", {}).items():
                if key not in user_servers:
                    user_servers[key] = val
                    changed = True
            # Merge inputs
            user_inputs = user_mcp.setdefault("inputs", [])
            existing_ids = set()
            for inp in user_inputs:
                if isinstance(inp, dict) and "id" in inp:
                    existing_ids.add(inp["id"])
            for inp in tpl_mcp.get("inputs", []):
                if isinstance(inp, dict) and inp.get("id") not in existing_ids:
                    user_inputs.append(inp)
                    changed = True
            if changed:
                with open(mcp_path, "w", encoding="utf-8") as f:
                    json.dump(user_mcp, f, indent=2)
                    f.write("\n")
                out.append("[update]  {}".format(mcp_path))
            else:
                out.append("[skip]    {}".format(mcp_path))

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
