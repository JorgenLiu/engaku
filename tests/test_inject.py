import json
import os
import sys
import unittest

# Add src to path for direct test execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_inject import run, _find_active_task


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

    def test_overview_present_wrapped_in_project_context(self):
        self._write(".ai/overview.md", "# Overview\n\nThis is a test project.")
        code, output = self._capture_run()
        self.assertEqual(code, 0)
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("<project-context>", ctx)
        self.assertIn("</project-context>", ctx)
        self.assertIn("This is a test project.", ctx)

    def test_no_files_produces_empty_context(self):
        code, output = self._capture_run()
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertEqual(data["hookSpecificOutput"]["additionalContext"], "")

    def test_output_is_valid_json(self):
        self._write(".ai/overview.md", "# Overview")
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
        self._write(".ai/overview.md", "# Overview\n\nThis is a test project.")
        code, output = self._capture_run_with_stdin({"hookEventName": "PreCompact"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertIn("systemMessage", data)
        self.assertNotIn("hookSpecificOutput", data)
        self.assertIn("This is a test project.", data["systemMessage"])
        self.assertIn("<project-context>", data["systemMessage"])

    def test_precompact_empty_files_outputs_empty_system_message(self):
        code, output = self._capture_run_with_stdin({"hookEventName": "PreCompact"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertEqual(data["systemMessage"], "")

    def test_session_start_event_uses_hook_specific_output(self):
        self._write(".ai/overview.md", "# Overview")
        code, output = self._capture_run_with_stdin({"hookEventName": "SessionStart"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertIn("hookSpecificOutput", data)
        self.assertNotIn("systemMessage", data)

    def test_subagent_start_event_uses_hook_specific_output(self):
        self._write(".ai/overview.md", "# Overview\n\nReviewer context test.")
        code, output = self._capture_run_with_stdin({"hookEventName": "SubagentStart"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertIn("hookSpecificOutput", data)
        self.assertNotIn("systemMessage", data)
        self.assertEqual(
            data["hookSpecificOutput"]["hookEventName"], "SubagentStart"
        )
        self.assertIn(
            "Reviewer context test.",
            data["hookSpecificOutput"]["additionalContext"],
        )

    def test_unknown_event_defaults_to_session_start_format(self):
        self._write(".ai/overview.md", "# Overview")
        code, output = self._capture_run_with_stdin({"hookEventName": "UserPromptSubmit"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertIn("hookSpecificOutput", data)

    def test_active_task_block_included_in_output(self):
        self._write(".ai/overview.md", "# Overview\n\nProject overview.")
        os.makedirs(".ai/tasks")
        self._write(
            ".ai/tasks/task-001.md",
            "---\ntitle: My Feature\nstatus: in-progress\n---\n\n## Tasks\n\n- [x] Done step\n- [ ] Pending step one\n- [ ] Pending step two\n",
        )
        code, output = self._capture_run()
        self.assertEqual(code, 0)
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("<active-task>", ctx)
        self.assertIn("</active-task>", ctx)
        self.assertIn("## My Feature", ctx)
        self.assertIn("- [ ] Pending step one", ctx)
        self.assertIn("- [ ] Pending step two", ctx)
        self.assertNotIn("- [x] Done step", ctx)

    def test_no_active_task_no_block(self):
        self._write(".ai/overview.md", "# Overview\n\nProject overview.")
        os.makedirs(".ai/tasks")
        self._write(
            ".ai/tasks/task-001.md",
            "---\ntitle: Done Task\nstatus: completed\n---\n\n- [ ] Something\n",
        )
        code, output = self._capture_run()
        self.assertEqual(code, 0)
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("<active-task>", ctx)


class TestFindActiveTask(unittest.TestCase):
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

    def test_no_tasks_dir_returns_none(self):
        result = _find_active_task(self.tmpdir)
        self.assertIsNone(result)

    def test_empty_tasks_dir_returns_none(self):
        os.makedirs(os.path.join(self.tmpdir, ".ai", "tasks"))
        result = _find_active_task(self.tmpdir)
        self.assertIsNone(result)

    def test_no_in_progress_returns_none(self):
        self._write(
            ".ai/tasks/t.md",
            "---\ntitle: Done\nstatus: completed\n---\n\n- [ ] Step\n",
        )
        result = _find_active_task(self.tmpdir)
        self.assertIsNone(result)

    def test_in_progress_returns_title_and_unchecked(self):
        self._write(
            ".ai/tasks/task-001.md",
            "---\ntitle: My Task\nstatus: in-progress\n---\n\n- [x] Done\n- [ ] Todo A\n- [ ] Todo B\n",
        )
        result = _find_active_task(self.tmpdir)
        self.assertIsNotNone(result)
        title, unchecked = result
        self.assertEqual(title, "My Task")
        self.assertIn("- [ ] Todo A", unchecked)
        self.assertIn("- [ ] Todo B", unchecked)
        self.assertNotIn("- [x] Done", unchecked)

    def test_no_frontmatter_skipped(self):
        self._write(
            ".ai/tasks/notask.md",
            "status: in-progress\n\n- [ ] Step\n",
        )
        result = _find_active_task(self.tmpdir)
        self.assertIsNone(result)

    def test_title_falls_back_to_filename(self):
        self._write(
            ".ai/tasks/my-task-file.md",
            "---\nstatus: in-progress\n---\n\n- [ ] Something\n",
        )
        result = _find_active_task(self.tmpdir)
        self.assertIsNotNone(result)
        title, _ = result
        self.assertEqual(title, "my-task-file")

    def test_returns_first_in_progress_alphabetically(self):
        self._write(
            ".ai/tasks/aaa.md",
            "---\ntitle: First\nstatus: in-progress\n---\n\n- [ ] A\n",
        )
        self._write(
            ".ai/tasks/bbb.md",
            "---\ntitle: Second\nstatus: in-progress\n---\n\n- [ ] B\n",
        )
        result = _find_active_task(self.tmpdir)
        self.assertIsNotNone(result)
        title, _ = result
        self.assertEqual(title, "First")


if __name__ == "__main__":
    unittest.main()
