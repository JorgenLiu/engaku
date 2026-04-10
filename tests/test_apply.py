"""Tests for engaku apply."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_apply import run, _update_agent_model, _update_rules_max_chars


class TestApply(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.agents_dir = os.path.join(self.tmpdir, ".github", "agents")
        os.makedirs(self.agents_dir)
        ai_dir = os.path.join(self.tmpdir, ".ai")
        os.makedirs(ai_dir)
        self.config_path = os.path.join(ai_dir, "engaku.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_config(self, agents):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"agents": agents}, f)

    def _write_agent(self, name, content):
        path = os.path.join(self.agents_dir, "{}.agent.md".format(name))
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _read_agent(self, name):
        path = os.path.join(self.agents_dir, "{}.agent.md".format(name))
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _capture_run(self, cwd=None):
        import io
        buf_out, buf_err = io.StringIO(), io.StringIO()
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            code = run(cwd=cwd or self.tmpdir)
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err
        return code, buf_out.getvalue(), buf_err.getvalue()

    # ------------------------------------------------------------------

    def test_no_config_file_returns_error(self):
        code, _, err = self._capture_run()
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_inserts_model_into_agent_without_model_field(self):
        self._write_config({"dev": "claude-sonnet-4-5 (copilot)"})
        self._write_agent("dev", "---\nname: dev\ntools: ['edit']\n---\n\nDo work.\n")
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("model: ['claude-sonnet-4-5 (copilot)']", self._read_agent("dev"))
        self.assertIn("[updated]", out)

    def test_updates_existing_model_field(self):
        self._write_config({"keeper": "gpt-4o-mini (copilot)"})
        self._write_agent(
            "keeper",
            "---\nname: keeper\nmodel: ['old-model (copilot)']\n---\n\nBody.\n",
        )
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        content = self._read_agent("keeper")
        self.assertIn("model: ['gpt-4o-mini (copilot)']", content)
        self.assertNotIn("old-model", content)
        self.assertIn("[updated]", out)

    def test_skips_missing_agent_file(self):
        self._write_config({"nonexistent": "gpt-4o (copilot)"})
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("[skip]", out)
        self.assertIn("file not found", out)

    def test_model_inserted_after_name_field(self):
        self._write_config({"dev": "claude-sonnet-4-5 (copilot)"})
        self._write_agent("dev", "---\nname: dev\ndescription: A dev agent\n---\n\nBody.\n")
        self._capture_run()
        lines = self._read_agent("dev").split("\n")
        name_idx = next(i for i, l in enumerate(lines) if l.startswith("name:"))
        model_idx = next(i for i, l in enumerate(lines) if l.startswith("model:"))
        self.assertEqual(model_idx, name_idx + 1)

    def test_no_change_when_model_already_correct(self):
        self._write_config({"dev": "claude-sonnet-4-5 (copilot)"})
        original = "---\nname: dev\nmodel: ['claude-sonnet-4-5 (copilot)']\n---\n\nBody.\n"
        self._write_agent("dev", original)
        self._capture_run()
        self.assertEqual(self._read_agent("dev"), original)

    def test_empty_agents_config_exits_zero(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"agents": {}}, f)
        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)

    def test_invalid_json_returns_error(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")
        code, _, err = self._capture_run()
        self.assertEqual(code, 1)
        self.assertIn("invalid JSON", err)

    def test_agent_without_frontmatter_is_skipped(self):
        self._write_config({"dev": "claude-sonnet-4-5 (copilot)"})
        self._write_agent("dev", "No frontmatter here.\n")
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("[skip]", out)
        self.assertIn("no frontmatter", out)


class TestUpdateRulesMaxChars(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.rules_path = os.path.join(self.tmpdir, ".ai", "rules.md")
        os.makedirs(os.path.dirname(self.rules_path))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_rules(self, content):
        with open(self.rules_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _read_rules(self):
        with open(self.rules_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_updates_max_chars_value(self):
        self._write_rules("## Agent Configuration\n- MAX_CHARS for module knowledge body: 1200 (frontmatter excluded).\n")
        changed, reason = _update_rules_max_chars(self.rules_path, 1500)
        self.assertTrue(changed)
        self.assertIn("MAX_CHARS for module knowledge body: 1500", self._read_rules())

    def test_no_change_when_value_already_matches(self):
        self._write_rules("## Agent Configuration\n- MAX_CHARS for module knowledge body: 1500 (frontmatter excluded).\n")
        changed, reason = _update_rules_max_chars(self.rules_path, 1500)
        self.assertFalse(changed)
        self.assertEqual(reason, "no change")

    def test_missing_rules_file_returns_not_changed(self):
        changed, reason = _update_rules_max_chars("/nonexistent/rules.md", 1500)
        self.assertFalse(changed)
        self.assertEqual(reason, "file not found")

    def test_rules_without_max_chars_line_returns_no_change(self):
        self._write_rules("## Overview\nSome other content.\n")
        changed, reason = _update_rules_max_chars(self.rules_path, 1500)
        self.assertFalse(changed)
        self.assertEqual(reason, "no change")


class TestApplyMaxCharsIntegration(unittest.TestCase):
    """Integration: engaku apply syncs max_chars from engaku.json to rules.md."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        ai_dir = os.path.join(self.tmpdir, ".ai")
        os.makedirs(ai_dir)
        os.makedirs(os.path.join(self.tmpdir, ".github", "agents"))
        self.config_path = os.path.join(ai_dir, "engaku.json")
        self.rules_path = os.path.join(ai_dir, "rules.md")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _capture_run(self):
        import io
        buf_out, buf_err = io.StringIO(), io.StringIO()
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            code = run(cwd=self.tmpdir)
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err
        return code, buf_out.getvalue(), buf_err.getvalue()

    def test_max_chars_synced_to_rules_md(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"agents": {}, "max_chars": 1500}, f)
        with open(self.rules_path, "w", encoding="utf-8") as f:
            f.write("- MAX_CHARS for module knowledge body: 1200 (frontmatter excluded).\n")
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("[updated]", out)
        self.assertIn("MAX_CHARS", out)
        with open(self.rules_path, encoding="utf-8") as f:
            self.assertIn("1500", f.read())

    def test_max_chars_skip_when_already_correct(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"agents": {}, "max_chars": 1500}, f)
        with open(self.rules_path, "w", encoding="utf-8") as f:
            f.write("- MAX_CHARS for module knowledge body: 1500 (frontmatter excluded).\n")
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("[skip]", out)
