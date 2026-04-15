# Route B: Transcript-Based Edit Detection

> 设计文档。由 brainstorming agent 整理，供 dev agent 一次性实施。

---

## 背景与目的

当前 Stop hook (`engaku check-update`) 通过 `.ai/.session-edits.tmp` 获取本轮修改的文件列表，该文件由 PostToolUse hook (`engaku log-edit`) 在每次 tool 调用后追加。

**根本问题：** VS Code 的 `toolNames` 过滤器不可靠，导致 `read_file` 等非编辑操作也触发 hook，产生大量假阳性（读过的文件被误记为"修改"）。

**解决方案（Route B）：** 废弃 PostToolUse 路径，改用 VS Code 为所有 hook 提供的 `transcript_path` 字段，在 Stop hook 中直接解析 JSONL transcript，提取实际成功的编辑操作。

**验证：** 已通过对比本项目一轮真实对话的 transcript 与实际 git 状态进行确认：Route B 输出与真实改动完全一致，无假阳性、无漏报。

---

## Scope

**新增：**
- `src/engaku/utils.py` — 新增 `parse_transcript_edits(transcript_path, cwd)` 函数
- `tests/test_utils.py` — 新增，包含 `TestParseTranscriptEdits` 测试类

**修改：**
- `src/engaku/cmd_check_update.py` — 更新 `_get_changed_files()` fallback 链，删除无用函数和 debug 代码
- `src/engaku/constants.py` — 删除 `SESSION_EDITS` 常量
- `src/engaku/cli.py` — 删除 `log-edit` 子命令
- `tests/test_check_update.py` — 删除 `TestGetSessionEdits`，更新 `TestGetChangedFilesFallback`，新增 `TestGetChangedFilesTranscript`

**删除：**
- `src/engaku/cmd_log_edit.py`
- `src/engaku/templates/hooks/edit-log.json`
- `.github/hooks/edit-log.json`
- `tests/test_log_edit.py`

**不变：**
- `cmd_check_update.py` 中的检查逻辑（Cases 1、2、3）
- `cmd_log_read.py`、`access-log.json`（access log 机制独立于 edit tracking）
- git fallback 逻辑（transcript 不存在时退化为 git diff）

---

## 一、`parse_transcript_edits()` 实现规格

### 位置

`src/engaku/utils.py`，追加在文件末尾（新增公共函数）。

### 编辑工具集（模块级常量，紧贴函数定义之前）

```python
_EDIT_TOOL_NAMES = frozenset({
    "create_file",
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "insert_edit_into_file",
    "apply_patch",
})
```

（前缀 `_` 表示模块私有，不对外导出）

### 函数签名

```python
def parse_transcript_edits(transcript_path, cwd):
    """Parse a VS Code transcript JSONL file and return a deduplicated list of
    successfully-edited file paths, expressed as paths relative to cwd.

    Only tool calls that both (a) used an edit tool and (b) completed with
    success=true are included. Failed edits and read-only tool calls are ignored.

    Returns [] on any I/O or parse error (never raises).
    """
```

### 算法

JSONL 文件，每行一个 JSON 对象。

```
pending = {}   # {toolCallId: [abs_paths...]}
result  = []   # insertion-order dedup list
seen    = set()

for each line in file (skip lines that fail json.loads):
    if event["type"] == "tool.execution_start":
        tool_name = event["data"]["toolName"]
        if tool_name not in _EDIT_TOOL_NAMES:
            continue
        paths = _extract_paths_from_args(tool_name, event["data"]["arguments"])
        if paths:
            pending[event["data"]["toolCallId"]] = paths

    elif event["type"] == "tool.execution_complete":
        call_id = event["data"]["toolCallId"]
        if call_id not in pending:
            continue
        if not event["data"].get("success", False):
            del pending[call_id]   # failed edit: discard
            continue
        for p in pending.pop(call_id):
            rel = relative_to_cwd(p, cwd)
            if rel not in seen:
                seen.add(rel)
                result.append(rel)

return result
```

**内部辅助函数（模块私有，定义在 `parse_transcript_edits` 前）：**

```python
def _extract_paths_from_args(tool_name, args):
    """Extract file path(s) from parsed tool arguments dict.
    Returns list of path strings (may be empty on unexpected shape).
    """
    if not isinstance(args, dict):
        return []
    paths = []
    if tool_name in ("create_file", "replace_string_in_file", "insert_edit_into_file"):
        p = args.get("filePath") or args.get("path")
        if isinstance(p, str):
            paths.append(p)
    elif tool_name == "multi_replace_string_in_file":
        for r in args.get("replacements") or []:
            if isinstance(r, dict):
                fp = r.get("filePath")
                if isinstance(fp, str):
                    paths.append(fp)
    elif tool_name == "apply_patch":
        # Extract from "*** Update File: <path>" lines in arguments["input"]
        import re
        text = args.get("input", "")
        if isinstance(text, str):
            for m in re.finditer(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$", text, re.MULTILINE):
                paths.append(m.group(1).strip())
    return paths
```

### 边界情况

| 情况 | 处理方式 |
|------|----------|
| transcript 文件不存在 / 不可读 | catch OSError → return `[]` |
| 某行 JSON 解析失败 | skip 该行，继续 |
| `arguments` 结构不符合预期 | return `[]` for that event，不 crash |
| `toolCallId` 出现 start 但没有 complete | 留在 pending，最终被抛弃（无影响） |
| 路径为绝对路径 | `relative_to_cwd()` 自动转相对路径 |
| 路径在 cwd 之外（如 VS Code 内部 tmp 文件） | `relative_to_cwd()` 返回 `../../...` 形式路径，后续 `is_code_file()` 会过滤掉 |
| 重复路径（同一文件被多次编辑） | 去重，保持首次出现位置 |

---

## 二、`cmd_check_update.py` 修改规格

### 移除内容

1. `import shutil`（仅用于 debug 代码）
2. `from engaku.constants import RECENT_SECONDS, SESSION_EDITS` → 删除 `SESSION_EDITS`（只保留 `RECENT_SECONDS`）
3. `_get_session_edits(cwd)` 函数 — 整个删除
4. Stop hook 中的 debug transcript dump 代码块：
   ```python
   tp = hook_input.get("transcript_path")
   if tp and os.path.isfile(tp):
       dest = os.path.join(cwd, ".ai", ".last-transcript.json")
       try:
           shutil.copy2(tp, dest)
       except OSError:
           pass
   ```

### 修改 `_get_changed_files(cwd)`

将旧的三级 fallback 改为新的三级 fallback（第 1 级变为 transcript，其余不变）：

```python
def _get_changed_files(cwd, hook_input=None):
    """Return list of changed file paths relative to cwd.

    Fallback chain (first non-empty non-None result wins):
    1. transcript_path from hook_input  — parse actual edit tool calls
    2. git diff --name-only HEAD        — uncommitted changes vs last commit
    3. git diff --cached + git ls-files --others  — staged/untracked (never-committed repos)
    """
    # 1. Transcript-based edit detection (accurate; no false positives)
    if hook_input:
        tp = hook_input.get("transcript_path")
        if tp and os.path.isfile(tp):
            from engaku.utils import parse_transcript_edits
            edits = parse_transcript_edits(tp, cwd)
            if edits is not None:   # empty list is valid (no edits this session)
                return edits

    # 2. Changes vs HEAD (standard case)
    head_diff = _git_run(["diff", "--name-only", "HEAD"], cwd)
    if head_diff is not None:
        return head_diff

    # 3. Never-committed repo ...（现有逻辑不变）
```

> **注意：** `hook_input=None` 参数让函数在测试中可以不传 hook_input 而退化到 git fallback，保持现有测试不变。

### 修改 `run()` 的调用点

在 `run()` 中，将：
```python
changed = _get_changed_files(cwd)
```
改为：
```python
changed = _get_changed_files(cwd, hook_input=hook_input)
```

### 不变

- `_git_run()` 及 git fallback 逻辑
- `_suggest_modules()`、`_load_module_paths()`、`_match_path()`、`_has_module_files()`、`_classify_files()`、`_claimed_modules_updated()`、`_is_ignored_path()`
- Cases 1、2、3 全部检查逻辑不变

---

## 三、`constants.py` 修改规格

删除以下一行：
```python
SESSION_EDITS = os.path.join(".ai", ".session-edits.tmp")
```

---

## 四、`cli.py` 修改规格

删除 `log-edit` 子命令定义：
```python
# engaku log-edit
subparsers.add_parser(
    "log-edit",
    help="Track code file edits in .ai/.session-edits.tmp for PostToolUse hook",
)
```

以及 dispatch 块：
```python
elif args.command == "log-edit":
    from engaku.cmd_log_edit import run
    sys.exit(run())
```

---

## 五、文件删除清单

以下文件直接删除（Python `os.remove` 或 shell `rm`）：

| 文件 | 原因 |
|------|------|
| `src/engaku/cmd_log_edit.py` | PostToolUse 路径废弃 |
| `src/engaku/templates/hooks/edit-log.json` | 配套 hook 模板 |
| `.github/hooks/edit-log.json` | 配套 hook live 文件 |
| `tests/test_log_edit.py` | 对应的测试文件 |
| `.ai/.last-transcript.json` | debug 用途，已完成分析 |

---

## 六、测试规格

### 删除

- `tests/test_log_edit.py`（整个文件）
- `test_check_update.py` 中的 `TestGetSessionEdits` 类（约 lines 204–237）

### 修改 `TestGetChangedFilesFallback`

删除 `_write_session_edits()` helper 和其对应测试用例：
- `test_session_edits_takes_priority_over_git` — 删除
- `test_falls_back_to_git_when_no_session_edits` — **重命名** 为 `test_falls_back_to_git_when_no_transcript`，将 hook_input 传 `{}` 给 `_get_changed_files`
- `test_falls_back_to_staged_untracked_when_no_head` — 保留，但调用改为 `mod._get_changed_files(self.tmpdir, hook_input={})`

新增一个用例：
```python
def test_transcript_takes_priority_over_git(self):
    # Create a minimal transcript with one successful edit
    import tempfile, json as _json
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        self._transcript_path = f.name
        f.write(_json.dumps({"type": "tool.execution_start", "data": {
            "toolCallId": "c1", "toolName": "replace_string_in_file",
            "arguments": {"filePath": os.path.join(self.tmpdir, "src/edited.py")}
        }}) + "\n")
        f.write(_json.dumps({"type": "tool.execution_complete", "data": {
            "toolCallId": "c1", "success": True
        }}) + "\n")

    orig_git_run = mod._git_run
    git_called = []
    mod._git_run = lambda args, cwd: (git_called.append(args), ["src/from_git.py"])[1]
    try:
        result = mod._get_changed_files(
            self.tmpdir, hook_input={"transcript_path": self._transcript_path}
        )
    finally:
        mod._git_run = orig_git_run
        import os as _os; _os.unlink(self._transcript_path)

    self.assertIn("src/edited.py", result)
    self.assertEqual(git_called, [], "git must not be called when transcript exists")
```

### 新建 `tests/test_utils.py`

```python
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


if __name__ == "__main__":
    unittest.main()
```

---

## 七、Hook 配置影响

`edit-log.json` 删除后，`PostToolUse` 只剩 `access-log.json`（用于 `log-read`），不需要其他改动。

Stop hook 仍在 `dev.agent.md` 中通过 `hooks.Stop` 配置调用 `engaku check-update`，无需修改。

---

## 八、现有测试兼容性

所有 `TestCheckUpdate` 中的测试通过 `_run(changed_files=[...])` mock 了 `_get_changed_files()`，不受本次变更影响，全部应继续通过。

`TestLoadConfig`、`TestSuggestModules`、`TestLoadModulePaths`、`TestMatchPath`、`TestClassifyFiles`、`TestClaimedModulesUpdated` 同理，无需修改。

---

## 九、实施顺序建议（供 dev agent 参考）

1. `utils.py`：添加 `_EDIT_TOOL_NAMES`、`_extract_paths_from_args()`、`parse_transcript_edits()`
2. `cmd_check_update.py`：修改 imports、删除 `_get_session_edits()`、修改 `_get_changed_files()`、修改 `run()` 调用点、删除 debug 代码
3. `constants.py`：删除 `SESSION_EDITS`
4. `cli.py`：删除 `log-edit` 子命令
5. 删除文件：`cmd_log_edit.py`、`templates/hooks/edit-log.json`、`.github/hooks/edit-log.json`、`.ai/.last-transcript.json`
6. `tests/test_utils.py`：新建，包含 `TestParseTranscriptEdits`
7. `tests/test_check_update.py`：删除 `TestGetSessionEdits`，更新 `TestGetChangedFilesFallback`
8. `tests/test_log_edit.py`：删除整个文件
9. 运行 `python -m pytest tests/ -v` 验证全部通过
