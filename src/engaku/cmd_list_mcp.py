"""
engaku list-mcp
List available built-in MCP server recipes.

Usage:
  engaku list-mcp
"""
import sys

from engaku.mcp_recipes import list_recipes


def run():
    recipes = list_recipes()
    if not recipes:
        sys.stdout.write("No MCP recipes found.\n")
        return 0

    col_name = max(len(r.get("name", "")) for r in recipes)
    col_agents = max(len(", ".join(r.get("default_agents", []))) for r in recipes)
    col_wc = max(len(r.get("tool_wildcard", "")) for r in recipes)

    header_name = "NAME"
    header_agents = "DEFAULT AGENTS"
    header_wc = "WILDCARD"
    header_desc = "DESCRIPTION"

    col_name = max(col_name, len(header_name))
    col_agents = max(col_agents, len(header_agents))
    col_wc = max(col_wc, len(header_wc))

    fmt = "  {{:<{}}} {{:<{}}} {{:<{}}} {{}}\n".format(col_name, col_agents, col_wc)
    sys.stdout.write(fmt.format(header_name, header_agents, header_wc, header_desc))
    sep = "  " + "-" * (col_name + col_agents + col_wc + len(header_desc) + 6)
    sys.stdout.write(sep + "\n")
    for r in recipes:
        sys.stdout.write(fmt.format(
            r.get("name", ""),
            ", ".join(r.get("default_agents", [])),
            r.get("tool_wildcard", ""),
            r.get("description", ""),
        ))
    return 0


def main():
    sys.exit(run())
