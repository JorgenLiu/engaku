# Hook 架构整合 + prompt-check 增强计划

> 状态：已完成  
> 背景：当前存在两个问题：
> 1. 全局 hook 文件对所有 agent 生效，导致 subagent 被不应有的 hook 污染，且与 dev.agent.md frontmatter 中的重复注册形成双重触发
> 2. `prompt-check` 只提醒 stale 模块，不提醒 unclaimed 文件（需要走 scanner）

---

## 问题诊断

### 问题 A：全局 hook 污染 subagent

`.github/hooks/` 下的 JSON 文件是 workspace 级 hook，对所有 agent（包括 knowledge-keeper、planner、scanner 等子 agent）生效。

当前五个全局 hook 文件的归属分析：

| 文件 | 事件 | 实际意图 | 是否应全局 |
|------|------|----------|-----------|
| `session.json` | SessionStart → `engaku inject` | dev session 开始时注入项目上下文 | ❌ dev-only |
| `access-log.json` | PostToolUse(read_file) → `engaku log-read` | 记录 dev 读取的文件 | ❌ dev-only |
| `precompact.json` | PreCompact → `engaku inject` | dev 长会话 compact 前重注入上下文 | ❌ dev-only |
| `prompt-check.json` | UserPromptSubmit → `engaku prompt-check` | 检测 dev 收到的 prompt 中的规则/stale | ❌ dev-only，且与 dev.agent.md 重复 |
| `subagent-start.json` | SubagentStart → `engaku subagent-start` | dev 启动 knowledge-keeper 时注入上下文 | ❌ dev-only，且与 dev.agent.md 重复 |

所有五个 hook 均应仅对 dev 生效，移入 dev.agent.md frontmatter。

### 问题 B：重复触发

`prompt-check.json`（全局）和 `dev.agent.md` frontmatter 中的 `UserPromptSubmit` 同时注册，dev agent 每次收到 prompt 时两个 hook 都触发，导致相同的 stale 提醒出现两次。

`subagent-start.json` 同理。

### 问题 C：prompt-check 缺少 unclaimed 文件提醒

`engaku prompt-check` 目前只检测 stale（已被模块覆盖但知识过期）的文件，不检测 unclaimed（未被任何模块覆盖）的文件。用户在 dev 新建了源文件但没走 scanner 时，不会收到任何提醒。

---

## 任务计划

### Task 1：将所有全局 hook 迁移进 dev.agent.md

**影响文件**
- `src/engaku/templates/agents/dev.agent.md`（template）
- `.github/agents/dev.agent.md`（live，必须同步）
- `src/engaku/templates/hooks/*.json`（五个 template hook 文件）
- `.github/hooks/*.json`（五个 live hook 文件）
- `src/engaku/cmd_init.py`（安装循环）
- `tests/test_init.py`（EXPECTED_FILES）

**步骤 1.1：更新 dev.agent.md frontmatter（template + live 各一份）**

将以下三个新 hook 事件加入 `hooks:` 块（现有三个保留不变）：

```yaml
hooks:
  Stop:
    - type: command
      command: engaku check-update
      timeout: 10
  UserPromptSubmit:
    - type: command
      command: engaku prompt-check
      timeout: 5
  SubagentStart:
    - type: command
      command: engaku subagent-start
      timeout: 5
  SessionStart:
    - type: command
      command: engaku inject
      timeout: 5
  PreCompact:
    - type: command
      command: engaku inject
      timeout: 5
  PostToolUse:
    - type: command
      command: engaku log-read
      timeout: 5
      toolNames:
        - read_file
```

注意：`toolNames` 语法需与 VS Code agent frontmatter 规范对齐；如果 YAML 格式不被接受，退回到保留 `access-log.json` 作为全局 hook（因为 `PostToolUse` + `toolNames` 过滤目前只有全局 hook JSON 格式有明确文档）。这一点在执行时需要验证。

**步骤 1.2：清空所有全局 hook 文件（template + live）**

将五个文件内容都改为 `{}` — 保留文件占位，不再注册任何 hook：
- `src/engaku/templates/hooks/session.json` → `{}`
- `src/engaku/templates/hooks/access-log.json` → `{}`
- `src/engaku/templates/hooks/precompact.json` → `{}`
- `src/engaku/templates/hooks/prompt-check.json` → `{}`
- `src/engaku/templates/hooks/subagent-start.json` → `{}`
- 对应五个 `.github/hooks/` live 文件同步清空

**步骤 1.3：从 `cmd_init.py` 安装循环中移除 hook 文件**

`cmd_init.py` 中，`hooks_dir` 的安装循环目前拷贝五个文件。由于 hook 已全部移入 dev.agent.md，这些文件不再需要安装。

将循环改为空（或直接删除循环），只保留 hooks 目录本身的创建（即 `os.makedirs(hooks_dir, exist_ok=True)`）。

同步更新模块 docstring 中的 `.github/hooks/` 文件列表。

**步骤 1.4：更新 `tests/test_init.py` EXPECTED_FILES**

从列表中移除五个 hook 文件路径：
```python
os.path.join(".github", "hooks", "session.json"),
os.path.join(".github", "hooks", "access-log.json"),
os.path.join(".github", "hooks", "precompact.json"),
os.path.join(".github", "hooks", "prompt-check.json"),
os.path.join(".github", "hooks", "subagent-start.json"),
```

**验证**：`python -m unittest tests.test_init` 通过。

---

### Task 2：prompt-check 增加 unclaimed 文件提醒

**影响文件**
- `src/engaku/cmd_prompt_check.py`
- `tests/test_prompt_check.py`

**步骤 2.1：在 `cmd_prompt_check.py` 中新增 `_build_unclaimed_reminder()`**

在 `_build_stale_reminder()` 函数之后，添加：

```python
def _build_unclaimed_reminder(cwd, hook_input):
    """Return a reminder string if any code files edited this session have no
    module coverage.

    Returns None when all edited files are covered or no edits were found.
    """
    tp = hook_input.get("transcript_path")
    if not tp or not os.path.isfile(tp):
        return None

    all_edits = parse_transcript_edits(tp, cwd, last_turn_only=False)
    code_files = [f for f in all_edits if is_code_file(f)]
    if not code_files:
        return None

    _, unclaimed = _classify_files(cwd, code_files)
    if not unclaimed:
        return None

    return (
        "Uncovered files detected: [{}]. "
        "Call @scanner-update to assign them to a module, "
        "then @knowledge-keeper to update module knowledge."
    ).format(", ".join(unclaimed))
```

**步骤 2.2：在 `run()` 中调用 `_build_unclaimed_reminder()`**

在 `_build_stale_reminder` 调用之后追加：

```python
unclaimed_reminder = _build_unclaimed_reminder(cwd, hook_input)
if unclaimed_reminder:
    messages.append(unclaimed_reminder)
```

**步骤 2.3：在 `tests/test_prompt_check.py` 新增测试类**

在 `TestPromptCheckStaleReminder` 类之后新增 `TestPromptCheckUnclaimedReminder`，覆盖：

1. `test_no_transcript_no_unclaimed_reminder` — 无 transcript → 无输出
2. `test_all_claimed_no_reminder` — 所有编辑文件都被模块覆盖 → 无 scanner 提醒
3. `test_unclaimed_file_reminder_injected` — 有 unclaimed 文件 → systemMessage 含 `scanner-update` 和文件名
4. `test_unclaimed_and_stale_both_in_message` — 同时有 unclaimed + stale → 单条 systemMessage 包含两个提醒

测试辅助方法（`_write_module`, `_write_src`, `_write_transcript`, `_run_with_hook_input`）可以从 `TestPromptCheckStaleReminder` 中复制，结构相同。

**验证**：`python -m unittest tests.test_prompt_check` 通过。

---

## 执行顺序

1. Task 1（hook 迁移）先执行，Task 2（unclaimed 提醒）后执行
2. Task 1.1 需要 **先验证** `PostToolUse` + `toolNames` 是否支持在 agent frontmatter YAML 中使用。如果不支持，保留 `access-log.json` 作为全局 hook（file 内容不清空），仅清空其余四个文件
3. 每个 Task 完成后分别运行全套测试：`python -m unittest discover -s tests`
4. 完成后调用 knowledge-keeper 更新 `session-hooks`、`scaffolding`、`templates` 三个模块

## 完成标准

- [x] `dev.agent.md`（template + live）frontmatter 包含全部 6 个 hook 事件（PostToolUse 视验证结果）
- [x] 五个全局 hook JSON 文件均为 `{}`（或四个，视 PostToolUse 情况）
- [x] `cmd_init.py` 不再安装 hook 文件
- [x] `engaku prompt-check` 在有 unclaimed 文件时输出 scanner 提醒
- [x] 全套测试通过：`Ran N tests — OK`
- [x] `engaku validate` 全部 `[OK]`
