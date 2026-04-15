"""
engaku init
Initialize .ai/ knowledge structure and .github/ hooks + agents in the current
git repository.

Files created (never overwritten if they already exist):
  .ai/
    overview.md
    engaku.json
    decisions/.gitkeep
    tasks/.gitkeep
    docs/.gitkeep
  .github/
    agents/
      dev.agent.md
      planner.agent.md
      reviewer.agent.md
      scanner.agent.md
    instructions/
      hooks.instructions.md
      tests.instructions.md
      templates.instructions.md
    skills/
      systematic-debugging/SKILL.md
      verification-before-completion/SKILL.md
      frontend-design/SKILL.md
      proactive-initiative/SKILL.md
    copilot-instructions.md
"""
import os
import shutil
import subprocess
import sys


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


def _copy_template(src, dst, out):
    """Copy src to dst unless dst already exists. Prints [create] or [skip]."""
    if os.path.exists(dst):
        out.append("[skip]   {}".format(dst))
        return
    dst_dir = os.path.dirname(dst)
    if dst_dir and not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)
    shutil.copy2(src, dst)
    out.append("[create] {}".format(dst))


def _touch_gitkeep(path, out):
    """Create an empty .gitkeep inside path, creating path if needed."""
    if not os.path.isdir(path):
        os.makedirs(path)
    gk = os.path.join(path, ".gitkeep")
    if os.path.exists(gk):
        out.append("[skip]   {}".format(gk))
    else:
        open(gk, "w").close()
        out.append("[create] {}".format(gk))


def _ensure_vscode_setting(cwd, key, value, out):
    """Merge a single key/value into .vscode/settings.json, creating it if needed.

    Uses simple JSON load/dump so existing user settings are preserved.
    Skips if the key is already set to the desired value.
    """
    import json
    vscode_dir = os.path.join(cwd, ".vscode")
    settings_path = os.path.join(vscode_dir, "settings.json")

    if not os.path.isdir(vscode_dir):
        os.makedirs(vscode_dir)

    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (ValueError, OSError):
            settings = {}

    if settings.get(key) == value:
        out.append("[skip]   {} ({} already set)".format(settings_path, key))
        return

    settings[key] = value
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    out.append("[create] {} ({} = {})".format(settings_path, key, json.dumps(value)))


def run(cwd=None):
    if cwd is None:
        cwd = os.getcwd()

    if not _is_git_repo(cwd):
        sys.stderr.write(
            "Error: {} is not a git repository.\n"
            "Run `git init` first, then re-run `engaku init`.\n".format(cwd)
        )
        return 1

    tpl = _templates_dir()
    out = []

    # ── .ai/ skeleton ────────────────────────────────────────────────────────
    _copy_template(
        os.path.join(tpl, "ai", "overview.md"),
        os.path.join(cwd, ".ai", "overview.md"),
        out,
    )
    _copy_template(
        os.path.join(tpl, "ai", "engaku.json"),
        os.path.join(cwd, ".ai", "engaku.json"),
        out,
    )
    _touch_gitkeep(os.path.join(cwd, ".ai", "decisions"), out)
    _touch_gitkeep(os.path.join(cwd, ".ai", "tasks"), out)
    _touch_gitkeep(os.path.join(cwd, ".ai", "docs"), out)

    # ── .github/agents/ ──────────────────────────────────────────────────────
    agents_dir = os.path.join(cwd, ".github", "agents")
    for name in ("dev.agent.md", "planner.agent.md",
                   "reviewer.agent.md", "scanner.agent.md"):
        _copy_template(os.path.join(tpl, "agents", name), os.path.join(agents_dir, name), out)

    # ── .github/instructions/ ─────────────────────────────────────────────
    instructions_dir = os.path.join(cwd, ".github", "instructions")
    for name in ("hooks.instructions.md", "tests.instructions.md", "templates.instructions.md"):
        _copy_template(
            os.path.join(tpl, "instructions", name),
            os.path.join(instructions_dir, name),
            out,
        )

    # ── .github/skills/ ──────────────────────────────────────────────────────
    skills_dir = os.path.join(cwd, ".github", "skills")
    for skill in ("systematic-debugging", "verification-before-completion", "frontend-design", "proactive-initiative"):
        _copy_template(
            os.path.join(tpl, "skills", skill, "SKILL.md"),
            os.path.join(skills_dir, skill, "SKILL.md"),
            out,
        )

    # ── .github/copilot-instructions.md ──────────────────────────────────────
    _copy_template(
        os.path.join(tpl, "copilot-instructions.md"),
        os.path.join(cwd, ".github", "copilot-instructions.md"),
        out,
    )
    # ── .vscode/settings.json ── enable agent-scoped hooks (Preview) ─────────
    _ensure_vscode_setting(cwd, "chat.useCustomAgentHooks", True, out)

    for line in out:
        sys.stdout.write(line + "\n")

    created = sum(1 for l in out if l.startswith("[create]"))
    skipped = sum(1 for l in out if l.startswith("[skip]"))
    sys.stdout.write(
        "\nDone. {} file(s) created, {} skipped.\n"
        "Tip: Run the scanner agent in Copilot chat to generate .instructions.md files.\n".format(created, skipped)
    )
    return 0


def main(argv=None):
    sys.exit(run())

