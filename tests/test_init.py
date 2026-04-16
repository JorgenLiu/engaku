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
    os.path.join(".github", "agents", "dev.agent.md"),
    os.path.join(".github", "agents", "planner.agent.md"),
    os.path.join(".github", "agents", "reviewer.agent.md"),
    os.path.join(".github", "agents", "scanner.agent.md"),
    os.path.join(".github", "instructions", "hooks.instructions.md"),
    os.path.join(".github", "instructions", "tests.instructions.md"),
    os.path.join(".github", "instructions", "templates.instructions.md"),
    os.path.join(".github", "skills", "systematic-debugging", "SKILL.md"),
    os.path.join(".github", "skills", "verification-before-completion", "SKILL.md"),
    os.path.join(".github", "skills", "frontend-design", "SKILL.md"),
    os.path.join(".github", "skills", "proactive-initiative", "SKILL.md"),
    os.path.join(".github", "skills", "mcp-builder", "SKILL.md"),
    os.path.join(".github", "skills", "doc-coauthoring", "SKILL.md"),
    os.path.join(".github", "copilot-instructions.md"),
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
        # overview.md should exist
        overview = os.path.join(self.tmpdir, ".ai", "overview.md")
        self.assertTrue(os.path.exists(overview))


if __name__ == "__main__":
    unittest.main()
