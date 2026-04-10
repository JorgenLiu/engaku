import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_validate import run


GOOD_CONTENT = (
    "---\npaths:\n  - src/auth.py\n---\n\n"
    "## Overview\n\n"
    "The auth module handles user authentication, including JWT token generation, "
    "validation, and refresh. AuthService encapsulates all auth logic and depends "
    "on Redis for token blacklist storage."
)


class TestValidate(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmpdir)
        os.makedirs(".ai/modules")

    def tearDown(self):
        os.chdir(self.orig_cwd)
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_module(self, name, content, mtime=None):
        path = os.path.join(".ai", "modules", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        if mtime is not None:
            os.utime(path, (mtime, mtime))
        return path

    def _capture_run(self, recent=False):
        import io
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            code = run(recent=recent)
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err
        return code, buf_out.getvalue(), buf_err.getvalue()

    def test_good_file_passes(self):
        self._write_module("auth.md", GOOD_CONTENT)
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("[OK]", out)

    def test_missing_heading_fails(self):
        self._write_module(
            "auth.md",
            "---\npaths:\n  - src/auth.py\n---\n\n"
            "This is the auth module handling user authentication and JWT token management." * 2,
        )
        code, _, err = self._capture_run()
        self.assertEqual(code, 2)
        self.assertIn("Overview", err)

    def test_too_short_fails(self):
        self._write_module("auth.md", "---\npaths:\n  - src/auth.py\n---\n\n## Overview\n\nToo short.")
        code, _, err = self._capture_run()
        self.assertEqual(code, 2)
        self.assertIn("too short", err)

    def test_forbidden_phrase_fails(self):
        body = (
            "## Overview\n\n"
            "The auth module handles user authentication, including JWT token generation, "
            "validation, and refresh. AuthService encapsulates all auth logic and depends "
            "on Redis for token blacklist storage."
            "\n\nupdated the logic."
        )
        content = "---\npaths:\n  - src/auth.py\n---\n\n" + body
        self._write_module("auth.md", content)
        code, _, err = self._capture_run()
        self.assertEqual(code, 2)
        self.assertIn("forbidden phrase", err)

    def test_too_long_fails(self):
        long_content = "---\npaths:\n  - src/auth.py\n---\n\n## Overview\n\n" + "This module handles a lot of important logic. " * 34
        self._write_module("auth.md", long_content)
        code, _, err = self._capture_run()
        self.assertEqual(code, 2)
        self.assertIn("too long", err)

    def test_frontmatter_excluded_from_char_count(self):
        # frontmatter with many chars should not count toward the limit
        fat_fm = "---\npaths:\n" + "  - src/some/path.py\n" * 10 + "---\n\n"
        self._write_module("mod.md", fat_fm + GOOD_CONTENT)
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("[OK]", out)

    def test_frontmatter_body_must_have_heading(self):
        # heading absent from body (even if present in frontmatter) should fail
        content = (
            "---\npaths:\n  - src/auth.py\n---\n\n"
            "No heading here but this line has enough content to satisfy the "
            "minimum character threshold easily without a heading."
        )
        self._write_module("mod.md", content)
        code, _, err = self._capture_run()
        self.assertEqual(code, 2)
        self.assertIn("Overview", err)

    def test_file_with_paths_frontmatter_passes(self):
        content = (
            "---\npaths:\n  - src/engaku/cmd_validate.py\n---\n\n"
            + GOOD_CONTENT
        )
        self._write_module("mod.md", content)
        code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("[OK]", out)

    def test_recent_skips_old_files(self):
        old_time = time.time() - 700  # older than 10 min
        # Write a bad file but stamp it as old
        self._write_module(
            "old.md",
            "## Overview\n\nToo short.",
            mtime=old_time,
        )
        # With --recent, old file should be skipped → exit 0
        code, _, _ = self._capture_run(recent=True)
        self.assertEqual(code, 0)

    def test_no_modules_dir_passes(self):
        import shutil
        shutil.rmtree(".ai/modules")
        code, _, _ = self._capture_run()
        self.assertEqual(code, 0)

    def test_missing_frontmatter_fails(self):
        # Module file with no frontmatter at all → fail
        body = (
            "## Overview\n\n"
            "The auth module handles user authentication, including JWT token "
            "generation, validation, and refresh flows."
        )
        self._write_module("auth.md", body)
        code, _, err = self._capture_run()
        self.assertEqual(code, 2)
        self.assertIn("missing paths: frontmatter", err)

    def test_frontmatter_without_paths_key_fails(self):
        # Frontmatter exists but has no paths: key → fail
        content = (
            "---\ndescription: auth module\n---\n\n"
            "## Overview\n\n"
            "The auth module handles JWT generation, validation, and refresh."
        )
        self._write_module("auth.md", content)
        code, _, err = self._capture_run()
        self.assertEqual(code, 2)
        self.assertIn("paths: list is empty", err)

    def test_empty_paths_list_fails(self):
        # Frontmatter with paths: key but no items → fail
        content = (
            "---\npaths:\n---\n\n"
            "## Overview\n\n"
            "The auth module handles JWT generation, validation, and refresh."
        )
        self._write_module("auth.md", content)
        code, _, err = self._capture_run()
        self.assertEqual(code, 2)
        self.assertIn("paths: list is empty", err)


if __name__ == "__main__":
    unittest.main()
