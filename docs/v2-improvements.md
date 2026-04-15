# Engaku V2 Improvements — Implementation Plan

> 整理自 2026-04-08 设计讨论。涵盖六项改进，按优先级分组。

**Goal:** 解决 MVP 实测暴露的核心缺陷：git 依赖导致变更检测静默失败、知识冷启动 friction 过高、知识文件格式规范不足、长 session 知识丢失、以及可观测性缺失。

**Architecture 原则不变：** 纯 Python stdlib CLI + VS Code Hooks + Subagents。不引入新依赖，不改变总体生命周期。

---

## 总览：六项改进

| # | 改进 | 优先级 | 主要变更 |
|---|------|--------|---------|
| 1 | Session 内编辑追踪（解除 git 依赖） | P0 | 新增 hook + cmd_log_edit.py |
| 2 | check-update 附带文件列表 | P0 | 改 cmd_check_update.py |
| 3 | 知识冷启动 `/seed` 触发 | P1 | 新增 seed.prompt.md 模板 |
| 4 | 模块路径 frontmatter（`paths:`） | P1 | 改 validate + check-update |
| 5 | 字符限制放宽 + frontmatter 不计入 | P1 | 改 cmd_validate.py |
| 6 | PreCompact 注入 + 知识历史视图 | P2 | 新增 cmd_precompact.py + 改 stats |

---

## 改进 1：Session 内编辑追踪（解除 git 依赖）

### 问题

`cmd_check_update.py` 当前用 `git diff --name-only HEAD` 检测代码变更。若 repo 从未 commit（HEAD 不存在），返回 returncode != 0，函数返回 `[]`，check-update **静默放行**——知识更新提醒完全失效。

### 方案

**PostToolUse hook** 捕获文件写入操作，追加到 `.ai/.session-edits.tmp`。Stop hook 时 `check-update` 优先读此文件，只有文件不存在时才 fallback 到 `git diff`。SessionStart 时清除临时文件。

整个链条不需要 git 有任何 commit 历史。

**关于 PostToolUse 性能：** 只过滤文件写入工具（`editFiles`、`create_file`、`replace_string_in_file`、`insert_edit_into_file`），一个 session 内触发次数通常 10-20 次，Python 启动开销约 50-100ms/次，总计 0.5-2 秒散布在整个 session，可以接受。

### File Map

- **Create:** `src/engaku/cmd_log_edit.py`
- **Modify:** `src/engaku/cmd_inject.py` — SessionStart 时清除 `.session-edits.tmp`
- **Modify:** `src/engaku/cmd_check_update.py` — 优先读 `.session-edits.tmp`
- **Modify:** `src/engaku/templates/access-log.json` → 重命名为更通用的 hook，或新增 `edit-log.json`
- **Test:** `tests/test_log_edit.py`

### Tasks

#### Task 1.1: 实现 `cmd_log_edit.py`

**Files:** Create `src/engaku/cmd_log_edit.py`

- [ ] 从 stdin 读取 PostToolUse hook JSON（格式同 cmd_log_read.py）
- [ ] 从 `tool_input` 提取文件路径（`filePath`、`path`、`files` 数组，需处理多文件情况）
- [ ] 过滤掉 `.ai/` 目录内的文件（知识文件自身的编辑不触发）
- [ ] 过滤掉非代码文件（复用 `_is_code_file` 逻辑，从 check-update 抽出为 shared helper）
- [ ] 追加到 `.ai/.session-edits.tmp`，格式：每行一个相对路径
- [ ] 文件写入失败时静默，永远 exit 0

```python
# .session-edits.tmp 格式示例
src/engaku/cmd_check_update.py
src/engaku/cmd_validate.py
```

- [ ] Verify: 用 mock PostToolUse JSON 测试各路径提取情况

#### Task 1.2: 新增 `edit-log.json` hook 模板

**Files:** Create `src/engaku/templates/edit-log.json`

- [ ] 创建 hook 配置，监听写入类工具，调用 `engaku log-edit`：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "engaku log-edit",
        "timeout": 5,
        "toolNames": [
          "editFiles",
          "create_file",
          "replace_string_in_file",
          "insert_edit_into_file"
        ]
      }
    ]
  }
}
```

- [ ] 更新 `cmd_init.py` 将此文件复制到目标 repo 的 `.github/hooks/edit-log.json`
- [ ] 更新 `tests/test_init.py` 断言此文件被创建

#### Task 1.3: `cmd_inject.py` SessionStart 时清除临时文件

**Files:** Modify `src/engaku/cmd_inject.py`

- [ ] 在 `run()` 的末尾，检查并删除 `.ai/.session-edits.tmp`（若存在）
- [ ] 删除失败时静默

#### Task 1.4: `cmd_check_update.py` 优先读 `.session-edits.tmp`

**Files:** Modify `src/engaku/cmd_check_update.py`

- [ ] 新增 `_get_session_edits(cwd)` 函数：读取 `.ai/.session-edits.tmp`，返回路径列表（文件不存在则返回 `None`，区别于空列表）
- [ ] `run()` 中：若 `_get_session_edits` 返回非 `None`，用其结果代替 `_get_changed_files`
- [ ] fallback 链：session edits → `git diff HEAD` → `git diff --cached` + `git ls-files --others --exclude-standard`

```python
def _get_changed_files(cwd):
    # 1. session edits (no git needed)
    session = _get_session_edits(cwd)
    if session is not None:
        return session
    # 2. committed changes
    result = _git_diff(["--name-only", "HEAD"], cwd)
    if result is not None:
        return result
    # 3. staged + untracked (never-committed repo)
    staged = _git_diff(["--cached", "--name-only"], cwd) or []
    untracked = _git_ls_files_untracked(cwd) or []
    return staged + untracked
```

- [ ] 写测试：有 `.session-edits.tmp` 时不调用 git，无文件时调用 git

#### Task 1.5: 注册 CLI 子命令

**Files:** Modify `src/engaku/cli.py`

- [ ] 注册 `log-edit` 子命令，路由到 `cmd_log_edit.run`
- [ ] 写 `tests/test_log_edit.py`（参考 test_log_read.py 结构）
- [ ] Verify: `python -m pytest tests/test_log_edit.py tests/test_check_update.py -v`

---

## 改进 2：check-update Block Reason 附带文件列表

### 问题

当前 block 消息是固定文字，agent 不知道该更新哪些模块的知识文件，知识更新质量低。

### 方案

把本次 session/git 检测到的变更文件列表注入到 block reason，让 agent 有足够上下文去调 knowledge-keeper。

### File Map

- **Modify:** `src/engaku/cmd_check_update.py`

### Tasks

#### Task 2.1: 修改 block 输出

**Files:** Modify `src/engaku/cmd_check_update.py`

- [ ] 将 `sys.stderr.write` 内容改为包含文件列表的结构化消息：

```
Code changes detected but no knowledge files were updated.
Please call the knowledge-keeper subagent to update .ai/modules/ before ending the session.

Changed files in this session:
  src/engaku/cmd_check_update.py
  src/engaku/cmd_validate.py

Suggested modules to update: cmd_check_update, cmd_validate
```

- [ ] 新增 `_suggest_modules(code_files)` 函数：将文件路径映射到可能的模块名（取文件名去扩展名，或取最近的目录名），作为建议而非强制
- [ ] Verify: `echo '{"stop_hook_active":false}' | engaku check-update` 手动放一个 `.session-edits.tmp` 验证输出格式

---

## 改进 3：知识冷启动 `/seed` 触发

### 问题

`engaku init` 生成的 `.ai/rules.md` 和 `.ai/overview.md` 只有注释占位符，用户面对空模板不知道该写什么。

### 设计原则

**两类知识有不同来源：**

| 类型 | 示例 | 能否从代码推断 |
|------|------|--------------|
| 结构性知识 | 目录结构、模块列表、技术栈 | ✅ `/seed` 可以 |
| 决策性约束 | "不用 Python 3.9+语法"、"零依赖" | ❌ 只能用户手填或从对话提炼 |

`/seed` 不触碰 `rules.md`（规则只能从人类输入来），只生成 `overview.md` 和 `modules/*.md` 的初始内容。`rules.md` 通过 knowledge-keeper 在对话中逐步积累。

### 方案

提供 `seed.prompt.md` 模板，用户在 VS Code chat 中输入 `/seed` 触发。Prompt 指示 agent 使用 `@workspace` 扫描 repo 并生成知识文件。CLI 不做任何 AI 工作。

### File Map

- **Create:** `src/engaku/templates/seed.prompt.md`
- **Modify:** `src/engaku/cmd_init.py` — 将 seed.prompt.md 复制到 `.github/prompts/seed.prompt.md`
- **Modify:** `src/engaku/templates/rules.md` — 加上明确的手填说明，告知用户此文件不会被 `/seed` 填充

### Tasks

#### Task 3.1: 创建 `seed.prompt.md`

**Files:** Create `src/engaku/templates/seed.prompt.md`

```markdown
---
mode: agent
description: Scan this repo and generate initial knowledge files in .ai/
---

Analyze this repository and generate initial knowledge files.

## Steps

1. Read `pyproject.toml` / `package.json` / `go.mod` / `Cargo.toml` (whichever exists) to determine the tech stack and project name.
2. Scan the top-level directory structure. Identify the key source directories.
3. For each significant source module or package, read the main entry files to understand what it does.
4. Generate or overwrite the following files:

### `.ai/overview.md`

Fill in the project name, tech stack, directory structure, and core modules. Follow the existing template structure. Do not touch any user-written content that is not a placeholder comment.

### `.ai/modules/{name}.md` for each discovered module

Create one file per significant module. Each file must:
- Include `## Overview` heading
- Be ≤300 characters in the body (not counting frontmatter)
- Be specific: name key classes, functions, or non-obvious patterns
- Omit vague filler

## Do NOT touch

- `.ai/rules.md` — constraints and preferences must come from the human
- Any existing `.ai/modules/` file that already has real content (not just template comments)
```

- [ ] Verify: 在一个真实 repo 里用 `/seed` 触发，检查输出是否合理

#### Task 3.2: 更新 `cmd_init.py` 复制 seed prompt

**Files:** Modify `src/engaku/cmd_init.py`

- [ ] 在初始化逻辑中，将 `seed.prompt.md` 复制到 `.github/prompts/seed.prompt.md`（需创建 `prompts/` 目录）
- [ ] 在 init 完成后的输出中加上提示：`Tip: Run /seed in Copilot chat to generate initial knowledge files.`
- [ ] 更新 `tests/test_init.py`

#### Task 3.3: 更新 `rules.md` 模板

**Files:** Modify `src/engaku/templates/rules.md`

- [ ] 在顶部加上注释说明此文件不由 `/seed` 填充，需要开发过程中手动积累或由 knowledge-keeper 从对话中提炼

---

## 改进 4：模块路径 Frontmatter（`paths:` 字段）

### 问题

`check-update` 的模块级对应是模糊的（文件名启发），改了 `cmd_auth.py` 随便更新 `cmd_payment.md` 也能通过检查。

### 方案

模块知识文件支持可选的 YAML frontmatter，声明对应的源码路径。有 `paths:` 时做精确匹配，没有时 fallback 到文件名启发。

```markdown
---
paths:
  - src/engaku/cmd_check_update.py
  - src/engaku/cmd_validate.py
---

## Overview
这两个模块负责...
```

**frontmatter 不计入字符限制**，只统计 `---` 之后的 Markdown 正文。

### File Map

- **Modify:** `src/engaku/cmd_validate.py` — 解析 frontmatter，字符计数排除 frontmatter
- **Modify:** `src/engaku/cmd_check_update.py` — 用 paths 做精确模块匹配
- **Create:** `src/engaku/templates/modules/example.md` — 带 frontmatter 的示例模块文件
- **Test:** 更新 `tests/test_validate.py`

### Tasks

#### Task 4.1: `cmd_validate.py` 解析 frontmatter

**Files:** Modify `src/engaku/cmd_validate.py`

- [ ] 新增 `_parse_frontmatter(content)` 函数：检测文件开头是否有 `---\n...\n---`，若有则分离 frontmatter 和正文，返回 `(frontmatter_str, body_str)`；若无则返回 `(None, content)`
- [ ] 字符计数、标题检查、禁用词检查全部作用于 `body` 而非原始 content
- [ ] frontmatter 本身做基本格式校验：若存在但不是合法 YAML 结构，报 warning（不 fail）
- [ ] Verify: 写测试覆盖「有 frontmatter」「无 frontmatter」「frontmatter 格式错误」三种情况

#### Task 4.2: `cmd_check_update.py` 精确模块映射

**Files:** Modify `src/engaku/cmd_check_update.py`

- [ ] 新增 `_load_module_paths(cwd)` 函数：扫描 `.ai/modules/*.md`，解析 frontmatter 中的 `paths:` 字段，返回 `{module_stem: [paths...]}`
- [ ] 在 `_knowledge_updated_after` 中，若有 `paths:` 映射，只检查"变更文件对应的模块知识文件"是否更新，而不是"任意模块文件"
- [ ] fallback：无 `paths:` 的模块文件继续用文件名启发匹配（当前逻辑保留）
- [ ] Verify: 写测试覆盖精确匹配场景

---

## 改进 5：字符限制放宽 + frontmatter 不计入

### 问题

300 字符（约 50 个英文单词）对于有多个关键类型/函数的模块经常不够用。当前对中英文混排项目尤其紧张。

### 方案

- 将正文上限从 300 提升到 **600 字符**
- Frontmatter 不计入（已在改进 4 中实现）
- 下限保持 50 字符（防空文件）

600 字符仍足以控制 "每个知识文件必须精炼" 的原则，同时能写清楚 2-3 个关键函数/类型和非显而易见的约束。

### File Map

- **Modify:** `src/engaku/cmd_validate.py` — `MAX_CHARS = 600`
- **Modify:** `src/engaku/templates/knowledge-keeper.agent.md` — 同步更新说明
- **Modify:** `.github/agents/knowledge-keeper.agent.md`（本 repo 自身的 knowledge-keeper）
- **Test:** 更新 `tests/test_validate.py`

### Tasks

#### Task 5.1: 更新字符限制

**Files:** Modify `src/engaku/cmd_validate.py`

- [ ] `MAX_CHARS = 600`
- [ ] 同步更新 `REQUIRED_HEADING` 检查文档字符串（如有）
- [ ] Verify: `python -m pytest tests/test_validate.py -v`

#### Task 5.2: 同步更新 agent 指令

**Files:** Modify `src/engaku/templates/knowledge-keeper.agent.md`, `.github/agents/knowledge-keeper.agent.md`

- [ ] 将 "≤300 characters" 改为 "≤600 characters"

---

## 改进 6：PreCompact Hook + 知识历史视图

### 问题 A（长 session 知识丢失）

长 session 中 context window 被压缩后，`.ai/` 内容可能从对话上下文中消失。agent 后续操作可能与已确立的 rules 矛盾。

### 方案 A

PreCompact hook 触发时重新注入 `rules.md` + `overview.md`，与 SessionStart 的注入逻辑相同，确保 compact 后上下文里始终有项目知识。

### File Map

- **Create:** `src/engaku/templates/precompact.json`
- **Modify:** `src/engaku/cmd_init.py` — 复制 precompact.json
- **Modify:** `src/engaku/cmd_inject.py` — 支持 `--event` 参数区分 SessionStart 和 PreCompact 的输出格式

### Tasks

#### Task 6.1: 支持 PreCompact 输出格式

**Files:** Modify `src/engaku/cmd_inject.py`

PreCompact hook 使用通用输出格式（`systemMessage`），不是 SessionStart 专用的 `hookSpecificOutput`。

- [ ] 在 `run()` 中从 stdin 读取 hook 事件名（`hookEventName` 字段）
- [ ] 若 `hookEventName == "SessionStart"`（或无输入）：输出现有格式
- [ ] 若 `hookEventName == "PreCompact"`：输出 `{"systemMessage": "<rules + overview content>"}`
- [ ] Verify: 用 mock PreCompact JSON 测试输出格式

#### Task 6.2: 创建 `precompact.json` 模板

**Files:** Create `src/engaku/templates/precompact.json`

```json
{
  "hooks": {
    "PreCompact": [
      {
        "type": "command",
        "command": "engaku inject",
        "timeout": 5
      }
    ]
  }
}
```

- [ ] 更新 `cmd_init.py` 复制此文件到 `.github/hooks/precompact.json`
- [ ] 更新 `tests/test_init.py`

---

### 问题 B（知识历史可观测性）

`engaku stats` 只报告覆盖率和新鲜度，看不到知识文件的变化历史。无法判断某个模块的知识是否被错误覆盖。

### 方案 B

`engaku stats --history` 对每个 `.ai/modules/*.md` 输出最近 N 次 git commit 的摘要（commit hash 前 7 位 + 时间 + commit message 首行）。

**前提：** 依赖 git log，只在有 commit 历史时有效。无 commit 时友好输出提示。

### Tasks

#### Task 6.3: `cmd_stats.py` 增加 `--history` 选项

**Files:** Modify `src/engaku/cmd_stats.py`, `src/engaku/cli.py`

- [ ] `cli.py` 给 `stats` 子命令加 `--history` flag
- [ ] `cmd_stats.py` 新增 `_section_history(cwd, out, n=5)` 函数：
  - 枚举 `.ai/modules/*.md`
  - 对每个文件运行 `git log -5 --format="%h %ci %s" -- <path>`
  - 格式化输出，无 git 历史时输出 "(no commits yet)"
- [ ] `run(history=False)` 接受参数，为 True 时在输出末尾追加 history section
- [ ] Verify: 在本 repo（engaku）中运行 `engaku stats --history` 验证输出

---

## Scope Boundaries

**In scope（本计划）：**
- 6 项改进的全部实现
- 对应的 unittest 更新
- 模板文件同步更新

**Out of scope：**
- `engaku remove` 子命令
- 并发写入保护（OS-level append 已足够 MVP）
- 多 workspace 知识一致性
- PyPI 发布（保持 git install）
- DSL 工作流引擎（见 dsl-workflow-future.md）

---

## 执行顺序建议

改进 1 和 2 是 P0，应先做：改进 1 打通 session-edits 追踪链路后，改进 2 的"附带文件列表"才能有实际内容可以展示。

改进 4 和 5 应一起做：frontmatter 解析逻辑在 4 中实现，5 只是调整常量，两者同一个 validate 文件里完成。

改进 3、6 可以并行，各自独立。

```
P0: 改进1 → 改进2
P1: 改进4+5（一起）→ 改进3（独立）
P2: 改进6A → 改进6B
```
