"""Tests for engaku init."""
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_init import run


EXPECTED_FILES = [
    os.path.join(".ai", "overview.md"),
    os.path.join(".ai", "engaku.json"),
    os.path.join(".ai", "decisions", ".gitkeep"),
    os.path.join(".ai", "tasks", ".gitkeep"),
    os.path.join(".ai", "docs", ".gitkeep"),
    os.path.join(".github", "agents", "coder.agent.md"),
    os.path.join(".github", "agents", "planner.agent.md"),
    os.path.join(".github", "agents", "reviewer.agent.md"),
    os.path.join(".github", "agents", "scanner.agent.md"),
    os.path.join(".github", "skills", "systematic-debugging", "SKILL.md"),
    os.path.join(".github", "skills", "verification-before-completion", "SKILL.md"),
    os.path.join(".github", "skills", "frontend-design", "SKILL.md"),
    os.path.join(".github", "skills", "proactive-initiative", "SKILL.md"),
    os.path.join(".github", "skills", "mcp-builder", "SKILL.md"),
    os.path.join(".github", "skills", "doc-coauthoring", "SKILL.md"),
    os.path.join(".github", "skills", "brainstorming", "SKILL.md"),
    os.path.join(".github", "skills", "chrome-devtools", "SKILL.md"),
    os.path.join(".github", "skills", "context7", "SKILL.md"),
    os.path.join(".github", "skills", "database", "SKILL.md"),
    os.path.join(".github", "skills", "karpathy-guidelines", "SKILL.md"),
    os.path.join(".github", "copilot-instructions.md"),
    os.path.join(".github", "instructions", "lessons.instructions.md"),
    os.path.join(".github", "instructions", "agent-boundaries.instructions.md"),
    os.path.join(".vscode", "mcp.json"),
    os.path.join(".vscode", "dbhub.toml"),
]


def _git_init(path):
    subprocess.run(
        ["git", "init", "-q", path],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class TestInit(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _capture_run(self, cwd=None, no_mcp=False):
        import io
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            code = run(cwd=cwd or self.tmpdir, no_mcp=no_mcp)
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err
        return code, buf_out.getvalue(), buf_err.getvalue()

    # ------------------------------------------------------------------
    def test_creates_all_files_in_fresh_git_repo(self):
        _git_init(self.tmpdir)
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        for rel in EXPECTED_FILES:
            full = os.path.join(self.tmpdir, rel)
            self.assertTrue(os.path.exists(full), "Missing: {}".format(rel))
        self.assertIn("[create]", out)

    def test_skips_existing_files(self):
        _git_init(self.tmpdir)
        # Run twice
        self._capture_run()
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        # Second run: all files already exist → all lines should be [skip]
        lines = [l for l in out.splitlines() if l.startswith("[create]") or l.startswith("[skip]")]
        creates = [l for l in lines if l.startswith("[create]")]
        self.assertEqual(creates, [], "Second run should not create any files")
        self.assertIn("[skip]", out)

    def test_partial_existing_skipped_rest_created(self):
        _git_init(self.tmpdir)
        # Pre-create one file
        ai_dir = os.path.join(self.tmpdir, ".ai")
        os.makedirs(ai_dir, exist_ok=True)
        overview_path = os.path.join(ai_dir, "overview.md")
        with open(overview_path, "w") as f:
            f.write("custom overview")
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        # Pre-created file should be skipped and content unchanged
        with open(overview_path) as f:
            self.assertEqual(f.read(), "custom overview")
        self.assertIn("[skip]", out)
        self.assertIn("[create]", out)

    def test_non_git_repo_returns_error(self):
        # tmpdir has no .git → should fail
        code, _, err = self._capture_run()
        self.assertEqual(code, 1)
        self.assertIn("not a git repository", err)

    def test_template_files_have_expected_content(self):
        _git_init(self.tmpdir)
        self._capture_run()
        # overview.md should exist and contain Engaku-aware sections
        overview = os.path.join(self.tmpdir, ".ai", "overview.md")
        self.assertTrue(os.path.exists(overview))
        with open(overview) as f:
            content = f.read()
        self.assertIn("Engaku-Managed Files", content)
        self.assertIn("Verification Commands", content)

    def test_creates_lessons_instructions(self):
        """engaku init creates lessons.instructions.md with applyTo frontmatter."""
        _git_init(self.tmpdir)
        self._capture_run()
        lessons_path = os.path.join(
            self.tmpdir, ".github", "instructions", "lessons.instructions.md"
        )
        self.assertTrue(os.path.exists(lessons_path), "lessons.instructions.md not created")
        with open(lessons_path) as f:
            content = f.read()
        self.assertIn("applyTo", content)

    def test_creates_agent_boundaries_instructions(self):
        """engaku init creates agent-boundaries.instructions.md."""
        _git_init(self.tmpdir)
        self._capture_run()
        path = os.path.join(
            self.tmpdir, ".github", "instructions", "agent-boundaries.instructions.md"
        )
        self.assertTrue(os.path.exists(path), "agent-boundaries.instructions.md not created")
        with open(path) as f:
            content = f.read()
        self.assertIn('applyTo: "**"', content)
        self.assertIn("coder", content)
        self.assertIn("planner", content)
        self.assertIn("reviewer", content)
        self.assertIn("scanner", content)

    def test_agent_boundaries_instructions_preserved(self):
        """engaku init preserves existing agent-boundaries.instructions.md."""
        _git_init(self.tmpdir)
        path = os.path.join(
            self.tmpdir, ".github", "instructions", "agent-boundaries.instructions.md"
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("custom boundaries")
        self._capture_run()
        with open(path) as f:
            self.assertEqual(f.read(), "custom boundaries")

    def test_package_data_includes_toml_templates(self):
        """DBHub TOML template is included in package-data inputs."""
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        with open(os.path.join(root, "pyproject.toml")) as f:
            content = f.read()
        self.assertIn('"templates/*.toml"', content)

    def test_dbhub_toml_created_by_default_init(self):
        """engaku init creates .vscode/dbhub.toml with DBHUB_DSN and guardrails."""
        _git_init(self.tmpdir)
        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)
        toml_path = os.path.join(self.tmpdir, ".vscode", "dbhub.toml")
        self.assertTrue(os.path.exists(toml_path), "dbhub.toml should be created")
        with open(toml_path) as f:
            content = f.read()
        self.assertIn("DBHUB_DSN", content)
        self.assertIn("readonly = true", content)
        self.assertIn("max_rows = 1000", content)

    def test_dbhub_toml_preserved_on_second_init(self):
        """engaku init preserves existing .vscode/dbhub.toml."""
        _git_init(self.tmpdir)
        toml_path = os.path.join(self.tmpdir, ".vscode", "dbhub.toml")
        os.makedirs(os.path.dirname(toml_path), exist_ok=True)
        with open(toml_path, "w") as f:
            f.write("# custom config")
        self._capture_run()
        with open(toml_path) as f:
            self.assertEqual(f.read(), "# custom config", "dbhub.toml should not be overwritten")

    def test_no_mcp_flag_skips_mcp_files(self):
        """engaku init --no-mcp skips mcp.json, dbhub.toml and MCP-related skills."""
        _git_init(self.tmpdir)
        code, out, _ = self._capture_run(no_mcp=True)
        self.assertEqual(code, 0)
        # mcp.json should NOT exist
        mcp_path = os.path.join(self.tmpdir, ".vscode", "mcp.json")
        self.assertFalse(os.path.exists(mcp_path), "mcp.json should not exist with --no-mcp")
        # dbhub.toml should NOT exist
        toml_path = os.path.join(self.tmpdir, ".vscode", "dbhub.toml")
        self.assertFalse(os.path.exists(toml_path), "dbhub.toml should not exist with --no-mcp")
        # MCP-related skills should NOT exist
        for skill in ("chrome-devtools", "context7", "database"):
            skill_path = os.path.join(self.tmpdir, ".github", "skills", skill, "SKILL.md")
            self.assertFalse(os.path.exists(skill_path), "{} should not exist with --no-mcp".format(skill))
        # Non-MCP skills should still exist
        sd_path = os.path.join(self.tmpdir, ".github", "skills", "systematic-debugging", "SKILL.md")
        self.assertTrue(os.path.exists(sd_path), "systematic-debugging should exist with --no-mcp")
        kg_path = os.path.join(self.tmpdir, ".github", "skills", "karpathy-guidelines", "SKILL.md")
        self.assertTrue(os.path.exists(kg_path), "karpathy-guidelines should exist with --no-mcp")

    def test_mcp_json_is_valid(self):
        """engaku init creates a valid mcp.json with all three servers."""
        import json
        _git_init(self.tmpdir)
        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)
        mcp_path = os.path.join(self.tmpdir, ".vscode", "mcp.json")
        self.assertTrue(os.path.exists(mcp_path), "mcp.json should be created")
        with open(mcp_path) as f:
            data = json.load(f)
        self.assertIn("servers", data)
        for server in ("chrome-devtools", "context7", "dbhub"):
            self.assertIn(server, data["servers"], "Missing server: {}".format(server))
        # DBHub shape assertions (TOML-backed)
        db = data["servers"]["dbhub"]
        self.assertEqual(db.get("type"), "stdio", "dbhub must have type=stdio")
        args = db.get("args", [])
        self.assertIn("-y", args)
        self.assertIn("--transport", args)
        self.assertIn("stdio", args)
        self.assertIn("--config", args)
        self.assertIn("${workspaceFolder}/.vscode/dbhub.toml", args)
        self.assertNotIn("--dsn", args, "dbhub must use TOML config, not --dsn")
        self.assertEqual(db.get("env", {}).get("DBHUB_DSN"), "${input:db-dsn}")
        # DBHub input assertions
        inputs = data.get("inputs", [])
        db_input = next((i for i in inputs if isinstance(i, dict) and i.get("id") == "db-dsn"), None)
        self.assertIsNotNone(db_input, "inputs must contain an entry with id=db-dsn")
        self.assertTrue(db_input.get("password"), "db-dsn input must have password=true")

    def test_default_init_injects_mcp_tools_into_agents(self):
        """Default init writes MCP tools into agent frontmatter via apply."""
        _git_init(self.tmpdir)
        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)
        coder_path = os.path.join(self.tmpdir, ".github", "agents", "coder.agent.md")
        with open(coder_path) as f:
            content = f.read()
        self.assertIn("chrome-devtools/*", content)
        self.assertIn("context7/*", content)
        self.assertIn("dbhub/*", content)

    def test_no_mcp_init_has_no_mcp_tools_in_agents(self):
        """--no-mcp init does not inject MCP tools into agent frontmatter."""
        _git_init(self.tmpdir)
        code, _, _ = self._capture_run(no_mcp=True)
        self.assertEqual(code, 0)
        coder_path = os.path.join(self.tmpdir, ".github", "agents", "coder.agent.md")
        with open(coder_path) as f:
            content = f.read()
        self.assertNotIn("chrome-devtools/*", content)
        self.assertNotIn("context7/*", content)
        self.assertNotIn("dbhub/*", content)

    def test_engaku_json_shape_default(self):
        """Default init generates engaku.json with agents and mcp_tools."""
        import json
        _git_init(self.tmpdir)
        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path) as f:
            data = json.load(f)
        self.assertIn("agents", data)
        self.assertIn("mcp_tools", data)
        self.assertEqual(len(data["mcp_tools"]["coder"]), 3)
        self.assertIn("python", data)
        self.assertIsNone(data["python"])

    def test_engaku_json_has_python_key_no_mcp(self):
        """--no-mcp init generates engaku.json with python: null."""
        import json
        _git_init(self.tmpdir)
        code, _, _ = self._capture_run(no_mcp=True)
        self.assertEqual(code, 0)
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path) as f:
            data = json.load(f)
        self.assertIn("python", data)
        self.assertIsNone(data["python"])

    def test_engaku_json_shape_no_mcp(self):
        """--no-mcp init generates engaku.json without mcp_tools."""
        import json
        _git_init(self.tmpdir)
        code, _, _ = self._capture_run(no_mcp=True)
        self.assertEqual(code, 0)
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path) as f:
            data = json.load(f)
        self.assertIn("agents", data)
        self.assertNotIn("mcp_tools", data)


if __name__ == "__main__":
    unittest.main()
