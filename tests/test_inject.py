import json
import os
import sys
import unittest

# Add src to path for direct test execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_inject import run, _build_module_index, _parse_paths_frontmatter


class TestInject(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        os.makedirs(".ai")

    def tearDown(self):
        os.chdir(self.orig_cwd)
        import shutil
        shutil.rmtree(self.tmpdir)

    def _capture_run(self):
        import io
        buf = io.StringIO()
        orig_stdout = sys.stdout
        sys.stdout = buf
        try:
            result = run()
        finally:
            sys.stdout = orig_stdout
        return result, buf.getvalue()

    def _write(self, path, content):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_both_files_present(self):
        self._write(".ai/rules.md", "# Rules\n\nNo inline styles.")
        self._write(".ai/overview.md", "# Overview\n\nThis is a test project.")
        code, output = self._capture_run()
        self.assertEqual(code, 0)
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("No inline styles.", ctx)
        self.assertIn("This is a test project.", ctx)
        self.assertIn("---", ctx)

    def test_only_rules(self):
        self._write(".ai/rules.md", "# Rules\n\nNo inline styles.")
        code, output = self._capture_run()
        self.assertEqual(code, 0)
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("No inline styles.", ctx)
        self.assertNotIn("---", ctx)

    def test_no_files(self):
        code, output = self._capture_run()
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertEqual(data["hookSpecificOutput"]["additionalContext"], "")

    def test_output_is_valid_json(self):
        self._write(".ai/rules.md", "# Rules")
        _, output = self._capture_run()
        parsed = json.loads(output)
        self.assertIn("hookSpecificOutput", parsed)
        self.assertEqual(
            parsed["hookSpecificOutput"]["hookEventName"], "SessionStart"
        )

    def _capture_run_with_stdin(self, stdin_json):
        import io
        buf = io.StringIO()
        orig_stdout = sys.stdout
        orig_stdin = sys.stdin
        sys.stdout = buf
        sys.stdin = io.StringIO(json.dumps(stdin_json))
        try:
            result = run()
        finally:
            sys.stdout = orig_stdout
            sys.stdin = orig_stdin
        return result, buf.getvalue()

    def test_precompact_event_outputs_system_message(self):
        self._write(".ai/rules.md", "# Rules\n\nNo inline styles.")
        self._write(".ai/overview.md", "# Overview\n\nThis is a test project.")
        code, output = self._capture_run_with_stdin({"hookEventName": "PreCompact"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertIn("systemMessage", data)
        self.assertNotIn("hookSpecificOutput", data)
        self.assertIn("No inline styles.", data["systemMessage"])
        self.assertIn("This is a test project.", data["systemMessage"])

    def test_precompact_empty_files_outputs_empty_system_message(self):
        code, output = self._capture_run_with_stdin({"hookEventName": "PreCompact"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertEqual(data["systemMessage"], "")

    def test_session_start_event_uses_hook_specific_output(self):
        self._write(".ai/rules.md", "# Rules")
        code, output = self._capture_run_with_stdin({"hookEventName": "SessionStart"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertIn("hookSpecificOutput", data)
        self.assertNotIn("systemMessage", data)

    def test_unknown_event_defaults_to_session_start_format(self):
        self._write(".ai/rules.md", "# Rules")
        code, output = self._capture_run_with_stdin({"hookEventName": "UserPromptSubmit"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertIn("hookSpecificOutput", data)


class TestModuleIndex(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write(self, rel_path, content):
        full = os.path.join(self.tmpdir, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

    def test_no_modules_dir_returns_empty(self):
        result = _build_module_index(self.tmpdir)
        self.assertEqual(result, "")

    def test_empty_modules_dir_returns_empty(self):
        os.makedirs(os.path.join(self.tmpdir, ".ai", "modules"))
        result = _build_module_index(self.tmpdir)
        self.assertEqual(result, "")

    def test_module_with_paths_generates_table(self):
        self._write(
            os.path.join(".ai", "modules", "hooks.md"),
            "---\npaths:\n  - src/engaku/cmd_inject.py\n  - src/engaku/cmd_log_edit.py\n---\n## Overview\nHooks module.",
        )
        result = _build_module_index(self.tmpdir)
        self.assertIn("## Module Knowledge Index", result)
        self.assertIn("| hooks |", result)
        self.assertIn("src/engaku/cmd_inject.py, src/engaku/cmd_log_edit.py", result)
        self.assertIn(".ai/modules/hooks.md", result)
        self.assertIn(
            "Before modifying files listed above, read the corresponding knowledge file.",
            result,
        )

    def test_module_without_paths_shows_unscoped(self):
        self._write(
            os.path.join(".ai", "modules", "misc.md"),
            "## Overview\nNo frontmatter here.",
        )
        result = _build_module_index(self.tmpdir)
        self.assertIn("| misc |", result)
        self.assertIn("(unscoped)", result)

    def test_module_index_included_in_run_output(self):
        os.makedirs(os.path.join(self.tmpdir, ".ai"))
        self._write(".ai/rules.md", "# Rules\n\nNo inline styles.")
        self._write(
            os.path.join(".ai", "modules", "quality.md"),
            "---\npaths:\n  - src/engaku/cmd_validate.py\n---\n## Overview\nQuality module.",
        )
        import io
        buf = io.StringIO()
        orig_stdout = sys.stdout
        sys.stdout = buf
        try:
            code = run(cwd=self.tmpdir)
        finally:
            sys.stdout = orig_stdout
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("## Module Knowledge Index", ctx)
        self.assertIn("src/engaku/cmd_validate.py", ctx)

    def test_parse_paths_frontmatter_returns_list(self):
        self._write(
            os.path.join(".ai", "modules", "x.md"),
            "---\npaths:\n  - a/b.py\n  - c/d.py\n---\n## Overview",
        )
        paths = _parse_paths_frontmatter(os.path.join(self.tmpdir, ".ai", "modules", "x.md"))
        self.assertEqual(paths, ["a/b.py", "c/d.py"])

    def test_parse_paths_frontmatter_missing_returns_empty(self):
        self._write(
            os.path.join(".ai", "modules", "y.md"),
            "## Overview\nNo frontmatter.",
        )
        paths = _parse_paths_frontmatter(os.path.join(self.tmpdir, ".ai", "modules", "y.md"))
        self.assertEqual(paths, [])


if __name__ == "__main__":
    unittest.main()
