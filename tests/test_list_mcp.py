"""Tests for engaku list-mcp."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_list_mcp import run
from engaku.mcp_recipes import list_recipes, get_recipe, RECIPE_NAMES


class TestListMcp(unittest.TestCase):
    def _capture_run(self):
        import io
        buf = io.StringIO()
        orig = sys.stdout
        sys.stdout = buf
        try:
            code = run()
        finally:
            sys.stdout = orig
        return code, buf.getvalue()

    def test_exits_zero(self):
        code, _ = self._capture_run()
        self.assertEqual(code, 0)

    def test_all_recipe_names_in_output(self):
        code, out = self._capture_run()
        self.assertEqual(code, 0)
        for name in RECIPE_NAMES:
            self.assertIn(name, out, "Missing recipe in output: {}".format(name))

    def test_header_row_present(self):
        _, out = self._capture_run()
        self.assertIn("NAME", out)
        self.assertIn("WILDCARD", out)
        self.assertIn("DESCRIPTION", out)

    def test_list_recipes_returns_all_four(self):
        recipes = list_recipes()
        names = [r["name"] for r in recipes]
        for name in RECIPE_NAMES:
            self.assertIn(name, names, "Missing recipe: {}".format(name))

    def test_get_recipe_github(self):
        r = get_recipe("github")
        self.assertIsNotNone(r)
        self.assertEqual(r["name"], "github")
        self.assertIn("server", r)
        self.assertIn("tool_wildcard", r)
        self.assertIn("default_agents", r)

    def test_get_recipe_unknown_returns_none(self):
        self.assertIsNone(get_recipe("nonexistent"))

    def test_recipe_fields_present(self):
        for name in RECIPE_NAMES:
            r = get_recipe(name)
            self.assertIsNotNone(r, "Recipe not found: {}".format(name))
            for field in ("name", "description", "upstream", "last_verified",
                          "server", "tool_wildcard", "default_agents", "notes"):
                self.assertIn(field, r, "Missing field '{}' in recipe '{}'".format(field, name))

    def test_github_default_agents_includes_planner(self):
        r = get_recipe("github")
        self.assertIn("planner", r["default_agents"])

    def test_jira_default_agents_coder_planner_only(self):
        r = get_recipe("jira")
        self.assertIn("coder", r["default_agents"])
        self.assertIn("planner", r["default_agents"])
        self.assertNotIn("reviewer", r["default_agents"])

    def test_confluence_default_agents_coder_planner_only(self):
        r = get_recipe("confluence")
        self.assertIn("coder", r["default_agents"])
        self.assertIn("planner", r["default_agents"])
        self.assertNotIn("reviewer", r["default_agents"])

    def test_service_recipes_no_credential_inputs(self):
        """GitLab, Jira, Confluence recipes must not include credential input placeholders."""
        import json
        for name in ("gitlab", "jira", "confluence"):
            r = get_recipe(name)
            raw = json.dumps(r)
            self.assertNotIn("${input:", raw,
                "Recipe '{}' must not contain VS Code input placeholders".format(name))
            self.assertNotIn("env", r["server"],
                "Recipe '{}' must not have a server.env block".format(name))

    def test_atlassian_recipes_use_uvx(self):
        """Jira and Confluence use uvx mcp-atlassian, not the invalid npm package."""
        for name in ("jira", "confluence"):
            r = get_recipe(name)
            self.assertEqual(r["server"]["command"], "uvx")
            self.assertEqual(r["server"]["args"], ["mcp-atlassian"])

    def test_gitlab_uses_verified_package(self):
        """GitLab recipe uses @zereight/mcp-gitlab@latest, not the invalid @gitlab-org package."""
        r = get_recipe("gitlab")
        args_str = " ".join(r["server"]["args"])
        self.assertIn("@zereight/mcp-gitlab@latest", args_str)
        self.assertNotIn("@gitlab-org/mcp-server-gitlab", args_str)


if __name__ == "__main__":
    unittest.main()
