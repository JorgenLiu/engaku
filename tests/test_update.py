"""Tests for engaku update."""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_update import run, _SKILLS, _AGENTS


def _git_init(path):
    subprocess.run(
        ["git", "init", "-q", path],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class TestUpdate(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _capture_run(self, cwd=None):
        import io
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            code = run(cwd=cwd or self.tmpdir)
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err
        return code, buf_out.getvalue(), buf_err.getvalue()

    # ------------------------------------------------------------------
    def test_updates_agents_and_skills_in_existing_repo(self):
        """run init, corrupt an agent file, run update, verify agent restored."""
        _git_init(self.tmpdir)
        from engaku.cmd_init import run as init_run
        import io
        buf = io.StringIO()
        orig = sys.stdout
        sys.stdout = buf
        try:
            init_run(cwd=self.tmpdir)
        finally:
            sys.stdout = orig

        # Corrupt one agent file
        agent_path = os.path.join(self.tmpdir, ".github", "agents", "coder.agent.md")
        with open(agent_path, "w") as f:
            f.write("CORRUPTED")

        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)

        with open(agent_path) as f:
            content = f.read()
        self.assertNotEqual(content, "CORRUPTED", "Agent file should be restored")
        self.assertIn("[update]", out)

    def test_creates_new_skills_added_in_update(self):
        """run update on a repo without brainstorming, verify skill is created."""
        _git_init(self.tmpdir)
        # Ensure brainstorming does not pre-exist
        skill_path = os.path.join(
            self.tmpdir, ".github", "skills", "brainstorming", "SKILL.md"
        )
        self.assertFalse(os.path.exists(skill_path))

        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(skill_path), "brainstorming/SKILL.md should be created")
        self.assertIn("[create]", out)

    def test_preserves_user_files(self):
        """copilot-instructions.md and overview.md must not be touched by update."""
        _git_init(self.tmpdir)
        # Pre-create user-owned files with custom content
        github_dir = os.path.join(self.tmpdir, ".github")
        os.makedirs(github_dir, exist_ok=True)
        ci_path = os.path.join(github_dir, "copilot-instructions.md")
        with open(ci_path, "w") as f:
            f.write("my custom instructions")

        ai_dir = os.path.join(self.tmpdir, ".ai")
        os.makedirs(ai_dir, exist_ok=True)
        overview_path = os.path.join(ai_dir, "overview.md")
        with open(overview_path, "w") as f:
            f.write("my custom overview")

        self._capture_run()

        with open(ci_path) as f:
            self.assertEqual(f.read(), "my custom instructions")
        with open(overview_path) as f:
            self.assertEqual(f.read(), "my custom overview")

    def test_auto_applies_model_config(self):
        """After update, engaku.json model config should be written to agent frontmatter."""
        import json
        _git_init(self.tmpdir)

        # Create engaku.json with a model config
        ai_dir = os.path.join(self.tmpdir, ".ai")
        os.makedirs(ai_dir, exist_ok=True)
        config_path = os.path.join(ai_dir, "engaku.json")
        with open(config_path, "w") as f:
            json.dump({"agents": {"coder": "test-model"}}, f)

        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)

        # coder.agent.md should have the model field
        agent_path = os.path.join(self.tmpdir, ".github", "agents", "coder.agent.md")
        with open(agent_path) as f:
            content = f.read()
        self.assertIn("test-model", content, "model config should be applied to agent frontmatter")

    def test_creates_lessons_instructions(self):
        """engaku update creates lessons.instructions.md if missing."""
        _git_init(self.tmpdir)
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        lessons_path = os.path.join(
            self.tmpdir, ".github", "instructions", "lessons.instructions.md"
        )
        self.assertTrue(os.path.exists(lessons_path), "lessons.instructions.md not created")
        with open(lessons_path) as f:
            content = f.read()
        self.assertIn("applyTo", content)

    def test_non_git_repo_returns_error(self):
        # tmpdir has no .git → should fail
        code, _, err = self._capture_run()
        self.assertEqual(code, 1)
        self.assertIn("not a git repository", err)

    def test_brainstorming_skill_included(self):
        self.assertIn("brainstorming", _SKILLS)

    def test_karpathy_skill_included(self):
        self.assertIn("karpathy-guidelines", _SKILLS)

    def test_creates_karpathy_skill_in_fresh_repo(self):
        """run update on a repo without karpathy-guidelines, verify skill is created."""
        _git_init(self.tmpdir)
        skill_path = os.path.join(
            self.tmpdir, ".github", "skills", "karpathy-guidelines", "SKILL.md"
        )
        self.assertFalse(os.path.exists(skill_path))
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(skill_path), "karpathy-guidelines/SKILL.md should be created")

    def test_reviewer_agent_has_no_dev_agent_wording(self):
        """After update, reviewer.agent.md must not contain 'dev agent' wording."""
        _git_init(self.tmpdir)
        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)
        reviewer_path = os.path.join(self.tmpdir, ".github", "agents", "reviewer.agent.md")
        with open(reviewer_path) as f:
            content = f.read()
        self.assertNotIn("dev agent", content, "reviewer.agent.md must not mention 'dev agent'")

    def test_all_agents_updated(self):
        _git_init(self.tmpdir)
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        for name in _AGENTS:
            path = os.path.join(self.tmpdir, ".github", "agents", name)
            self.assertTrue(os.path.exists(path), "Missing agent: {}".format(name))

    def test_summary_counts_correct_for_fresh_repo(self):
        _git_init(self.tmpdir)
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("Done.", out)
        # All files are new → no [update] lines for agent/skill files
        # (+1 for .vscode/settings.json, +1 for lessons.instructions.md)
        created = out.count("[create]")
        self.assertEqual(created, len(_AGENTS) + len(_SKILLS) + 2)

    def test_update_merges_mcp_servers(self):
        """run init, remove one server from mcp.json, run update, verify restored."""
        import json
        _git_init(self.tmpdir)
        from engaku.cmd_init import run as init_run
        import io
        buf = io.StringIO()
        orig = sys.stdout
        sys.stdout = buf
        try:
            init_run(cwd=self.tmpdir)
        finally:
            sys.stdout = orig

        # Remove one server from mcp.json
        mcp_path = os.path.join(self.tmpdir, ".vscode", "mcp.json")
        with open(mcp_path) as f:
            data = json.load(f)
        # Add a custom server and remove context7
        data["servers"]["my-custom"] = {"command": "echo", "args": ["hi"]}
        del data["servers"]["context7"]
        with open(mcp_path, "w") as f:
            json.dump(data, f, indent=2)

        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)

        with open(mcp_path) as f:
            result = json.load(f)
        # context7 should be restored
        self.assertIn("context7", result["servers"], "context7 should be merged back")
        # custom server should be preserved
        self.assertIn("my-custom", result["servers"], "custom server should be preserved")
        # dbhub shape preserved (TOML-backed)
        db = result["servers"].get("dbhub", {})
        self.assertEqual(db.get("type"), "stdio", "dbhub must retain type=stdio after merge")
        args = db.get("args", [])
        self.assertIn("--config", args, "dbhub must use --config after merge")
        self.assertNotIn("--dsn", args, "dbhub must not use --dsn after merge")
        # inputs merged by id — db-dsn should be present
        inputs = result.get("inputs", [])
        ids = [i.get("id") for i in inputs if isinstance(i, dict)]
        self.assertIn("db-dsn", ids, "db-dsn input must be present after merge")
        self.assertIn("[update]", out)

    def test_update_injects_mcp_tools_into_agents(self):
        """After update, agents have MCP tools from mcp_tools config re-injected."""
        import json
        _git_init(self.tmpdir)

        # Create engaku.json with mcp_tools config
        ai_dir = os.path.join(self.tmpdir, ".ai")
        os.makedirs(ai_dir, exist_ok=True)
        config_path = os.path.join(ai_dir, "engaku.json")
        with open(config_path, "w") as f:
            json.dump({
                "agents": {"coder": "test-model"},
                "mcp_tools": {"coder": ["context7/*", "dbhub/*"]},
            }, f)

        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)

        agent_path = os.path.join(self.tmpdir, ".github", "agents", "coder.agent.md")
        with open(agent_path) as f:
            content = f.read()
        self.assertIn("context7/*", content, "MCP tools should be injected after update")
        self.assertIn("dbhub/*", content)

    def test_update_creates_dbhub_toml_if_missing(self):
        """run init (no_mcp=False), delete dbhub.toml, run update, verify it's recreated."""
        import io
        _git_init(self.tmpdir)
        from engaku.cmd_init import run as init_run
        buf = io.StringIO()
        orig = sys.stdout
        sys.stdout = buf
        try:
            init_run(cwd=self.tmpdir)
        finally:
            sys.stdout = orig

        toml_path = os.path.join(self.tmpdir, ".vscode", "dbhub.toml")
        self.assertTrue(os.path.exists(toml_path), "dbhub.toml should be created by init")
        os.remove(toml_path)

        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(toml_path), "dbhub.toml should be recreated by update")
        self.assertIn("[create]", out)

    def test_update_preserves_existing_dbhub_toml(self):
        """run update when dbhub.toml already exists — must not overwrite it."""
        import io
        _git_init(self.tmpdir)
        from engaku.cmd_init import run as init_run
        buf = io.StringIO()
        orig = sys.stdout
        sys.stdout = buf
        try:
            init_run(cwd=self.tmpdir)
        finally:
            sys.stdout = orig

        toml_path = os.path.join(self.tmpdir, ".vscode", "dbhub.toml")
        with open(toml_path, "w") as f:
            f.write("# custom toml")

        self._capture_run()

        with open(toml_path) as f:
            self.assertEqual(f.read(), "# custom toml", "dbhub.toml must not be overwritten by update")

    def test_update_reapplies_python_hook_interpreter(self):
        """After update with python set in engaku.json, hook commands use that interpreter."""
        import io
        import json
        _git_init(self.tmpdir)
        from engaku.cmd_init import run as init_run
        buf = io.StringIO()
        orig = sys.stdout
        sys.stdout = buf
        try:
            init_run(cwd=self.tmpdir)
        finally:
            sys.stdout = orig

        # Write engaku.json with python configured
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path, "w") as f:
            json.dump({
                "agents": {"coder": "test-model"},
                "python": ".venv/bin/python",
            }, f)

        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)

        coder_path = os.path.join(self.tmpdir, ".github", "agents", "coder.agent.md")
        with open(coder_path) as f:
            content = f.read()
        self.assertIn(".venv/bin/python -m engaku inject", content)
        self.assertIn(".venv/bin/python -m engaku prompt-check", content)

    def test_update_skips_mcp_when_no_mcp_json(self):
        """run init with no_mcp, run update, mcp.json should not be created."""
        _git_init(self.tmpdir)
        from engaku.cmd_init import run as init_run
        import io
        buf = io.StringIO()
        orig = sys.stdout
        sys.stdout = buf
        try:
            init_run(cwd=self.tmpdir, no_mcp=True)
        finally:
            sys.stdout = orig

        mcp_path = os.path.join(self.tmpdir, ".vscode", "mcp.json")
        self.assertFalse(os.path.exists(mcp_path), "mcp.json should not exist after init --no-mcp")

        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(mcp_path), "mcp.json should not be created by update")


if __name__ == "__main__":
    unittest.main()

