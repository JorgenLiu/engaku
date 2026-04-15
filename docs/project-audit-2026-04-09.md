# Engaku 项目审计报告 — 2026-04-09

> 基于 planner agent 初步评估 + 独立交叉验证。全部发现均经过代码级确认。

---

## 总览

Engaku 的核心架构已经成型，8 个子命令均可运行，四个 module knowledge 文件覆盖了全部源文件，
agent/hook 模板与 live 版本保持同步（除 model: 字段外）。`pyproject.toml` 配置完整，
零第三方依赖，Python >=3.8 合规。

以下为分级发现清单，按修复优先级排序。

---

## P0 — 功能缺失（当前行为错误）

### 1. `prompt-check` hook 模板不存在

**症状：** `cmd_prompt_check.py` 已实现并在 CLI 注册，但 `src/engaku/templates/hooks/` 中没有
对应的 hook JSON 文件。`engaku init` 不会安装 UserPromptSubmit hook，导致所有新初始化的 repo
中该功能**从未运行**。

**证据：**
- `src/engaku/templates/hooks/` 仅有 3 个文件：`session.json`、`access-log.json`、`precompact.json`
- `cmd_init.py` L149-L151 只遍历这 3 个文件
- `cmd_init.py` 模块 docstring 提到 `prompt-reminder.json`，但该文件从未存在——docstring 是脏数据
- `.github/hooks/` live 目录同样无此 hook

**修复：**
- 创建 `src/engaku/templates/hooks/prompt-check.json`（UserPromptSubmit hook，调用 `engaku prompt-check`）
- 更新 `cmd_init.py`：(a) 修正 docstring，(b) 在 hook 复制循环中加入 `prompt-check.json`
- 在 `.github/hooks/` 中安装 live 版本

**工作量：** 小

---

### 2. `cmd_stats` 的覆盖率分析对实际项目无效

**症状：** `_discover_source_modules()` 扫描 `src/` 下的**顶层目录名**（本项目返回 `["engaku"]`），
而 `.ai/modules/` 的文件名是逻辑分组名（`quality`、`scaffolding` 等）。运行 `engaku stats`
会显示 `0/1 modules have knowledge files (0%)`，同时把全部 4 个知识文件列为 "with no matching
source module"——**信息价值为零**。

**根因：** 设计假设"module name = package directory name"，但 V3 架构改为以逻辑单元分组后
（D5 决策），两者不再对应。

**修复方向：** 改用 module knowledge 文件本身作为唯一数据源。覆盖率可基于"所有被跟踪的源文件中，
有多少被某个 module 的 `paths:` 声明覆盖"来计算。不再依赖目录名匹配。

**工作量：** 中

---

## P1 — 约定违规

### 3. 4 个 `cmd_*.py` 缺少 `main()` 入口

项目规则要求"每个 `cmd_*.py` 都有 `run()` + `main()` 入口"。

| 文件 | `run()` | `main()` |
|------|---------|----------|
| `cmd_validate.py` | ✓ | ✗ |
| `cmd_check_update.py` | ✓ | ✗ |
| `cmd_inject.py` | ✓ | ✗ |
| `cmd_prompt_check.py` | ✓ | ✗ |

其余 4 个模块（`cmd_log_read`、`cmd_init`、`cmd_apply`、`cmd_stats`）均合规。

**工作量：** 很小（每个文件加 2-3 行）

### 4. `cmd_stats.py` 无对应测试文件

所有 cmd 模块均有 `tests/test_*.py` 对应，唯独缺 `test_stats.py`。
`cmd_stats` 是复杂度较高的模块（git 集成、access log 解析、三个报告段 + 可选 history 段）。

**工作量：** 中

### 5. `knowledge-keeper.agent.md` 模板硬编码了 `model:` 字段

`src/engaku/templates/agents/knowledge-keeper.agent.md` 中写死了
`model: ['GPT-5 mini (copilot)']`。按约定，模板应不含 `model:` 字段，由 `engaku apply` 管理。
其他 4 个 agent 模板均遵循此约定。

**工作量：** 很小

---

## P2 — 代码质量 & 一致性

### 6. `check-update` Case 2 vs Case 3 的输出格式不一致

| 场景 | 输出位置 | 退出码 | 结构化 JSON |
|------|----------|--------|-------------|
| Case 2: claimed module 过时 | stderr only | 2 | 无 |
| Case 3: unclaimed + block | stdout JSON + stderr | 0 | `hookSpecificOutput.decision` |

两种"阻断"场景使用完全不同的机制。Case 2 依赖 exit code 2 让 VS Code 阻断；
Case 3 通过 hookSpecificOutput 传递结构化信息。对于调试和一致性来说，Case 2 应当
也输出结构化 JSON 到 stdout，至少包含 stale module 列表。

**工作量：** 小

### 7. `_claimed_modules_updated` 的 mtime 判断逻辑在 `run()` 中被完整重复

`_claimed_modules_updated()` 返回 `bool`，但 `run()` 为了拼 `stale_stems` 错误消息，
又手动走了一遍完整的 mtime 比较循环。这段逻辑可以合并——让函数返回 stale stem 列表而非 bool。

**工作量：** 小

### 8. `MAX_CHARS` 值在四处存在不一致

| 位置 | 值 |
|------|-----|
| `.ai/engaku.json` (live) | 1600 |
| `.ai/rules.md` (live) | 1600 |
| `src/engaku/constants.py` (框架默认) | 1500 |
| `src/engaku/templates/ai/engaku.json` (模板默认) | 1500 |

设计意图是"engaku.json 为 canonical source，constants.py 只是 fallback default"，所以
1500 vs 1600 属于预期内的 default vs override。但规则文本说"Canonical value set in
`.ai/engaku.json`; run `engaku apply` to sync into `rules.md`"——如果新用户用 `engaku init`
安装模板，拿到的默认值是 1500 而非 1600，这个行为是否符合预期需要确认。

**操作项：** 非 bug，但需明确：模板默认值（1500）和本项目运行值（1600）的差异是否 intentional。

---

## P3 — 文档 & 可观测性

### 9. `README.md` 完全为空（仅 `# engaku`）

作为一个 `pip install git+https://...` 分发的 CLI 工具，README 是用户唯一的入口文档。
当前缺少：项目描述、安装指南、8 个子命令说明、使用示例、架构概览。

**工作量：** 中

### 10. `.ai/overview.md` 仍为空模板

本项目自身的 overview.md 只有占位注释，未填写实际内容。作为 dogfooding 项目，
inject 注入的上下文中 overview 段为空，影响 agent 工作质量。

**工作量：** 小

### 11. `dsl-workflow-future.md` 已明确标注为已归档

文件开头写明"此文档内容已合并至 design.md"。可以删除或移到 archive 目录以减少噪音。

**工作量：** 很小

### 12. `pyproject.toml` 缺少 `license` 字段

metadata 中无 license 声明。若计划开源或发布至 PyPI，需补充。

**工作量：** 很小

---

## 优先级执行建议

| 序号 | 问题 | 优先级 | 工作量 | 依赖关系 |
|------|------|--------|--------|----------|
| 1 | 创建 `prompt-check.json` 模板 + 修 docstring | P0 | 小 | 无 |
| 2 | 修复 `_discover_source_modules` 逻辑 | P0 | 中 | 无 |
| 3 | 给 4 个 cmd 补 `main()` | P1 | 很小 | 无 |
| 4 | 创建 `test_stats.py` | P1 | 中 | 建议在 #2 之后 |
| 5 | 去掉 knowledge-keeper 模板中硬编码的 `model:` | P1 | 很小 | 无 |
| 6 | 统一 check-update Case 2 输出格式 | P2 | 小 | 无 |
| 7 | 合并 stale-stem 重复逻辑 | P2 | 小 | 可与 #6 合并 |
| 8 | 确认 MAX_CHARS 模板默认值意图 | P2 | 决策 | 无 |
| 9 | 编写 README.md | P3 | 中 | 建议在功能修复后 |
| 10 | 填写 .ai/overview.md | P3 | 小 | 无 |
| 11 | 归档 dsl-workflow-future.md | P3 | 很小 | 无 |
| 12 | 补 pyproject.toml license | P3 | 很小 | 无 |

#1-5 可并行执行（无依赖）。#6 和 #7 建议合并为一个 task。#9 建议在功能修复完成后再写，
避免文档与代码状态不一致。
