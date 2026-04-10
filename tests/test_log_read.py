"""Tests for engaku log-read (PostToolUse hook)."""
import os
import tempfile

import pytest

from engaku.cmd_log_read import run, _is_ai_file, _extract_file_path


def _make_project(tmp_path):
    """Create a minimal .ai/ project in tmp_path."""
    ai_dir = os.path.join(str(tmp_path), ".ai")
    os.makedirs(os.path.join(ai_dir, "modules"), exist_ok=True)
    return str(tmp_path)


def _read_log(cwd):
    log_path = os.path.join(cwd, ".ai", "access.log")
    if not os.path.exists(log_path):
        return []
    with open(log_path, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


# ---------------------------------------------------------------------------
# _extract_file_path
# ---------------------------------------------------------------------------

def test_extract_filePath_key():
    data = {"tool_input": {"filePath": "/some/file.md"}}
    assert _extract_file_path(data) == "/some/file.md"


def test_extract_path_key():
    data = {"tool_input": {"path": "/other/file.md"}}
    assert _extract_file_path(data) == "/other/file.md"


def test_extract_missing_tool_input():
    assert _extract_file_path({}) is None


# ---------------------------------------------------------------------------
# _is_ai_file
# ---------------------------------------------------------------------------

def test_is_ai_file_true(tmp_path):
    cwd = _make_project(tmp_path)
    assert _is_ai_file(".ai/modules/auth.md", cwd) is True


def test_is_ai_file_false_src(tmp_path):
    cwd = _make_project(tmp_path)
    assert _is_ai_file("src/main.py", cwd) is False


def test_is_ai_file_absolute(tmp_path):
    cwd = _make_project(tmp_path)
    abs_path = os.path.join(cwd, ".ai", "rules.md")
    assert _is_ai_file(abs_path, cwd) is True


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

def test_run_ai_file_logs_entry(tmp_path):
    cwd = _make_project(tmp_path)
    data = {
        "tool_input": {"filePath": ".ai/modules/auth.md"},
        "session_id": "sess1",
    }
    rc = run(cwd=cwd, stdin_data=data)
    assert rc == 0
    lines = _read_log(cwd)
    assert len(lines) == 1
    parts = lines[0].split("\t")
    assert len(parts) == 3
    assert parts[1] == os.path.join(".ai", "modules", "auth.md")
    assert parts[2] == "sess1"


def test_run_non_ai_file_does_not_log(tmp_path):
    cwd = _make_project(tmp_path)
    data = {"tool_input": {"filePath": "src/main.py"}, "session_id": "sess2"}
    rc = run(cwd=cwd, stdin_data=data)
    assert rc == 0
    assert _read_log(cwd) == []


def test_run_creates_log_if_absent(tmp_path):
    cwd = _make_project(tmp_path)
    log_path = os.path.join(cwd, ".ai", "access.log")
    assert not os.path.exists(log_path)
    run(cwd=cwd, stdin_data={"tool_input": {"filePath": ".ai/rules.md"}, "session_id": ""})
    assert os.path.exists(log_path)


def test_run_appends_multiple_entries(tmp_path):
    cwd = _make_project(tmp_path)
    for i in range(3):
        run(cwd=cwd, stdin_data={"tool_input": {"filePath": ".ai/rules.md"}, "session_id": str(i)})
    assert len(_read_log(cwd)) == 3


def test_run_empty_stdin_no_crash(tmp_path):
    cwd = _make_project(tmp_path)
    rc = run(cwd=cwd, stdin_data={})
    assert rc == 0
    assert _read_log(cwd) == []
