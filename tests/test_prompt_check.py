"""Tests for engaku prompt-check."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import engaku.cmd_prompt_check as mod


def _run_with_prompt(prompt, cwd=None):
    """Call run() with the given prompt string; return (exit_code, stdout)."""
    hook_input = {"prompt": prompt} if prompt is not None else {}
    stdin_data = json.dumps(hook_input)
    orig_stdin, orig_stdout = sys.stdin, sys.stdout
    sys.stdin = io.StringIO(stdin_data)
    buf = io.StringIO()
    sys.stdout = buf
    try:
        code = mod.run(cwd=cwd)
    finally:
        sys.stdin, sys.stdout = orig_stdin, orig_stdout
    return code, buf.getvalue()


class TestPromptCheck(unittest.TestCase):

    def setUp(self):
        # Use an isolated temp dir so no active task is found.
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _run(self, prompt):
        return _run_with_prompt(prompt, cwd=self.tmpdir)

    # ── keyword matches ───────────────────────────────────────────────────────

    def test_always_triggers(self):
        code, out = self._run("always use type hints")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("systemMessage", data)
        self.assertIn("copilot-instructions.md", data["systemMessage"])

    def test_never_triggers(self):
        code, out = self._run("never import star")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_rule_english_triggers(self):
        code, out = self._run("add a rule: no magic numbers")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_rule_english_case_insensitive(self):
        code, out = self._run("Follow this Rule in all modules")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_constraint_triggers(self):
        code, out = self._run("there is a new constraint on imports")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_preference_triggers(self):
        code, out = self._run("my preference is to use f-strings")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_chinese_rule_triggers(self):
        code, out = self._run("规则：所有函数必须有类型注解")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_chinese_cong_xianzai_kaishi_triggers(self):
        code, out = self._run("从现在开始，禁止使用全局变量")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_chinese_biyao_triggers(self):
        code, out = self._run("这个函数必须返回字符串")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    # ── no keyword match ──────────────────────────────────────────────────────

    def test_plain_prompt_no_match(self):
        code, out = self._run("fix the bug in auth.py")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {})

    def test_empty_prompt_no_match(self):
        code, out = self._run("")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {})

    def test_no_prompt_field_no_match(self):
        """Missing prompt key in hook_input should produce empty output."""
        orig_stdin, orig_stdout = sys.stdin, sys.stdout
        sys.stdin = io.StringIO(json.dumps({}))
        buf = io.StringIO()
        sys.stdout = buf
        try:
            code = mod.run(cwd=self.tmpdir)
        finally:
            sys.stdin, sys.stdout = orig_stdin, orig_stdout
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue()), {})

    def test_empty_stdin_no_crash(self):
        """No stdin (tty-like) should not crash."""
        orig_stdin, orig_stdout = sys.stdin, sys.stdout
        sys.stdin = io.StringIO("")
        buf = io.StringIO()
        sys.stdout = buf
        try:
            code = mod.run(cwd=self.tmpdir)
        finally:
            sys.stdin, sys.stdout = orig_stdin, orig_stdout
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue()), {})

    def test_always_exits_zero(self):
        """Should never return non-zero regardless of input."""
        for prompt in ["always fail", "just a question", ""]:
            code, _ = self._run(prompt)
            self.assertEqual(code, 0)

    # ── keyword precision ─────────────────────────────────────────────────────

    def test_always_alone_no_trigger(self):
        """Bare 'always' without a directive verb should not trigger."""
        code, out = self._run("always")
        self.assertEqual(code, 0)
        self.assertNotIn("copilot-instructions.md", json.loads(out).get("systemMessage", ""))

    def test_always_in_question_no_trigger(self):
        """'always' in a normal question should not trigger keyword match."""
        code, out = self._run("why does this always fail?")
        self.assertEqual(code, 0)
        self.assertNotIn("copilot-instructions.md", json.loads(out).get("systemMessage", ""))

    def test_always_use_triggers(self):
        code, out = _run_with_prompt("always use type hints")
        self.assertIn("systemMessage", json.loads(out))

    def test_never_import_triggers(self):
        code, out = _run_with_prompt("never import star")
        self.assertIn("systemMessage", json.loads(out))


class TestPromptCheckActiveTask(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tasks_dir = os.path.join(self.tmpdir, ".ai", "tasks")
        os.makedirs(self.tasks_dir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write_task(self, filename, status, title, body):
        content = "---\nstatus: {}\ntitle: {}\n---\n{}".format(status, title, body)
        with open(os.path.join(self.tasks_dir, filename), "w", encoding="utf-8") as f:
            f.write(content)

    def test_active_task_injected_into_system_message(self):
        self._write_task(
            "task1.md", "in-progress", "Fix auth module",
            "- [x] Step 1 done\n- [ ] Step 2: update tests\n- [ ] Step 3: deploy\n",
        )
        code, out = _run_with_prompt("help", cwd=self.tmpdir)
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("systemMessage", data)
        self.assertIn("Fix auth module", data["systemMessage"])
        self.assertIn("Step 2: update tests", data["systemMessage"])
        self.assertNotIn("Step 1 done", data["systemMessage"])

    def test_active_task_all_unchecked_shown(self):
        body = "".join("- [ ] Step {}\n".format(i) for i in range(1, 9))
        self._write_task("task1.md", "in-progress", "Big task", body)
        _, out = _run_with_prompt("go", cwd=self.tmpdir)
        msg = json.loads(out)["systemMessage"]
        for i in range(1, 9):
            self.assertIn("Step {}".format(i), msg)

    def test_no_active_task_no_system_message_for_plain_prompt(self):
        self._write_task("task1.md", "done", "Old task", "- [x] Done\n")
        code, out = _run_with_prompt("just a question", cwd=self.tmpdir)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {})

    def test_keyword_match_and_active_task_combined(self):
        self._write_task("task1.md", "in-progress", "My task", "- [ ] Do thing\n")
        _, out = _run_with_prompt("always use type hints", cwd=self.tmpdir)
        msg = json.loads(out)["systemMessage"]
        self.assertIn("copilot-instructions.md", msg)
        self.assertIn("My task", msg)

    def test_multiple_active_tasks_all_shown(self):
        """Both in-progress task titles and unchecked steps appear in systemMessage."""
        self._write_task("a_task1.md", "in-progress", "First task", "- [ ] Step A\n")
        self._write_task("b_task2.md", "in-progress", "Second task", "- [ ] Step B\n")
        _, out = _run_with_prompt("help", cwd=self.tmpdir)
        msg = json.loads(out)["systemMessage"]
        self.assertIn("First task", msg)
        self.assertIn("Step A", msg)
        self.assertIn("Second task", msg)
        self.assertIn("Step B", msg)


if __name__ == "__main__":
    unittest.main()
