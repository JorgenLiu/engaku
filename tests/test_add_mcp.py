"""Tests for engaku add-mcp."""
import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_add_mcp import run
from engaku.mcp_recipes import RECIPE_NAMES


def _git_init(path):
    subprocess.run(
        ["git", "init", "-q", path],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _make_engaku_json(cwd, mcp_tools=None):
    ai_dir = os.path.join(cwd, ".ai")
    os.makedirs(ai_dir, exist_ok=True)
    data = {
        "agents": {
            "coder": "Claude Sonnet 4.6 (copilot)",
            "planner": "Claude Opus 4.6 (copilot)",
            "reviewer": "Claude Sonnet 4.6 (copilot)",
            "scanner": "Claude Opus 4.6 (copilot)",
        },
        "python": None,
    }
    if mcp_tools is not None:
        data["mcp_tools"] = mcp_tools
    with open(os.path.join(ai_dir, "engaku.json"), "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


class TestAddMcp(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _capture_run(self, name, agents=None, dry_run=False, no_apply=True, cwd=None):
        import io
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            code = run(
                cwd=cwd or self.tmpdir,
                name=name,
                agents=agents,
                dry_run=dry_run,
                no_apply=no_apply,
            )
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err
        return code, buf_out.getvalue(), buf_err.getvalue()

    def test_unknown_recipe_returns_error(self):
        _make_engaku_json(self.tmpdir)
        code, _, err = self._capture_run("nonexistent")
        self.assertEqual(code, 1)
        self.assertIn("unknown MCP recipe", err)

    def test_missing_engaku_json_returns_error(self):
        code, _, err = self._capture_run("github")
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_creates_mcp_json_when_missing(self):
        _make_engaku_json(self.tmpdir)
        code, out, _ = self._capture_run("github")
        self.assertEqual(code, 0)
        mcp_path = os.path.join(self.tmpdir, ".vscode", "mcp.json")
        self.assertTrue(os.path.exists(mcp_path))
        with open(mcp_path) as f:
            data = json.load(f)
        self.assertIn("github", data["servers"])

    def test_merges_server_into_existing_mcp_json(self):
        vscode_dir = os.path.join(self.tmpdir, ".vscode")
        os.makedirs(vscode_dir)
        mcp_path = os.path.join(vscode_dir, "mcp.json")
        with open(mcp_path, "w") as f:
            json.dump({"servers": {"context7": {"type": "http", "url": "https://example.com"}}}, f)
        _make_engaku_json(self.tmpdir)
        code, _, _ = self._capture_run("github")
        self.assertEqual(code, 0)
        with open(mcp_path) as f:
            data = json.load(f)
        self.assertIn("context7", data["servers"], "Existing server must be preserved")
        self.assertIn("github", data["servers"], "Recipe server must be merged")

    def test_does_not_overwrite_existing_server(self):
        vscode_dir = os.path.join(self.tmpdir, ".vscode")
        os.makedirs(vscode_dir)
        mcp_path = os.path.join(vscode_dir, "mcp.json")
        custom_cfg = {"type": "http", "url": "https://custom.example.com"}
        with open(mcp_path, "w") as f:
            json.dump({"servers": {"github": custom_cfg}}, f)
        _make_engaku_json(self.tmpdir)
        code, out, _ = self._capture_run("github")
        self.assertEqual(code, 0)
        with open(mcp_path) as f:
            data = json.load(f)
        self.assertEqual(
            data["servers"]["github"]["url"],
            "https://custom.example.com",
            "Existing github server config must not be overwritten",
        )
        self.assertIn("[skip]", out)

    def test_appends_tool_wildcard_to_engaku_json(self):
        _make_engaku_json(self.tmpdir, mcp_tools={"coder": [], "planner": [], "reviewer": []})
        code, _, _ = self._capture_run("github")
        self.assertEqual(code, 0)
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path) as f:
            data = json.load(f)
        self.assertIn("github/*", data["mcp_tools"]["coder"])
        self.assertIn("github/*", data["mcp_tools"]["planner"])
        self.assertIn("github/*", data["mcp_tools"]["reviewer"])

    def test_no_duplicate_wildcard_in_engaku_json(self):
        _make_engaku_json(self.tmpdir, mcp_tools={"coder": ["github/*"]})
        code, out, _ = self._capture_run("github")
        self.assertEqual(code, 0)
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path) as f:
            data = json.load(f)
        count = data["mcp_tools"]["coder"].count("github/*")
        self.assertEqual(count, 1, "Wildcard must not be duplicated")

    def test_dry_run_does_not_write_files(self):
        _make_engaku_json(self.tmpdir)
        code, out, _ = self._capture_run("github", dry_run=True)
        self.assertEqual(code, 0)
        self.assertIn("[dry-run]", out)
        mcp_path = os.path.join(self.tmpdir, ".vscode", "mcp.json")
        self.assertFalse(os.path.exists(mcp_path), "mcp.json must not be written in dry-run")

    def test_custom_agents_override(self):
        _make_engaku_json(self.tmpdir, mcp_tools={"coder": [], "planner": [], "reviewer": []})
        code, _, _ = self._capture_run("github", agents=["coder"])
        self.assertEqual(code, 0)
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path) as f:
            data = json.load(f)
        self.assertIn("github/*", data["mcp_tools"]["coder"])
        self.assertNotIn("github/*", data["mcp_tools"].get("planner", []))
        self.assertNotIn("github/*", data["mcp_tools"].get("reviewer", []))

    def test_all_recipe_names_are_valid(self):
        import shutil
        import tempfile
        for name in RECIPE_NAMES:
            tmpdir = tempfile.mkdtemp()
            try:
                _make_engaku_json(tmpdir, mcp_tools={"coder": [], "planner": [], "reviewer": []})
                import io
                buf_out = io.StringIO()
                buf_err = io.StringIO()
                orig_out, orig_err = sys.stdout, sys.stderr
                sys.stdout, sys.stderr = buf_out, buf_err
                try:
                    code = run(cwd=tmpdir, name=name, no_apply=True)
                finally:
                    sys.stdout, sys.stderr = orig_out, orig_err
                self.assertEqual(
                    code, 0, "Recipe '{}' failed: {}".format(name, buf_err.getvalue())
                )
            finally:
                shutil.rmtree(tmpdir)

    def test_end_to_end_add_mcp_with_apply(self):
        """add-mcp with no_apply=False merges server, updates engaku.json, and rewrites agent frontmatter."""
        _git_init(self.tmpdir)
        _make_engaku_json(
            self.tmpdir,
            mcp_tools={
                "coder": ["context7/*"],
                "planner": ["context7/*"],
                "reviewer": [],
            },
        )
        agents_dir = os.path.join(self.tmpdir, ".github", "agents")
        os.makedirs(agents_dir)
        for agent in ("coder", "planner", "reviewer"):
            with open(os.path.join(agents_dir, "{}.agent.md".format(agent)), "w") as f:
                f.write(
                    "---\nname: {name}\nmodel: \"Claude Sonnet 4.6 (copilot)\"\n"
                    "tools: ['edit', 'context7/*']\n---\n\nBody.\n".format(name=agent)
                )

        code, _, err = self._capture_run("github", no_apply=False)
        self.assertEqual(code, 0, "add-mcp failed: {}".format(err))

        # mcp.json has github server
        mcp_path = os.path.join(self.tmpdir, ".vscode", "mcp.json")
        with open(mcp_path) as f:
            mcp_data = json.load(f)
        self.assertIn("github", mcp_data["servers"])

        # engaku.json has github/* in coder and planner (github's default_agents)
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path) as f:
            config_data = json.load(f)
        self.assertIn("github/*", config_data["mcp_tools"]["coder"])
        self.assertIn("github/*", config_data["mcp_tools"]["planner"])

        # agent frontmatter has github/* after apply
        for agent in ("coder", "planner"):
            with open(os.path.join(agents_dir, "{}.agent.md".format(agent))) as f:
                content = f.read()
            self.assertIn(
                "github/*", content,
                "{}.agent.md missing github/* after add-mcp+apply".format(agent),
            )


if __name__ == "__main__":
    unittest.main()