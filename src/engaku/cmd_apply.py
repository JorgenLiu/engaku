"""
engaku apply
Apply .ai/engaku.json configuration to .github/agents/ files.

Reads model assignments from .ai/engaku.json and writes the model: field
into each matching .github/agents/{name}.agent.md frontmatter.  If an agent
file has no model: field, one is inserted immediately after the name: line.

Usage:
  engaku apply
"""
import json
import os
import re
import sys

from engaku.constants import CONFIG_FILE
from engaku.utils import load_config


def _update_agent_model(agent_path, model):
    """Update or insert model: field in agent frontmatter.

    Returns (changed, reason) where changed is True if the file was written.
    """
    with open(agent_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---\n"):
        return False, "no frontmatter"

    close = content.find("\n---", 4)
    if close == -1:
        return False, "unclosed frontmatter"

    # Guard against false match (--- embedded inside a multiline value)
    after_close = content[close + 4:]
    if after_close and after_close[0] not in ("\n", "\r"):
        return False, "malformed frontmatter"

    fm = content[4:close]       # YAML body — no trailing newline
    rest = content[close:]      # starts with \n---

    model_line = "model: ['{}']".format(model)

    if re.search(r"^model:", fm, re.MULTILINE):
        new_fm = re.sub(r"^model:.*$", model_line, fm, flags=re.MULTILINE)
    else:
        # Insert immediately after the name: line if present, else append.
        if re.search(r"^name:", fm, re.MULTILINE):
            new_fm = re.sub(
                r"(^name:.*$)",
                r"\1\n" + model_line,
                fm,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            new_fm = fm + "\n" + model_line

    if new_fm == fm:
        return False, "no change"

    with open(agent_path, "w", encoding="utf-8") as f:
        f.write("---\n" + new_fm + rest)
    return True, "ok"


def run(cwd=None):
    if cwd is None:
        cwd = os.getcwd()

    config_path = os.path.join(cwd, CONFIG_FILE)
    if not os.path.isfile(config_path):
        sys.stderr.write(
            "error: {} not found.\n"
            "Run 'engaku init' to create it.\n".format(config_path)
        )
        return 1

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            json.load(f)
    except ValueError as exc:
        sys.stderr.write(
            "error: invalid JSON in {}: {}\n".format(config_path, exc)
        )
        return 1

    config = load_config(cwd)


    # ── agents → .github/agents/ ─────────────────────────────────────────────
    agents_config = config.get("agents", {})
    agents_dir = os.path.join(cwd, ".github", "agents")
    changed = 0
    skipped = 0

    for agent_name in sorted(agents_config):
        model = agents_config[agent_name]
        agent_path = os.path.join(agents_dir, "{}.agent.md".format(agent_name))
        if not os.path.isfile(agent_path):
            sys.stdout.write(
                "  [skip]    {}.agent.md (file not found)\n".format(agent_name)
            )
            skipped += 1
            continue

        updated, reason = _update_agent_model(agent_path, model)
        if updated:
            sys.stdout.write(
                "  [updated] {}.agent.md -> {}\n".format(agent_name, model)
            )
            changed += 1
        else:
            sys.stdout.write(
                "  [skip]    {}.agent.md ({})\n".format(agent_name, reason)
            )
            skipped += 1

    total_changed = changed
    total_skipped = skipped
    sys.stdout.write(
        "\napply complete: {} updated, {} skipped.\n".format(total_changed, total_skipped)
    )
    return 0


def main():
    sys.exit(run())
