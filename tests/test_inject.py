import json
import os
import sys
import unittest

# Add src to path for direct test execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_inject import run, _find_active_tasks, _extract_task_compact_body


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
        self.assertIn("<active-tasks>", ctx)
        self.assertIn("</active-tasks>", ctx)
        self.assertIn('<task file="task-001.md" state="needs-work">', ctx)
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
        self.assertNotIn("<active-tasks>", ctx)


class TestFindActiveTasks(unittest.TestCase):
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

    def test_no_tasks_dir_returns_empty_list(self):
        result = _find_active_tasks(self.tmpdir)
        self.assertEqual(result, [])

    def test_empty_tasks_dir_returns_empty_list(self):
        os.makedirs(os.path.join(self.tmpdir, ".ai", "tasks"))
        result = _find_active_tasks(self.tmpdir)
        self.assertEqual(result, [])

    def test_no_in_progress_returns_empty_list(self):
        self._write(
            ".ai/tasks/t.md",
            "---\ntitle: Done\nstatus: completed\n---\n\n- [ ] Step\n",
        )
        result = _find_active_tasks(self.tmpdir)
        self.assertEqual(result, [])

    def test_in_progress_returns_title_and_unchecked(self):
        self._write(
            ".ai/tasks/task-001.md",
            "---\ntitle: My Task\nstatus: in-progress\n---\n\n- [x] Done\n- [ ] Todo A\n- [ ] Todo B\n",
        )
        result = _find_active_tasks(self.tmpdir)
        self.assertEqual(len(result), 1)
        title, unchecked, body, filename, state = result[0]
        self.assertEqual(title, "My Task")
        self.assertIn("- [ ] Todo A", unchecked)
        self.assertIn("- [ ] Todo B", unchecked)
        self.assertNotIn("- [x] Done", unchecked)
        self.assertIn("- [x] Done", body)
        self.assertEqual(filename, "task-001.md")
        self.assertEqual(state, "needs-work")

    def test_no_frontmatter_skipped(self):
        self._write(
            ".ai/tasks/notask.md",
            "status: in-progress\n\n- [ ] Step\n",
        )
        result = _find_active_tasks(self.tmpdir)
        self.assertEqual(result, [])

    def test_title_falls_back_to_filename(self):
        self._write(
            ".ai/tasks/my-task-file.md",
            "---\nstatus: in-progress\n---\n\n- [ ] Something\n",
        )
        result = _find_active_tasks(self.tmpdir)
        self.assertEqual(len(result), 1)
        title, _, _, _, _ = result[0]
        self.assertEqual(title, "my-task-file")

    def test_returns_all_in_progress_tasks(self):
        self._write(
            ".ai/tasks/aaa.md",
            "---\ntitle: First\nstatus: in-progress\n---\n\n- [ ] A\n",
        )
        self._write(
            ".ai/tasks/bbb.md",
            "---\ntitle: Second\nstatus: in-progress\n---\n\n- [ ] B\n",
        )
        result = _find_active_tasks(self.tmpdir)
        self.assertEqual(len(result), 2)
        titles = [r[0] for r in result]
        self.assertEqual(titles, ["First", "Second"])

    def test_needs_review_state_when_all_checked(self):
        self._write(
            ".ai/tasks/done.md",
            "---\ntitle: Review Me\nstatus: in-progress\n---\n\n- [x] Step A\n- [x] Step B\n",
        )
        result = _find_active_tasks(self.tmpdir)
        self.assertEqual(len(result), 1)
        _, _, _, _, state = result[0]
        self.assertEqual(state, "needs-review")

    def test_mixed_needs_work_and_needs_review(self):
        self._write(
            ".ai/tasks/aaa.md",
            "---\ntitle: Working\nstatus: in-progress\n---\n\n- [x] Done\n- [ ] Todo\n",
        )
        self._write(
            ".ai/tasks/bbb.md",
            "---\ntitle: Reviewing\nstatus: in-progress\n---\n\n- [x] All done\n",
        )
        result = _find_active_tasks(self.tmpdir)
        self.assertEqual(len(result), 2)
        states = {r[0]: r[4] for r in result}
        self.assertEqual(states["Working"], "needs-work")
        self.assertEqual(states["Reviewing"], "needs-review")


class TestExtractTaskCompactBody(unittest.TestCase):

    def test_includes_key_sections_and_checkboxes(self):
        body = (
            "## Background\nThis work is needed for testing.\n\n"
            "## Design\nKey technical decisions here.\n\n"
            "## File Map\n- Modify: src/foo.py\n\n"
            "## Tasks\n\n- [x] 1. **Done step**\n  - Verify: `echo done`\n"
            "- [ ] 2. **Pending step**\n  - Verify: `echo pending`\n\n"
            "## Out of Scope\nDo not touch the database.\n"
        )
        result = _extract_task_compact_body(body)
        self.assertIn("## Background", result)
        self.assertIn("This work is needed for testing.", result)
        self.assertIn("## Design", result)
        self.assertIn("Key technical decisions here.", result)
        self.assertIn("## File Map", result)
        self.assertIn("Modify: src/foo.py", result)
        self.assertIn("- [x] 1.", result)
        self.assertIn("- [ ] 2.", result)
        self.assertNotIn("## Out of Scope", result)
        self.assertNotIn("Do not touch the database.", result)

    def test_empty_body_returns_empty_string(self):
        self.assertEqual(_extract_task_compact_body(""), "")

    def test_no_matching_sections(self):
        body = "## Tasks\n\n- [ ] Step one\n"
        result = _extract_task_compact_body(body)
        self.assertIn("- [ ] Step one", result)
        self.assertNotIn("## Tasks", result)


class TestInjectPreCompactWithTask(unittest.TestCase):

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

    def _write(self, path, content):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

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

    def test_precompact_with_task_includes_compact_body(self):
        self._write(".ai/overview.md", "# Overview")
        os.makedirs(".ai/tasks")
        self._write(
            ".ai/tasks/task-001.md",
            "---\ntitle: My Feature\nstatus: in-progress\n---\n\n"
            "## Background\nNeeded for X.\n\n## Design\nUse approach Y.\n\n"
            "## Tasks\n\n- [x] Done step\n- [ ] Pending step\n",
        )
        code, output = self._capture_run_with_stdin({"hookEventName": "PreCompact"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        msg = data["systemMessage"]
        self.assertIn("<active-tasks>", msg)
        self.assertIn("## Background", msg)
        self.assertIn("Needed for X.", msg)
        self.assertIn("- [x] Done step", msg)
        self.assertIn("- [ ] Pending step", msg)

    def test_session_start_with_task_includes_only_unchecked(self):
        self._write(".ai/overview.md", "# Overview")
        os.makedirs(".ai/tasks")
        self._write(
            ".ai/tasks/task-001.md",
            "---\ntitle: My Feature\nstatus: in-progress\n---\n\n"
            "## Background\nNeeded for X.\n\n## Tasks\n\n"
            "- [x] Done step\n- [ ] Pending step\n",
        )
        code, output = self._capture_run_with_stdin({"hookEventName": "SessionStart"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn("- [ ] Pending step", ctx)
        self.assertNotIn("- [x] Done step", ctx)
        self.assertNotIn("## Background", ctx)

    def test_needs_review_task_emits_review_message(self):
        self._write(".ai/overview.md", "# Overview")
        os.makedirs(".ai/tasks")
        self._write(
            ".ai/tasks/task-001.md",
            "---\ntitle: Done Feature\nstatus: in-progress\n---\n\n"
            "## Tasks\n\n- [x] Step A\n- [x] Step B\n",
        )
        code, output = self._capture_run_with_stdin({"hookEventName": "SessionStart"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn('state="needs-review"', ctx)
        self.assertNotIn("All tasks completed", ctx)

    def test_multiple_tasks_both_appear_in_output(self):
        self._write(".ai/overview.md", "# Overview")
        os.makedirs(".ai/tasks")
        self._write(
            ".ai/tasks/aaa.md",
            "---\ntitle: Feature A\nstatus: in-progress\n---\n\n- [ ] Step A\n",
        )
        self._write(
            ".ai/tasks/bbb.md",
            "---\ntitle: Feature B\nstatus: in-progress\n---\n\n- [x] Done B\n",
        )
        code, output = self._capture_run_with_stdin({"hookEventName": "SessionStart"})
        self.assertEqual(code, 0)
        data = json.loads(output)
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIn('<task file="aaa.md" state="needs-work">', ctx)
        self.assertIn('<task file="bbb.md" state="needs-review">', ctx)
        self.assertIn("## Feature A", ctx)
        self.assertIn("## Feature B", ctx)


if __name__ == "__main__":
    unittest.main()
