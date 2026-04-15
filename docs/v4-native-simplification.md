# Engaku V4 — Native Simplification

> 整理自 2026-04-10 多轮设计讨论。对 Hermes Agent、Claude Code、VS Code 原生特性进行横向分析后得出。

**Goal:** 去除 module knowledge 系统及其所有维护机制，改用 VS Code 原生 `.instructions.md`
实现等价的路径条件知识注入。同时合并 rules.md 到 copilot-instructions.md，减少自有数据面，
将 engaku 从"知识管理框架"收缩为"工作流守卫 + 上下文注入器"。

**Architecture:** 纯 Python stdlib CLI + VS Code Hooks。不引入新依赖。

---

## V3 回顾：module knowledge 为什么失败了

V3 的核心设计是用 `.ai/modules/*.md` 存储模块知识，通过 inject hook 生成 module index
table 告诉 agent "修改这些文件前先读对应 module"。这个设计需要三套维护机制：

| 机制 | 用途 | 代价 |
|------|------|------|
| knowledge-keeper agent | 在 dev 完工后被 subagent 调用，更新 module 内容 | 专用 agent + subagent-start hook + dev.agent.md 中的调用规则 |
| scanner / scanner-update agents | 发现未覆盖文件、创建/更新 module 文件 | 两个专用 agent + 复杂的分类逻辑 |
| check-update Stop hook | 强制检测 stale module | 271 行最大源文件，对非编码 agent 误触发 |
| prompt-check hook | 提醒 unclaimed files / stale modules | stale/unclaimed 提醒逻辑 |
| validate / stats 命令 | 校验 module 格式、统计覆盖率 | 两个专用命令 |

**而 VS Code 原生的 `.github/instructions/*.instructions.md` + `applyTo` glob 完全覆盖了
module index 的路由功能**——当 agent 打开匹配文件时，VS Code 自动注入对应 instructions，
无需 engaku 扫描、索引、提醒。

---

## 外部参考

### Claude Code 的启示

Claude Code 的 CLAUDE.md 体系：
- 多级层次：managed policy → project root → ancestor dirs → user home → subdirectory lazy-load
- `.claude/rules/*.md` 支持 `paths:` glob frontmatter，按路径条件加载
- 自动记忆：`~/.claude/projects/<repo>/memory/`，agent 自主写入
- MEMORY.md 启动限制 200 行 / 25KB

关键启示：**路径条件知识注入是成熟方案**，不需要自建。

### Hermes Agent 的启示

Hermes Agent 的 SQLite + FTS5 跨 session 记忆：
- sessions 表用 parent_session_id 构建压缩链
- messages 表 + FTS5 外部内容索引
- session_search tool 查询 FTS5 → 解析 parent chain → 并行 LLM 摘要

关键启示：跨 session 记忆是独立能力，不依赖 module knowledge 系统。（本文档不讨论是否引入。）

### VS Code 原生特性

| 特性 | 说明 |
|------|------|
| `.github/copilot-instructions.md` | 全局 always-on 指令 |
| `.github/instructions/*.instructions.md` | `applyTo` glob 路径条件注入 |
| `.agent.md` frontmatter hooks | 8 种事件：SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, SubagentStart, SubagentStop, Stop |
| Hook 输入 | 所有 hook 均收到 `sessionId`, `timestamp`, `cwd`, `transcript_path` |
| PostToolUse | 额外收到 `tool_name`, `tool_input`, `tool_response` |
| PreToolUse | 支持 `permissionDecision: "deny"` 阻止工具执行 |

---

## 设计决策

### D1: 删除 module knowledge 系统

删除的文件与功能：

| 删除内容 | 类型 | 理由 |
|----------|------|------|
| `.ai/modules/*.md` | 数据文件 | 被 `.instructions.md` 替代 |
| `cmd_validate.py` + `test_validate.py` | 命令 | 仅服务于 module 格式校验 |
| `cmd_stats.py` + `test_stats.py` | 命令 | 仅服务于 module 覆盖率统计 |
| `cmd_subagent_start.py` + `test_subagent_start.py` | 命令 | 仅服务于 knowledge-keeper 上下文注入 |
| knowledge-keeper.agent.md | agent | 职责完全消失 |
| scanner-update.agent.md | agent | 合并回 scanner |

### D2: scanner agent 转型

scanner 不再生成 `.ai/modules/` 文件。新职责：

1. 分析项目结构，推荐 `.instructions.md` 文件分组
2. 为每个分组生成 `.github/instructions/<name>.instructions.md`，含 `applyTo` glob
3. 需要用户审核后才写入
4. 一次性使用或低频使用（项目结构变化时）

scanner-update 合并回 scanner，因为 instructions 文件的增量更新比 module 简单得多。

### D3: 合并 rules.md 到 copilot-instructions.md

**原因：**
- V3 中 rules.md 是 `.ai/` 数据面，通过 inject hook 注入。但 rules 本质是行为指令，不是项目知识。
- copilot-instructions.md 就是 VS Code 原生的全局行为指令入口。
- 合并后少一个注入环节，agent 在无 hook 时也能看到规则。

**合并策略：**
- 全局规则（~15 行）→ `.github/copilot-instructions.md`
- 路径条件规则 → `.github/instructions/*.instructions.md`
- `.ai/rules.md` 删除

### D4: inject 精简

inject (SessionStart / PreCompact hook) 的注入内容变为：

```
<project-context>
{overview.md 内容}
</project-context>

<active-task>
{当前活跃 task 计划摘要，如有}
</active-task>
```

删除：module index table 生成逻辑。
新增：活跃 task 检测——扫描 `.ai/tasks/` 找到 `status: in-progress` 的文件，注入其标题和未完成 checklist。

### D5: check-update 精简

**保留：**
- agent 类型检测（跳过非编码 agent）——由 `.agent.md` hook 的 `agents:` frontmatter 限定

**删除：**
- `_load_module_paths()` — module paths 扫描
- `_classify_files()` — unclaimed file 分类
- `_claimed_modules_updated()` — stale module 检测
- 所有 stale / unclaimed 相关提醒逻辑

**保留/改造为：**
- 检测是否有新文件未被任何 `.instructions.md` 的 `applyTo` 覆盖（可选，低优先级）

### D6: prompt-check 精简

**保留：**
- 关键词检测 → systemMessage 提醒可能需要更新规则

**删除：**
- `_build_stale_reminder()` — stale module 提醒
- `_build_unclaimed_reminder()` — unclaimed file 提醒

### D7: 新增 PostToolUse guard（可选）

用 PostToolUse hook 检测 agent 是否写入了禁止路径（如直接编辑 `.instructions.md` 或
`copilot-instructions.md`）。如果检测到，返回 systemMessage 警告。

这替代了 V3 中 knowledge-keeper 独占 module 写权限的机制。

### D8: overview.md 保留

overview.md 是高变频项目描述，继续由 inject 注入。与 copilot-instructions.md 的
行为指令性质不同，不合并。维护方式：dev agent 在需要时直接更新。

### D9: Skills 随 engaku init 捆绑安装

engaku v4 将 `.github/skills/` 纳入 init 生成的模板结构。Skills 定义可复用的工作方法论，
与 agent 定义角色互补——agent 约束边界，skill 提供具体工作流程。任何 agent 在判断相关时
自动加载对应 skill，无需额外配置。

初始 skill 列表（跟随 `engaku init` 安装）：

| Skill | 触发场景 | `disable-model-invocation` |
|-------|----------|:---:|
| `systematic-debugging` | bug、测试失败、runtime 错误、CI 失败 | false（自动检测） |
| `verification-before-completion` | 声明工作完成、测试通过、PR 就绪前 | false（自动检测） |
| `frontend-design` | 前端页面、组件、dashboard、UI 设计 | true（手动调用） |

这三个 skill 是通用方法论，不针对特定项目，在任何使用 engaku 初始化的项目中都有价值。

**与 planner 的关系：** planner agent 已内置分析和规划能力，`writing-plans` skill 不额外捆绑。

**skill 内容来源：** 直接从用户级 `~/.copilot/skills/` 打包进 templates，团队成员
`engaku init` 后无需配置个人 skills 目录即可使用，适用于团队共享和 CI 场景。

---

## 终态结构

### 文件布局

```
.github/
  copilot-instructions.md          # 全局行为指令（含原 rules.md 内容）
  agents/
    dev.agent.md                   # dev agent + hooks 配置
    planner.agent.md               # 分析和规划
    reviewer.agent.md              # 任务验收
    scanner.agent.md               # 生成 .instructions.md 文件
  instructions/
    hooks.instructions.md          # applyTo: "src/engaku/cmd_*.py"
    templates.instructions.md      # applyTo: "src/engaku/templates/**"
    tests.instructions.md          # applyTo: "tests/**"
    ...                            # 项目自定义
  skills/
    systematic-debugging/
      SKILL.md
    verification-before-completion/
      SKILL.md
    frontend-design/
      SKILL.md
  hooks/
    *.json                         # hook 配置
.ai/
  overview.md                      # 项目架构描述
  engaku.json                      # engaku 元数据
  tasks/                           # 任务计划
  decisions/                       # 架构决策记录
```

### Agent 变化

| Agent | V3 | V4 | 说明 |
|-------|----|----|------|
| dev | ✓ | ✓ | 不变 |
| planner | ✓ | ✓ | 不变 |
| reviewer | ✓ | ✓ | 不变 |
| scanner | ✓ | ✓ | 转型：生成 .instructions.md |
| scanner-update | ✓ | ✗ | 合并回 scanner |
| knowledge-keeper | ✓ | ✗ | 职责消失 |

### 命令变化

| 命令 | V3 | V4 | 说明 |
|------|----|----|------|
| init | ✓ | ✓ | 模板更新：去除 module 相关文件 |
| inject | ✓ | ✓ | 精简：overview + active task only |
| check-update | ✓ | ✓ | 精简：去除 module stale 检测 |
| prompt-check | ✓ | ✓ | 精简：去除 stale/unclaimed |
| task-review | ✓ | ✓ | 不变 |
| apply | ✓ | ✓ | 不变 |
| log-read | ✓ | ✓ | 不变 |
| validate | ✓ | ✗ | 删除 |
| stats | ✓ | ✗ | 删除 |
| subagent-start | ✓ | ✗ | 删除 |

### 代码影响估算

| 变更 | 估算行数 |
|------|----------|
| 删除 cmd_validate.py + test | ~200 行 |
| 删除 cmd_stats.py + test | ~200 行 |
| 删除 cmd_subagent_start.py + test | ~150 行 |
| 精简 cmd_check_update.py | ~150 行删除 |
| 精简 cmd_prompt_check.py | ~50 行删除 |
| 精简 cmd_inject.py | ~30 行删除，~20 行新增（active task） |
| 更新 templates/ | 文件数减少 |
| **净删除** | **~750-800 行** |

---

## 不包含在本设计中

- **跨 session 记忆（SQLite / FTS5）**：技术上可行（stdlib sqlite3 内置 FTS5），
  但价值需要单独论证。是否引入作为独立决策。
- **PreToolUse deny 机制**：比 PostToolUse warn 更强，但侵入性更高，暂不设计。
