import io
import json
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import engaku.cmd_check_update as mod


class TestCheckUpdate(unittest.TestCase):
    """Integration-style tests for run() using real temp directories."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        os.makedirs(os.path.join(self.tmpdir, ".ai", "modules"))
        os.makedirs(os.path.join(self.tmpdir, "src"))

    def tearDown(self):
        os.chdir(self.orig_cwd)
        import shutil
        shutil.rmtree(self.tmpdir)

    def _run(self, hook_input=None, changed_files=None):
        """Invoke run() with patched _get_changed_files; return (code, stdout, stderr)."""
        stdin_data = json.dumps(hook_input) if hook_input else ""
        orig_stdin, orig_stdout, orig_stderr = sys.stdin, sys.stdout, sys.stderr
        sys.stdin = io.StringIO(stdin_data)
        buf_out, buf_err = io.StringIO(), io.StringIO()
        sys.stdout, sys.stderr = buf_out, buf_err

        orig_get = mod._get_changed_files
        mod._get_changed_files = lambda cwd, hook_input=None: (changed_files if changed_files is not None else [])
        try:
            code = mod.run()
        finally:
            sys.stdin, sys.stdout, sys.stderr = orig_stdin, orig_stdout, orig_stderr
            mod._get_changed_files = orig_get
        return code, buf_out.getvalue(), buf_err.getvalue()

    def _write_module(self, name, paths, mtime=None):
        content = "---\npaths:\n{}\n---\n## Overview\nTest.\n".format(
            "\n".join("  - " + p for p in paths)
        )
        path = os.path.join(self.tmpdir, ".ai", "modules", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        if mtime is not None:
            os.utime(path, (mtime, mtime))
        return path

    def _write_src(self, name, mtime=None):
        path = os.path.join(self.tmpdir, "src", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# code\n")
        if mtime is not None:
            os.utime(path, (mtime, mtime))
        return path

    def _write_config(self, data):
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data))

    # ------------------------------------------------------------------
    # Basic guards

    def test_stop_hook_active_exits_zero(self):
        code, _, _ = self._run(
            hook_input={"stop_hook_active": True},
            changed_files=["src/main.py"],
        )
        self.assertEqual(code, 0)

    def test_no_code_changes_exits_zero(self):
        code, _, _ = self._run(changed_files=[])
        self.assertEqual(code, 0)

    def test_only_config_files_exits_zero(self):
        code, _, _ = self._run(
            changed_files=[".gitignore", "README.md", "pyproject.toml"]
        )
        self.assertEqual(code, 0)

    # ------------------------------------------------------------------
    # Case 1: empty modules directory

    def test_empty_modules_exits_zero_with_system_message(self):
        # No .md files in modules/
        code, out, err = self._run(changed_files=["src/auth.py"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertIn("systemMessage", data)
        self.assertIn("scanner", data["systemMessage"])

    # ------------------------------------------------------------------
    # Case 2: claimed files, module stale → hard block

    def test_claimed_stale_exits_two(self):
        t_old = time.time() - 100
        t_new = time.time()
        self._write_src("auth.py", mtime=t_new)
        self._write_module("auth.md", ["src/auth.py"], mtime=t_old)
        code, _, err = self._run(changed_files=["src/auth.py"])
        self.assertEqual(code, 2)
        self.assertIn("auth.py", err)
        self.assertIn("auth", err)

    def test_claimed_updated_exits_zero(self):
        t_old = time.time() - 100
        t_new = time.time()
        self._write_src("auth.py", mtime=t_old)
        self._write_module("auth.md", ["src/auth.py"], mtime=t_new)
        code, _, _ = self._run(changed_files=["src/auth.py"])
        self.assertEqual(code, 0)

    def test_block_message_names_stale_modules(self):
        t_old = time.time() - 100
        t_new = time.time()
        self._write_src("auth.py", mtime=t_new)
        self._write_src("payment.py", mtime=t_new)
        self._write_module("auth.md", ["src/auth.py"], mtime=t_old)
        self._write_module("payment.md", ["src/payment.py"], mtime=t_old)
        _, _, err = self._run(changed_files=["src/auth.py", "src/payment.py"])
        self.assertIn("auth", err)
        self.assertIn("payment", err)

    # ------------------------------------------------------------------
    # Case 3: unclaimed files → block with scanner-update guidance

    def test_unclaimed_files_exits_zero_with_block_decision(self):
        # Module exists but doesn't cover the changed file
        self._write_config({"check_update": {"uncovered_action": "block"}})
        self._write_module("other.md", ["src/other.py"])
        code, out, err = self._run(changed_files=["src/new_feature.py"])
        self.assertEqual(code, 0)
        self.assertIn("new_feature.py", err)
        data = json.loads(out)
        self.assertIn("hookSpecificOutput", data)
        ho = data["hookSpecificOutput"]
        self.assertEqual(ho["decision"], "block")
        self.assertIn("scanner-update", ho["reason"])
        self.assertIn("new_feature.py", ho["reason"])

    def test_unclaimed_plus_claimed_updated_yields_unclaimed_block(self):
        # claimed file is up to date; unclaimed file also present
        self._write_config({"check_update": {"uncovered_action": "block"}})
        t_old = time.time() - 100
        t_new = time.time()
        self._write_src("auth.py", mtime=t_old)
        self._write_module("auth.md", ["src/auth.py"], mtime=t_new)
        code, out, _ = self._run(changed_files=["src/auth.py", "src/new.py"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["hookSpecificOutput"]["decision"], "block")
        self.assertIn("new.py", data["hookSpecificOutput"]["reason"])

    def test_unclaimed_plus_claimed_stale_yields_hard_block(self):
        # claimed file is stale — hard block takes priority over unclaimed notice
        t_old = time.time() - 100
        t_new = time.time()
        self._write_src("auth.py", mtime=t_new)
        self._write_module("auth.md", ["src/auth.py"], mtime=t_old)
        code, _, err = self._run(changed_files=["src/auth.py", "src/new.py"])
        self.assertEqual(code, 2)
        self.assertIn("auth.py", err)

    def test_config_ignore_filters_files(self):
        # Files under docs/ must be filtered when docs/ is in config ignore list
        self._write_config({"check_update": {"ignore": ["docs/"]}})
        self._write_module("other.md", ["src/other.py"])
        code, out, err = self._run(changed_files=["docs/design.md"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_uncovered_action_warn(self):
        # warn (default): systemMessage output, no block, exit 0
        self._write_config({"check_update": {"uncovered_action": "warn"}})
        self._write_module("other.md", ["src/other.py"])
        code, out, err = self._run(changed_files=["src/new_feature.py"])
        self.assertEqual(code, 0)
        self.assertIn("new_feature.py", err)
        data = json.loads(out)
        self.assertIn("systemMessage", data)
        self.assertNotIn("hookSpecificOutput", data)
        self.assertIn("new_feature.py", data["systemMessage"])

    def test_uncovered_action_ignore(self):
        # ignore: no output at all for uncovered files
        self._write_config({"check_update": {"uncovered_action": "ignore"}})
        self._write_module("other.md", ["src/other.py"])
        code, out, err = self._run(changed_files=["src/new_feature.py"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "")

    def test_unclaimed_stderr_lists_files_and_scanner_hint(self):
        # stderr must name the unclaimed files and mention scanner agent
        self._write_config({"check_update": {"uncovered_action": "warn"}})
        self._write_module("other.md", ["src/other.py"])
        _, _, err = self._run(changed_files=["src/alpha.py", "src/beta.py"])
        self.assertIn("src/alpha.py", err)
        self.assertIn("src/beta.py", err)
        self.assertIn("scanner", err)


class TestGetChangedFilesFallback(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".ai", "modules"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_transcript_returns_last_turn_edits(self):
        import tempfile
        import json as _json
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            self._transcript_path = f.name
            # edit in a prior turn
            f.write(_json.dumps({"type": "tool.execution_start", "data": {
                "toolCallId": "c0", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/old.py")}
            }}) + "\n")
            f.write(_json.dumps({"type": "tool.execution_complete", "data": {
                "toolCallId": "c0", "success": True
            }}) + "\n")
            f.write(_json.dumps({"type": "user.message", "data": {"content": "next"}}) + "\n")
            # edit in the current turn
            f.write(_json.dumps({"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/edited.py")}
            }}) + "\n")
            f.write(_json.dumps({"type": "tool.execution_complete", "data": {
                "toolCallId": "c1", "success": True
            }}) + "\n")
        try:
            result = mod._get_changed_files(
                self.tmpdir, hook_input={"transcript_path": self._transcript_path}
            )
        finally:
            os.unlink(self._transcript_path)

        self.assertEqual(result, ["src/edited.py"])

    def test_no_transcript_returns_empty(self):
        result = mod._get_changed_files(self.tmpdir, hook_input={})
        self.assertEqual(result, [])

    def test_missing_hook_input_returns_empty(self):
        result = mod._get_changed_files(self.tmpdir, hook_input=None)
        self.assertEqual(result, [])


class TestIsCodeFile(unittest.TestCase):
    # ── tracked: source files of all flavours ────────────────────────────────
    def test_python_is_code(self):
        self.assertTrue(mod._is_code_file("src/engaku/cli.py"))

    def test_go_is_code(self):
        self.assertTrue(mod._is_code_file("cmd/server/main.go"))

    def test_rust_is_code(self):
        self.assertTrue(mod._is_code_file("src/main.rs"))

    def test_typescript_is_code(self):
        self.assertTrue(mod._is_code_file("src/index.ts"))

    def test_dart_is_code(self):
        self.assertTrue(mod._is_code_file("lib/main.dart"))

    def test_dockerfile_is_code(self):
        self.assertTrue(mod._is_code_file("Dockerfile"))

    def test_makefile_is_code(self):
        self.assertTrue(mod._is_code_file("Makefile"))

    def test_yaml_workflow_is_code(self):
        self.assertTrue(mod._is_code_file(".github/workflows/ci.yml"))

    def test_toml_is_code(self):
        self.assertTrue(mod._is_code_file("pyproject.toml"))

    def test_markdown_is_code(self):
        self.assertTrue(mod._is_code_file("README.md"))

    def test_docs_markdown_is_code(self):
        self.assertTrue(mod._is_code_file("docs/design.md"))

    def test_json_config_is_code(self):
        self.assertTrue(mod._is_code_file("tsconfig.json"))

    def test_gitignore_is_code(self):
        self.assertTrue(mod._is_code_file(".gitignore"))

    def test_template_md_is_code(self):
        self.assertTrue(mod._is_code_file("src/engaku/templates/ai/rules.md"))

    def test_template_json_is_code(self):
        self.assertTrue(mod._is_code_file("src/engaku/templates/hooks/edit-log.json"))

    # ── NOT tracked: build artefacts and generated files ─────────────────────
    def test_pyc_is_not_code(self):
        self.assertFalse(mod._is_code_file("src/__pycache__/cli.cpython-312.pyc"))

    def test_pycache_dir_is_not_code(self):
        self.assertFalse(mod._is_code_file("src/engaku/__pycache__/cmd_init.pyc"))

    def test_venv_is_not_code(self):
        self.assertFalse(mod._is_code_file(".venv/lib/python3.11/site.py"))

    def test_node_modules_is_not_code(self):
        self.assertFalse(mod._is_code_file("node_modules/lodash/index.js"))

    def test_rust_target_is_not_code(self):
        self.assertFalse(mod._is_code_file("target/debug/main"))

    def test_dart_tool_is_not_code(self):
        self.assertFalse(mod._is_code_file(".dart_tool/package_config.json"))

    def test_egg_info_is_not_code(self):
        self.assertFalse(mod._is_code_file("mypackage.egg-info/PKG-INFO"))

    def test_next_build_is_not_code(self):
        self.assertFalse(mod._is_code_file(".next/cache/webpack/client.pack"))

    def test_dist_is_not_code(self):
        self.assertFalse(mod._is_code_file("dist/bundle.js"))

    def test_package_lock_is_not_code(self):
        self.assertFalse(mod._is_code_file("package-lock.json"))

    def test_cargo_lock_is_not_code(self):
        self.assertFalse(mod._is_code_file("Cargo.lock"))

    def test_poetry_lock_is_not_code(self):
        self.assertFalse(mod._is_code_file("poetry.lock"))

    def test_go_sum_is_not_code(self):
        self.assertFalse(mod._is_code_file("go.sum"))

    def test_pubspec_lock_is_not_code(self):
        self.assertFalse(mod._is_code_file("pubspec.lock"))

    def test_ds_store_is_not_code(self):
        self.assertFalse(mod._is_code_file(".DS_Store"))

    def test_png_is_not_code(self):
        self.assertFalse(mod._is_code_file("assets/icon.png"))

    def test_env_is_not_code(self):
        self.assertFalse(mod._is_code_file(".env"))

    def test_ai_module_is_not_code(self):
        # .ai/ knowledge files must not be treated as source changes
        self.assertFalse(mod._is_code_file(".ai/modules/quality.md"))


class TestSuggestModules(unittest.TestCase):
    def test_extracts_basename_stem(self):
        result = mod._suggest_modules(["src/engaku/cmd_check_update.py"])
        self.assertEqual(result, ["cmd_check_update"])

    def test_deduplicates(self):
        result = mod._suggest_modules(["src/auth.py", "tests/auth.py"])
        self.assertEqual(result, ["auth"])

    def test_multiple_modules(self):
        result = mod._suggest_modules(["src/auth.py", "src/payment.py"])
        self.assertEqual(result, ["auth", "payment"])

    def test_empty_input(self):
        self.assertEqual(mod._suggest_modules([]), [])


class TestLoadModulePaths(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".ai", "modules"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_module(self, name, content):
        path = os.path.join(self.tmpdir, ".ai", "modules", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_returns_empty_when_no_modules(self):
        result = mod._load_module_paths(self.tmpdir)
        self.assertEqual(result, {})

    def test_parses_single_path(self):
        self._write_module(
            "auth.md",
            "---\npaths:\n  - src/auth.py\n---\n\n## Overview\n",
        )
        result = mod._load_module_paths(self.tmpdir)
        self.assertIn("auth", result)
        self.assertIn("src/auth.py", result["auth"])

    def test_parses_multiple_paths(self):
        self._write_module(
            "auth.md",
            "---\npaths:\n  - src/auth.py\n  - src/auth_utils.py\n---\n\n## Overview\n",
        )
        result = mod._load_module_paths(self.tmpdir)
        self.assertEqual(sorted(result["auth"]), ["src/auth.py", "src/auth_utils.py"])

    def test_ignores_files_without_frontmatter(self):
        self._write_module("auth.md", "## Overview\nNo frontmatter here.")
        result = mod._load_module_paths(self.tmpdir)
        self.assertEqual(result, {})

    def test_ignores_frontmatter_without_paths_key(self):
        self._write_module(
            "auth.md",
            "---\ndescription: auth module\n---\n\n## Overview\n",
        )
        result = mod._load_module_paths(self.tmpdir)
        self.assertEqual(result, {})


class TestMatchPath(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(mod._match_path("src/auth.py", "src/auth.py"))

    def test_no_match(self):
        self.assertFalse(mod._match_path("src/auth.py", "src/payment.py"))

    def test_directory_prefix_with_trailing_slash(self):
        self.assertTrue(mod._match_path("src/engaku/cli.py", "src/engaku/"))

    def test_directory_prefix_without_trailing_slash(self):
        self.assertTrue(mod._match_path("src/engaku/cli.py", "src/engaku"))

    def test_directory_prefix_does_not_match_sibling(self):
        self.assertFalse(mod._match_path("src/engaku_extra/x.py", "src/engaku"))

    def test_glob_star(self):
        self.assertTrue(mod._match_path("src/engaku/cmd_init.py", "src/engaku/cmd_*.py"))

    def test_glob_no_match(self):
        self.assertFalse(mod._match_path("src/engaku/cli.py", "src/engaku/cmd_*.py"))

    def test_glob_question_mark(self):
        self.assertTrue(mod._match_path("src/a1.py", "src/a?.py"))


class TestClassifyFiles(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".ai", "modules"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_module(self, name, paths):
        content = "---\npaths:\n{}\n---\n## Overview\nTest.\n".format(
            "\n".join("  - " + p for p in paths)
        )
        path = os.path.join(self.tmpdir, ".ai", "modules", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_all_claimed(self):
        self._write_module("auth.md", ["src/auth.py"])
        claimed, unclaimed = mod._classify_files(self.tmpdir, ["src/auth.py"])
        self.assertIn("auth", claimed)
        self.assertEqual(unclaimed, [])

    def test_all_unclaimed(self):
        self._write_module("auth.md", ["src/auth.py"])
        claimed, unclaimed = mod._classify_files(self.tmpdir, ["src/new.py"])
        self.assertEqual(claimed, {})
        self.assertEqual(unclaimed, ["src/new.py"])

    def test_mixed(self):
        self._write_module("auth.md", ["src/auth.py"])
        claimed, unclaimed = mod._classify_files(
            self.tmpdir, ["src/auth.py", "src/new.py"]
        )
        self.assertIn("auth", claimed)
        self.assertIn("src/auth.py", claimed["auth"])
        self.assertEqual(unclaimed, ["src/new.py"])

    def test_glob_pattern_claims_file(self):
        self._write_module("hooks.md", ["src/engaku/cmd_*.py"])
        claimed, unclaimed = mod._classify_files(
            self.tmpdir, ["src/engaku/cmd_init.py"]
        )
        self.assertIn("hooks", claimed)
        self.assertEqual(unclaimed, [])

    def test_no_modules_all_unclaimed(self):
        claimed, unclaimed = mod._classify_files(self.tmpdir, ["src/auth.py"])
        self.assertEqual(claimed, {})
        self.assertEqual(unclaimed, ["src/auth.py"])


class TestClaimedModulesUpdated(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".ai", "modules"))
        os.makedirs(os.path.join(self.tmpdir, "src"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_module(self, name, mtime=None):
        path = os.path.join(self.tmpdir, ".ai", "modules", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("## Overview\nTest.\n")
        if mtime is not None:
            os.utime(path, (mtime, mtime))

    def _write_code(self, name, mtime=None):
        path = os.path.join(self.tmpdir, "src", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# code\n")
        if mtime is not None:
            os.utime(path, (mtime, mtime))

    def test_updated_module_returns_true(self):
        t = time.time()
        self._write_code("auth.py", mtime=t - 10)
        self._write_module("auth.md", mtime=t)
        result = mod._claimed_modules_updated(
            self.tmpdir,
            {"auth": ["src/auth.py"]},
            ["src/auth.py"],
        )
        self.assertTrue(result)

    def test_stale_module_returns_false(self):
        t = time.time()
        self._write_code("auth.py", mtime=t)
        self._write_module("auth.md", mtime=t - 10)
        result = mod._claimed_modules_updated(
            self.tmpdir,
            {"auth": ["src/auth.py"]},
            ["src/auth.py"],
        )
        self.assertFalse(result)

    def test_missing_module_file_returns_false(self):
        t = time.time()
        self._write_code("auth.py", mtime=t)
        # No auth.md written
        result = mod._claimed_modules_updated(
            self.tmpdir,
            {"auth": ["src/auth.py"]},
            ["src/auth.py"],
        )
        self.assertFalse(result)

    def test_one_stale_among_two_returns_false(self):
        t = time.time()
        self._write_code("auth.py", mtime=t)
        self._write_code("payment.py", mtime=t)
        self._write_module("auth.md", mtime=t + 1)    # fresh
        self._write_module("payment.md", mtime=t - 10)  # stale
        result = mod._claimed_modules_updated(
            self.tmpdir,
            {"auth": ["src/auth.py"], "payment": ["src/payment.py"]},
            ["src/auth.py", "src/payment.py"],
        )
        self.assertFalse(result)


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmpdir, ".ai"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_config(self, data):
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(data))

    def test_defaults_when_no_config_file(self):
        from engaku.utils import load_config
        config = load_config(self.tmpdir)
        self.assertEqual(config["agents"], {})
        self.assertEqual(config["max_chars"], 1500)
        self.assertEqual(config["check_update"]["ignore"], [])
        self.assertEqual(config["check_update"]["uncovered_action"], "warn")

    def test_partial_config_falls_back_to_defaults(self):
        from engaku.utils import load_config
        self._write_config({"agents": {"dev": "some-model"}})
        config = load_config(self.tmpdir)
        self.assertEqual(config["agents"], {"dev": "some-model"})
        self.assertEqual(config["max_chars"], 1500)
        self.assertEqual(config["check_update"]["ignore"], [])
        self.assertEqual(config["check_update"]["uncovered_action"], "warn")

    def test_custom_values_override_defaults(self):
        from engaku.utils import load_config
        self._write_config({
            "max_chars": 800,
            "check_update": {"ignore": ["docs/"], "uncovered_action": "block"},
        })
        config = load_config(self.tmpdir)
        self.assertEqual(config["max_chars"], 800)
        self.assertEqual(config["check_update"]["ignore"], ["docs/"])
        self.assertEqual(config["check_update"]["uncovered_action"], "block")

    def test_invalid_json_uses_defaults(self):
        from engaku.utils import load_config
        config_path = os.path.join(self.tmpdir, ".ai", "engaku.json")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("not-valid-json")
        config = load_config(self.tmpdir)
        self.assertEqual(config["max_chars"], 1500)
        self.assertEqual(config["check_update"]["uncovered_action"], "warn")


if __name__ == "__main__":
    unittest.main()
