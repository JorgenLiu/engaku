"""Tests for engaku setup-serena."""
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.cmd_setup_serena import (
    _find_uv,
    _install_uv_via_pip,
    _find_uv_after_install,
    _install_serena,
    _find_serena_executable,
    _validate_serena,
    _run_serena_init,
    _patch_mcp_json,
    run,
)


class TestFindUv(unittest.TestCase):
    def test_returns_path_when_uv_on_path(self):
        with mock.patch("shutil.which", return_value="/usr/local/bin/uv"):
            self.assertEqual(_find_uv(), "/usr/local/bin/uv")

    def test_returns_none_when_uv_not_on_path(self):
        with mock.patch("shutil.which", return_value=None):
            self.assertIsNone(_find_uv())


class TestInstallUvViaPip(unittest.TestCase):
    def test_returns_true_on_success(self):
        mock_result = mock.Mock()
        mock_result.returncode = 0
        with mock.patch("subprocess.run", return_value=mock_result):
            self.assertTrue(_install_uv_via_pip())

    def test_returns_false_on_failure(self):
        mock_result = mock.Mock()
        mock_result.returncode = 1
        with mock.patch("subprocess.run", return_value=mock_result):
            self.assertFalse(_install_uv_via_pip())

    def test_returns_false_on_os_error(self):
        with mock.patch("subprocess.run", side_effect=OSError("not found")):
            self.assertFalse(_install_uv_via_pip())

    def test_returns_false_on_timeout(self):
        import subprocess
        with mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pip", 120)):
            self.assertFalse(_install_uv_via_pip())


class TestInstallSerena(unittest.TestCase):
    def test_returns_true_empty_err_on_success(self):
        mock_result = mock.Mock()
        mock_result.returncode = 0
        mock_result.stderr = b""
        with mock.patch("subprocess.run", return_value=mock_result):
            ok, err = _install_serena("/usr/bin/uv")
        self.assertTrue(ok)
        self.assertEqual(err, "")

    def test_returns_false_with_err_on_failure(self):
        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = b"package not found"
        with mock.patch("subprocess.run", return_value=mock_result):
            ok, err = _install_serena("/usr/bin/uv")
        self.assertFalse(ok)
        self.assertIn("package not found", err)

    def test_returns_false_on_timeout(self):
        import subprocess
        with mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("uv", 300)):
            ok, err = _install_serena("/usr/bin/uv")
        self.assertFalse(ok)
        self.assertIn("timed out", err)

    def test_returns_false_on_os_error(self):
        with mock.patch("subprocess.run", side_effect=OSError("exec error")):
            ok, err = _install_serena("/usr/bin/uv")
        self.assertFalse(ok)
        self.assertIn("exec error", err)


class TestValidateSerena(unittest.TestCase):
    def test_returns_true_when_version_succeeds(self):
        mock_result = mock.Mock()
        mock_result.returncode = 0
        with mock.patch("subprocess.run", return_value=mock_result):
            self.assertTrue(_validate_serena("/usr/bin/serena"))

    def test_returns_false_when_both_flags_fail(self):
        mock_result = mock.Mock()
        mock_result.returncode = 1
        with mock.patch("subprocess.run", return_value=mock_result):
            self.assertFalse(_validate_serena("/usr/bin/serena"))

    def test_returns_false_on_os_error(self):
        with mock.patch("subprocess.run", side_effect=OSError):
            self.assertFalse(_validate_serena("/bad/path"))


class TestRunSerenaInit(unittest.TestCase):
    def test_returns_true_on_success(self):
        mock_result = mock.Mock()
        mock_result.returncode = 0
        mock_result.stderr = b""
        with mock.patch("subprocess.run", return_value=mock_result):
            ok, err = _run_serena_init("/usr/bin/serena", "/tmp")
        self.assertTrue(ok)

    def test_returns_false_with_err_on_failure(self):
        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = b"init failed"
        with mock.patch("subprocess.run", return_value=mock_result):
            ok, err = _run_serena_init("/usr/bin/serena", "/tmp")
        self.assertFalse(ok)
        self.assertIn("init failed", err)

    def test_returns_false_on_timeout(self):
        import subprocess
        with mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("serena", 60)):
            ok, err = _run_serena_init("/usr/bin/serena", "/tmp")
        self.assertFalse(ok)
        self.assertIn("timed out", err)


class TestPatchMcpJson(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.vscode_dir = os.path.join(self.tmpdir, ".vscode")
        os.makedirs(self.vscode_dir)
        self.mcp_path = os.path.join(self.vscode_dir, "mcp.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _write_mcp(self, data):
        with open(self.mcp_path, "w") as f:
            json.dump(data, f)

    def test_patches_command_when_serena_present(self):
        self._write_mcp({"servers": {"serena": {"type": "stdio", "command": "serena"}}})
        result = _patch_mcp_json(self.tmpdir, "/abs/path/serena")
        self.assertTrue(result)
        with open(self.mcp_path) as f:
            data = json.load(f)
        self.assertEqual(data["servers"]["serena"]["command"], "/abs/path/serena")

    def test_returns_false_when_no_change_needed(self):
        self._write_mcp({"servers": {"serena": {"command": "/abs/path/serena"}}})
        self.assertFalse(_patch_mcp_json(self.tmpdir, "/abs/path/serena"))

    def test_returns_false_when_no_mcp_json(self):
        self.assertFalse(_patch_mcp_json(self.tmpdir, "/abs/path/serena"))

    def test_returns_false_when_serena_not_in_servers(self):
        self._write_mcp({"servers": {"context7": {}}})
        self.assertFalse(_patch_mcp_json(self.tmpdir, "/abs/path/serena"))

    def test_returns_false_on_invalid_json(self):
        with open(self.mcp_path, "w") as f:
            f.write("{invalid json")
        self.assertFalse(_patch_mcp_json(self.tmpdir, "/abs/path/serena"))


class TestRun(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def _capture_run(self, **kwargs):
        import io
        buf_out, buf_err = io.StringIO(), io.StringIO()
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = buf_out, buf_err
        try:
            code = run(cwd=self.tmpdir, **kwargs)
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err
        return code, buf_out.getvalue(), buf_err.getvalue()

    def test_returns_zero_when_serena_already_installed(self):
        """If serena is on PATH, validate it and run init, both succeed."""
        mock_validate = mock.Mock(return_value=True)
        mock_init = mock.Mock(return_value=(True, ""))
        with mock.patch("shutil.which", return_value="/usr/bin/serena"), \
             mock.patch("engaku.cmd_setup_serena._validate_serena", mock_validate), \
             mock.patch("engaku.cmd_setup_serena._run_serena_init", mock_init):
            code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("already installed", out)

    def test_returns_nonzero_when_uv_not_found_and_pip_fails(self):
        """Returns 1 when called directly and uv cannot be installed."""
        with mock.patch("shutil.which", return_value=None), \
             mock.patch("engaku.cmd_setup_serena._install_uv_via_pip", return_value=False):
            code, _, err = self._capture_run()
        self.assertEqual(code, 1)
        self.assertIn("uv", err)

    def test_returns_zero_from_init_even_when_uv_fails(self):
        """When called from init, uv failure must not block (returns 0)."""
        with mock.patch("shutil.which", return_value=None), \
             mock.patch("engaku.cmd_setup_serena._install_uv_via_pip", return_value=False):
            code, _, err = self._capture_run(called_from_init=True)
        self.assertEqual(code, 0)
        self.assertIn("uv", err)

    def test_returns_nonzero_when_serena_install_fails(self):
        """Returns 1 when called directly and uv tool install fails."""
        with mock.patch("shutil.which", return_value=None), \
             mock.patch("engaku.cmd_setup_serena._find_uv", return_value="/usr/bin/uv"), \
             mock.patch("engaku.cmd_setup_serena._install_serena", return_value=(False, "network error")):
            code, _, err = self._capture_run()
        self.assertEqual(code, 1)
        self.assertIn("network error", err)

    def test_returns_zero_from_init_when_serena_install_fails(self):
        """called_from_init=True: serena install failure is a warning, not error."""
        with mock.patch("shutil.which", return_value=None), \
             mock.patch("engaku.cmd_setup_serena._find_uv", return_value="/usr/bin/uv"), \
             mock.patch("engaku.cmd_setup_serena._install_serena", return_value=(False, "network error")):
            code, _, err = self._capture_run(called_from_init=True)
        self.assertEqual(code, 0)
        self.assertIn("network error", err)

    def test_patches_mcp_json_with_absolute_path(self):
        """Absolute serena path is written to .vscode/mcp.json when present."""
        import subprocess
        vscode_dir = os.path.join(self.tmpdir, ".vscode")
        os.makedirs(vscode_dir)
        mcp_path = os.path.join(vscode_dir, "mcp.json")
        with open(mcp_path, "w") as f:
            json.dump({"servers": {"serena": {"type": "stdio", "command": "serena"}}}, f)

        mock_validate = mock.Mock(return_value=True)
        mock_init = mock.Mock(return_value=(True, ""))
        with mock.patch("shutil.which", return_value="/abs/path/to/serena"), \
             mock.patch("engaku.cmd_setup_serena._validate_serena", mock_validate), \
             mock.patch("engaku.cmd_setup_serena._run_serena_init", mock_init):
            code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        with open(mcp_path) as f:
            data = json.load(f)
        self.assertEqual(data["servers"]["serena"]["command"], "/abs/path/to/serena")

    def test_setup_complete_message_on_success(self):
        """run() prints 'Serena setup complete.' on full success."""
        mock_validate = mock.Mock(return_value=True)
        mock_init = mock.Mock(return_value=(True, ""))
        with mock.patch("shutil.which", return_value="/usr/bin/serena"), \
             mock.patch("engaku.cmd_setup_serena._validate_serena", mock_validate), \
             mock.patch("engaku.cmd_setup_serena._run_serena_init", mock_init):
            code, out, _ = self._capture_run()
        self.assertEqual(code, 0)
        self.assertIn("Serena setup complete", out)


if __name__ == "__main__":
    unittest.main()
