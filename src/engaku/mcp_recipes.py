"""engaku mcp_recipes
Catalog of built-in MCP server recipes.
"""
import json
import os

RECIPE_NAMES = ("github", "gitlab", "atlassian")


def _recipes_dir():
    return os.path.join(os.path.dirname(__file__), "templates", "mcp-recipes")


def list_recipes():
    """Return a list of all available recipe dicts, sorted by name."""
    rdir = _recipes_dir()
    recipes = []
    if not os.path.isdir(rdir):
        return recipes
    for fname in sorted(os.listdir(rdir)):
        if fname.endswith(".json"):
            fpath = os.path.join(rdir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                recipes.append(data)
            except (ValueError, OSError):
                pass
    return recipes


def get_recipe(name):
    """Return the recipe dict for a given name, or None if not found."""
    rdir = _recipes_dir()
    fpath = os.path.join(rdir, "{}.json".format(name))
    if not os.path.isfile(fpath):
        return None
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError):
        return None
