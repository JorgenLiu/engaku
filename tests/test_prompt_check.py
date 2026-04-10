"""Tests for engaku prompt-check."""
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import engaku.cmd_prompt_check as mod


def _run_with_prompt(prompt):
    """Call run() with the given prompt string; return (exit_code, stdout)."""
    hook_input = {"prompt": prompt} if prompt is not None else {}
    stdin_data = json.dumps(hook_input)
    orig_stdin, orig_stdout = sys.stdin, sys.stdout
    sys.stdin = io.StringIO(stdin_data)
    buf = io.StringIO()
    sys.stdout = buf
    try:
        code = mod.run()
    finally:
        sys.stdin, sys.stdout = orig_stdin, orig_stdout
    return code, buf.getvalue()


class TestPromptCheck(unittest.TestCase):

    # ── keyword matches ───────────────────────────────────────────────────────

    def test_always_triggers(self):
        code, out = _run_with_prompt("always use type hints")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("systemMessage", data)
        self.assertIn("rules.md", data["systemMessage"])

    def test_never_triggers(self):
        code, out = _run_with_prompt("never import star")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_rule_english_triggers(self):
        code, out = _run_with_prompt("add a rule: no magic numbers")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_rule_english_case_insensitive(self):
        code, out = _run_with_prompt("Follow this Rule in all modules")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_constraint_triggers(self):
        code, out = _run_with_prompt("there is a new constraint on imports")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_preference_triggers(self):
        code, out = _run_with_prompt("my preference is to use f-strings")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_chinese_rule_triggers(self):
        code, out = _run_with_prompt("规则：所有函数必须有类型注解")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_chinese_cong_xianzai_kaishi_triggers(self):
        code, out = _run_with_prompt("从现在开始，禁止使用全局变量")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    def test_chinese_biyao_triggers(self):
        code, out = _run_with_prompt("这个函数必须返回字符串")
        self.assertEqual(code, 0)
        self.assertIn("systemMessage", json.loads(out))

    # ── no keyword match ──────────────────────────────────────────────────────

    def test_plain_prompt_no_match(self):
        code, out = _run_with_prompt("fix the bug in auth.py")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {})

    def test_empty_prompt_no_match(self):
        code, out = _run_with_prompt("")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {})

    def test_no_prompt_field_no_match(self):
        """Missing prompt key in hook_input should produce empty output."""
        orig_stdin, orig_stdout = sys.stdin, sys.stdout
        sys.stdin = io.StringIO(json.dumps({}))
        buf = io.StringIO()
        sys.stdout = buf
        try:
            code = mod.run()
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
            code = mod.run()
        finally:
            sys.stdin, sys.stdout = orig_stdin, orig_stdout
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(buf.getvalue()), {})

    def test_always_exits_zero(self):
        """Should never return non-zero regardless of input."""
        for prompt in ["always fail", "just a question", ""]:
            code, _ = _run_with_prompt(prompt)
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
