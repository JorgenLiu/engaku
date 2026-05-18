"""
engaku add-mcp
Add a curated MCP server recipe to .vscode/mcp.json and .ai/engaku.json,
then sync agent frontmatter via engaku apply.

Usage:
  engaku add-mcp <name> [--agents agent1 agent2] [--dry-run] [--no-apply]
"""
import json
import os
import sys

from engaku.mcp_recipes import get_recipe, RECIPE_NAMES
from engaku.constants import CONFIG_FILE


def run(cwd=None, name=None, agents=None, dry_run=False, no_apply=False):
    if cwd is None:
        cwd = os.getcwd()

    recipe = get_recipe(name)
    if recipe is None:
        sys.stderr.write(
            "error: unknown MCP recipe '{}'. Available: {}\n".format(
                name, ", ".join(RECIPE_NAMES)
            )
        )
        return 1

    config_path = os.path.join(cwd, CONFIG_FILE)
    if not os.path.isfile(config_path):
        sys.stderr.write(
            "error: {} not found.\nRun 'engaku init' first.\n".format(config_path)
        )
        return 1

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (ValueError, OSError) as exc:
        sys.stderr.write("error: invalid JSON in {}: {}\n".format(config_path, exc))
        return 1

    if agents is not None:
        target_agents = [a.strip() for a in agents if a.strip()]
    else:
        target_agents = list(recipe.get("default_agents", []))

    mcp_path = os.path.join(cwd, ".vscode", "mcp.json")
    if os.path.isfile(mcp_path):
        try:
            with open(mcp_path, "r", encoding="utf-8") as f:
                mcp_data = json.load(f)
        except (ValueError, OSError) as exc:
            sys.stderr.write("error: invalid JSON in {}: {}\n".format(mcp_path, exc))
            return 1
    else:
        mcp_data = {"servers": {}}

    server_name = recipe["name"]
    tool_wildcard = recipe["tool_wildcard"]
    server_cfg = recipe["server"]

    servers = mcp_data.setdefault("servers", {})
    mcp_changed = server_name not in servers

    mcp_tools = config.setdefault("mcp_tools", {})
    engaku_changes = []
    for agent in target_agents:
        tool_list = mcp_tools.setdefault(agent, [])
        if tool_wildcard not in tool_list:
            engaku_changes.append(agent)

    if dry_run:
        if mcp_changed:
            sys.stdout.write(
                "[dry-run] Would merge server '{}' into {}\n".format(server_name, mcp_path)
            )
        else:
            sys.stdout.write(
                "[dry-run] Server '{}' already present in {}\n".format(server_name, mcp_path)
            )
        for agent in engaku_changes:
            sys.stdout.write(
                "[dry-run] Would append '{}' to mcp_tools.{} in {}\n".format(
                    tool_wildcard, agent, config_path
                )
            )
        if not engaku_changes and not mcp_changed:
            sys.stdout.write("[dry-run] No changes needed.\n")
        return 0

    if mcp_changed:
        servers[server_name] = server_cfg
        vscode_dir = os.path.dirname(mcp_path)
        if not os.path.isdir(vscode_dir):
            os.makedirs(vscode_dir)
        with open(mcp_path, "w", encoding="utf-8") as f:
            json.dump(mcp_data, f, indent=2)
            f.write("\n")
        sys.stdout.write("[update]  {}\n".format(mcp_path))
    else:
        sys.stdout.write(
            "[skip]    {} (server '{}' already present)\n".format(mcp_path, server_name)
        )

    if engaku_changes:
        for agent in engaku_changes:
            mcp_tools[agent].append(tool_wildcard)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
        for agent in engaku_changes:
            sys.stdout.write(
                "[update]  {} (added '{}' to mcp_tools.{})\n".format(
                    config_path, tool_wildcard, agent
                )
            )
    else:
        sys.stdout.write(
            "[skip]    {} (wildcard already present for all target agents)\n".format(
                config_path
            )
        )

    if not no_apply:
        from engaku.cmd_apply import run as apply_run
        apply_run(cwd)

    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog="engaku add-mcp",
        description="Add a curated MCP server recipe",
    )
    parser.add_argument(
        "name",
        help="Recipe name ({})".format(", ".join(RECIPE_NAMES)),
    )
    parser.add_argument(
        "--agents",
        nargs="+",
        metavar="AGENT",
        help="Override default agents (space-separated)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing files",
    )
    parser.add_argument(
        "--no-apply",
        action="store_true",
        help="Skip engaku apply after writing files",
    )
    args = parser.parse_args()
    sys.exit(run(name=args.name, agents=args.agents, dry_run=args.dry_run, no_apply=args.no_apply))
