"""Tests for engaku.utils public functions."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from engaku.utils import parse_transcript_edits


def _write_transcript(path, events):
    with open(path, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


class TestParseTranscriptEdits(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.transcript = os.path.join(self.tmpdir, "transcript.json")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    # ── success cases ──────────────────────────────────────────────────────

    def test_replace_string_in_file_success(self):
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/auth.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, ["src/auth.py"])

    def test_create_file_success(self):
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "create_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/new.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, ["src/new.py"])

    def test_multi_replace_string_in_file_success(self):
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "multi_replace_string_in_file",
                "arguments": {"replacements": [
                    {"filePath": os.path.join(self.tmpdir, "src/a.py")},
                    {"filePath": os.path.join(self.tmpdir, "src/b.py")},
                ]}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, ["src/a.py", "src/b.py"])

    def test_apply_patch_success(self):
        patch_text = (
            "*** Begin Patch\n"
            "*** Update File: {}/src/quality.md\n"
            "@@ some diff\n"
            "*** End Patch"
        ).format(self.tmpdir)
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "apply_patch",
                "arguments": {"input": patch_text}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, ["src/quality.md"])

    def test_deduplicates_same_file_edited_twice(self):
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/auth.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c2", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/auth.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c2", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, ["src/auth.py"])

    def test_multiple_different_files(self):
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/a.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c2", "toolName": "create_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/b.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c2", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, ["src/a.py", "src/b.py"])

    # ── failure / exclusion cases ──────────────────────────────────────────

    def test_failed_edit_excluded(self):
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/auth.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": False}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, [])

    def test_read_file_excluded(self):
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "read_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/auth.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, [])

    def test_empty_transcript_returns_empty_list(self):
        _write_transcript(self.transcript, [])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, [])

    def test_missing_transcript_returns_empty_list(self):
        result = parse_transcript_edits("/nonexistent/path.json", self.tmpdir)
        self.assertEqual(result, [])

    def test_malformed_json_lines_skipped(self):
        with open(self.transcript, "w") as f:
            f.write("not valid json\n")
            f.write(json.dumps({"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/auth.py")}
            }}) + "\n")
            f.write(json.dumps({"type": "tool.execution_complete", "data": {
                "toolCallId": "c1", "success": True
            }}) + "\n")
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, ["src/auth.py"])

    def test_interleaved_read_and_edit(self):
        """read_file between edit calls must not affect results."""
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "r1", "toolName": "read_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/auth.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "r1", "success": True}},
            {"type": "tool.execution_start", "data": {
                "toolCallId": "e1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/auth.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "e1", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir)
        self.assertEqual(result, ["src/auth.py"])

    # ── last_turn_only ─────────────────────────────────────────────────────

    def test_last_turn_only_excludes_pre_turn_edits(self):
        """Edits before the last user.message must not appear."""
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/old.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
            {"type": "user.message", "data": {"content": "next turn"}},
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c2", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/new.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c2", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir, last_turn_only=True)
        self.assertEqual(result, ["src/new.py"])

    def test_last_turn_only_multiple_user_messages(self):
        """Only edits after the *last* user.message are returned."""
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/turn1.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
            {"type": "user.message", "data": {"content": "turn 2"}},
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c2", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/turn2.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c2", "success": True}},
            {"type": "user.message", "data": {"content": "turn 3"}},
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c3", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/turn3.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c3", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir, last_turn_only=True)
        self.assertEqual(result, ["src/turn3.py"])

    def test_last_turn_only_no_user_message_returns_all(self):
        """With no user.message events, last_turn_only behaves like False."""
        _write_transcript(self.transcript, [
            {"type": "tool.execution_start", "data": {
                "toolCallId": "c1", "toolName": "replace_string_in_file",
                "arguments": {"filePath": os.path.join(self.tmpdir, "src/a.py")}
            }},
            {"type": "tool.execution_complete", "data": {"toolCallId": "c1", "success": True}},
        ])
        result = parse_transcript_edits(self.transcript, self.tmpdir, last_turn_only=True)
        self.assertEqual(result, ["src/a.py"])


if __name__ == "__main__":
    unittest.main()
