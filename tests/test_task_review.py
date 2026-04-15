import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import engaku.cmd_task_review as mod


class TestExtractTasksSection(unittest.TestCase):
    def test_extracts_between_tasks_and_next_heading(self):
        body = "## Tasks\n- [x] 1. Task one\n## Out of Scope\nignored\n"
        result = mod._extract_tasks_section(body)
        self.assertIn("- [x] 1. Task one", result)
        self.assertNotIn("ignored", result)
        self.assertNotIn("Out of Scope", result)

    def test_extracts_to_eof_when_no_next_heading(self):
        body = "## Tasks\n- [x] 1. Task one\n- [x] 2. Task two\n"
        result = mod._extract_tasks_section(body)
        self.assertIn("- [x] 1. Task one", result)
        self.assertIn("- [x] 2. Task two", result)

    def test_returns_empty_when_no_tasks_heading(self):
        body = "## Background\nsome text\n## Design\nsome design\n"
        result = mod._extract_tasks_section(body)
        self.assertEqual(result, "")


class TestAllTasksChecked(unittest.TestCase):
    def test_all_checked_returns_true(self):
        section = "- [x] 1. First\n- [x] 2. Second\n"
        self.assertTrue(mod._all_tasks_checked(section))

    def test_mixed_returns_false(self):
        section = "- [x] 1. First\n- [ ] 2. Second\n"
        self.assertFalse(mod._all_tasks_checked(section))

    def test_only_unchecked_returns_false(self):
        section = "- [ ] 1. First\n- [ ] 2. Second\n"
        self.assertFalse(mod._all_tasks_checked(section))

    def test_no_checkboxes_returns_false(self):
        section = "some text with no checkboxes\n"
        self.assertFalse(mod._all_tasks_checked(section))

    def test_empty_string_returns_false(self):
        self.assertFalse(mod._all_tasks_checked(""))


FRONTMATTER_INPROGRESS_ALL_CHECKED = """\
---
plan_id: test-plan
title: Test Plan
status: in-progress
created: 2026-04-10
---

## Background
Test plan background.

## Tasks

- [x] 1. **First task**
  - Verify: `echo ok`

- [x] 2. **Second task**
  - Verify: `echo ok`

## Out of Scope
Nothing.
"""

FRONTMATTER_INPROGRESS_PARTIAL = """\
---
plan_id: test-plan
title: Test Plan
status: in-progress
created: 2026-04-10
---

## Tasks

- [x] 1. **First task**
  - Verify: `echo ok`

- [ ] 2. **Second task**
  - Verify: `echo ok`
"""

FRONTMATTER_DONE_ALL_CHECKED = """\
---
plan_id: done-plan
title: Done Plan
status: done
created: 2026-04-10
---

## Tasks

- [x] 1. **First task**
  - Verify: `echo ok`
"""

FRONTMATTER_OUTOFSCOPE_HAS_UNCHECKED = """\
---
plan_id: test-plan
title: Test Plan
status: in-progress
created: 2026-04-10
---

## Tasks

- [x] 1. **First task**
  - Verify: `echo ok`

## Out of Scope

- [ ] This is excluded
"""


class TestFindCompletedTaskFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_dir = os.path.join(self.tmpdir, ".ai", "tasks")
        os.makedirs(self.tasks_dir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_task(self, filename, content):
        path = os.path.join(self.tasks_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_no_tasks_dir_returns_none(self):
        shutil.rmtree(self.tasks_dir)
        result = mod._find_completed_task_file(self.tmpdir)
        self.assertIsNone(result)

    def test_all_checked_in_progress_returns_path(self):
        self._write_task("2026-04-10-myplan.md", FRONTMATTER_INPROGRESS_ALL_CHECKED)
        result = mod._find_completed_task_file(self.tmpdir)
        self.assertIsNotNone(result)
        self.assertIn("2026-04-10-myplan.md", result)

    def test_partial_unchecked_returns_none(self):
        self._write_task("2026-04-10-myplan.md", FRONTMATTER_INPROGRESS_PARTIAL)
        result = mod._find_completed_task_file(self.tmpdir)
        self.assertIsNone(result)

    def test_done_status_skipped(self):
        self._write_task("2026-04-10-done.md", FRONTMATTER_DONE_ALL_CHECKED)
        result = mod._find_completed_task_file(self.tmpdir)
        self.assertIsNone(result)

    def test_out_of_scope_unchecked_not_counted(self):
        # ## Tasks has all [x]; ## Out of Scope has [ ] — should return the file
        self._write_task("2026-04-10-myplan.md", FRONTMATTER_OUTOFSCOPE_HAS_UNCHECKED)
        result = mod._find_completed_task_file(self.tmpdir)
        self.assertIsNotNone(result)
        self.assertIn("2026-04-10-myplan.md", result)


class TestRun(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.makedirs(os.path.join(self.tmpdir, ".ai", "tasks"))
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmpdir)

    def _run(self, hook_input=None):
        stdin_data = json.dumps(hook_input) if hook_input else "{}"
        orig_stdin, orig_stdout = sys.stdin, sys.stdout
        sys.stdin = io.StringIO(stdin_data)
        buf_out = io.StringIO()
        sys.stdout = buf_out
        try:
            code = mod.run()
        finally:
            sys.stdin = orig_stdin
            sys.stdout = orig_stdout
        return code, buf_out.getvalue()

    def _write_task(self, filename, content):
        path = os.path.join(self.tmpdir, ".ai", "tasks", filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_stop_hook_active_exits_zero_no_output(self):
        self._write_task("2026-04-10-plan.md", FRONTMATTER_INPROGRESS_ALL_CHECKED)
        code, out = self._run({"stop_hook_active": True})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_no_task_files_exits_zero(self):
        code, out = self._run({})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_all_checked_outputs_system_message(self):
        self._write_task("2026-04-10-plan.md", FRONTMATTER_INPROGRESS_ALL_CHECKED)
        code, out = self._run({})
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("systemMessage", data)
        self.assertIn("Verify Tasks", data["systemMessage"])
        self.assertIn("2026-04-10-plan.md", data["systemMessage"])

    def test_partial_tasks_no_output(self):
        self._write_task("2026-04-10-plan.md", FRONTMATTER_INPROGRESS_PARTIAL)
        code, out = self._run({})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
