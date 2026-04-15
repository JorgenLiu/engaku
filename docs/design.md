# Engaku - AI 持久记忆层

> 最后更新：2026-04-07

## 项目定位

一个嵌入开发工作流的 AI 外部记忆层。Copilot 通过直接文件读写 + VS Code 原生能力，实现跨会话的记忆持久化。

**不是知识库平台。不是文档管理系统。不是企业知识中台。**

## 解决的问题

1. **AI 跨会话失忆**：Copilot 每次新对话都不记得项目结构和历史决策
2. **项目约束不持久**：开发者说过"不要用 inline style"，下次对话 Copilot 忘了
3. **工作流无连续性**：brainstorming 产出的实施计划，后续执行时没有追踪

## 不解决的问题

- 不做全量代码向量化（Copilot @workspace 已有此能力）
- 不做外部系统集成（Jira/Confluence 是后续，不是 MVP）
- 不做团队协作功能（先个人验证，再考虑推广）

---

## 架构决策：CLI 而非 MCP Server

**结论：用 CLI 工具替代 MCP Server。**

原 MCP 方案要解决三个问题，逐一分析：

| 原 MCP 的作用 | 替代方案 | 等效性 |
|---|---|---|
| Resources 确定性注入 rules + overview | SessionStart Hook + `engaku inject` | ✅ 完全等效，且更可靠 |
| AI 调用 tool 写文件 + 服务器端内联校验 | AI 直接用 `edit` 写文件，Stop Hook 事后校验 | ✅ 基本等效（校验时机从写前变写后，用户感知无差异） |
| `search_knowledge` 检索 | AI 用 `@workspace` / `read` 直接访问 `.ai/` | ✅ 完全等效（知识体量 <100 文件，无需中间层） |

MCP Server 引入的额外成本不值得：依赖 Python SDK 和持续运行的进程，每个项目都需要配置 `.vscode/settings.json`，且在两周验证期内就产生摩擦。

**MCP 唯一不可替代的场景**：若 Stop Hook 事后校验导致"修了又坏"循环，MCP 的写入前拦截才有决定性价值。这留作验证失败后的 fallback，不是当前 MVP 的理由。

---

## 平台能力（调研截止 2026-04-07）

### GitHub Agentic Memory（官方）

GitHub 已推出官方 Agentic Memory（公开预览）：
- **当前不支持** VS Code 本地 Agent 模式，仅限 Cloud Agent / Code Review / Copilot CLI
- 28 天过期，黑盒，无法控制记什么

Engaku 填补的是官方 Memory 无法覆盖的部分：

| 能力 | 官方 Agentic Memory | Engaku |
|------|-------------------|--------|
| VS Code 本地 Agent | ❌ | ✅ |
| 显式项目规则/约束 | ❌ | ✅ |
| 长期架构决策（不过期） | ❌（28天） | ✅ |
| 可审查、可 git 版本控制 | ❌（黑盒） | ✅ |
| 工作流任务追踪 | ❌ | ✅ |

### VS Code Agent Hooks（Preview）

支持 8 个生命周期事件，执行确定性 shell 命令。Engaku 用到的事件：

| 事件 | 触发时机 | 用途 |
|------|---------|------|
| `SessionStart` | 新对话开始时 | `engaku inject` 注入 rules + overview |
| `PostToolUse` | tool 调用完成后 | 检测 `.ai/` 文件被直接编辑时注入格式提醒 |
| `PreCompact` | 上下文压缩前 | 导出关键 context，防止知识在压缩中丢失 |
| `Stop` | agent 会话结束时 | `engaku check-update` 检测知识更新遗漏，阻断会话 |
| `SubagentStop` | subagent 完成时 | 验证 knowledge-keeper 是否完成更新 |

关键细节（文档 2026-04-01 更新）：
- `SessionStart` hook 通过 `hookSpecificOutput.additionalContext` 直接注入内容到对话上下文
- `Stop` hook 收到 `stop_hook_active: true` 时表示已在因 hook 继续运行，需检查此字段防止无限循环
- **Agent-scoped hooks**（Preview）：hook 可直接定义在 agent frontmatter 的 `hooks:` 字段，仅在该 agent 激活时生效，`knowledge-keeper` 的质量校验 hook 用此方式内聚管理

### VS Code Subagents（Experimental）

- 主 agent 通过 `agent` tool 调用 custom agent 作为 subagent，有**独立 context window**
- `user-invocable: false`：对用户隐藏，仅供 agent 调用（已替代废弃的 `infer` 属性）
- `disable-model-invocation: true`：阻止被作为 subagent 调用
- `model` 属性：subagent 使用更便宜的模型（`Claude Haiku 4.5 (copilot)` / `Gemini 3 Flash (Preview) (copilot)`）
- `agents: ['name']`：显式限定允许调用的 subagent 列表，防止错选

### VS Code Handoffs

- agent frontmatter 的 `handoffs` 属性，在 agent 完成后展示引导按钮
- `send: false`：预填 prompt 等待用户确认，不自动提交
- `handoffs.model`：可指定 handoff 执行时使用的模型

---

## 文件存储结构

知识文件存在目标 repo 的 `.ai/` 目录下，跟随 git 版本控制：

```
<target-repo>/
├── .ai/
│   ├── rules.md              ← 项目规则（约束、偏好、禁忌）
│   ├── overview.md           ← 项目全局架构概览
│   ├── modules/              ← 模块知识（温层）
│   │   ├── auth.md
│   │   └── payment.md
│   ├── decisions/            ← 决策记录（冷层）
│   │   └── 001-jwt-choice.md
│   └── tasks/                ← 工作流计划
│       └── 2026-04-04-token-refresh.md
└── .github/
    ├── agents/
    │   ├── dev.agent.md              ← 主开发 agent
    │   ├── knowledge-keeper.agent.md ← 知识更新 subagent（用户不可见）
    │   └── planner.agent.md          ← brainstorming → 实施计划
    ├── hooks/
    │   ├── session.json              ← SessionStart Hook（注入上下文）
    │   └── knowledge-check.json      ← Stop Hook（阻断知识遗漏）
    └── copilot-instructions.md       ← 引导 Copilot 使用知识库的基础指令
```

---

## CLI 工具：engaku

CLI 只做 AI 做不了或不该做的事，其余让 AI 用自身的 `edit`/`read` 工具直接处理：

```
engaku init          ← 在目标 repo 初始化 .ai/ 结构 + .github/hooks/ + .github/agents/
engaku inject        ← 输出 rules.md + overview.md 的 JSON（供 SessionStart Hook 调用）
engaku check-update  ← 检查本次会话是否有代码变更但知识未更新（Stop Hook 调用）
engaku validate      ← 校验 .ai/modules/*.md 内容质量，支持 --recent 只检查最近修改的文件
```

### engaku check-update 逻辑

1. 读取 git diff（当前会话内的文件变更）
2. 若有 `.ai/` 外的代码文件变更，检查 `.ai/modules/` 是否有时间戳更新
3. 未更新则退出码 2（blocking error），stderr 输出：`你修改了代码但未更新知识文件，请调用 knowledge-keeper subagent 更新 .ai/modules/ 后再结束会话`
4. 检查 `stop_hook_active` 字段，为 `true` 时直接退出 0，防止无限循环

### engaku validate 校验规则

- 正文 ≥ 50 字
- 必须有 `## 概览` 标题
- 禁用词检测：`更新了业务逻辑`、`修改了代码`、`进行了优化`
- 单个文件 ≤ 300 字

---

## 读写机制

### 确定性读取（SessionStart Hook）

```json
// .github/hooks/session.json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "engaku inject",
        "timeout": 5
      }
    ]
  }
}
```

`engaku inject` 读取 `.ai/rules.md` + `.ai/overview.md`，输出：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<rules.md 内容>\n\n---\n\n<overview.md 内容>"
  }
}
```

AI 在第一条消息之前就已知道项目规则和模块概览。

### 写入机制

AI 通过内置的 `edit` / `create_file` 工具**直接写** `.ai/modules/*.md`，不经过中间层。格式要求定义在 `knowledge-keeper.agent.md` 的 instructions 中。

### 写入可靠性（三层叠加）

| 层 | 机制 | 类型 | 可靠性 |
|---|------|------|--------|
| 1 | `dev.agent.md` 指令 + knowledge-keeper subagent | 概率性↑ | ~90% |
| 2 | Agent-scoped Stop hook in knowledge-keeper | 概率性↑ | ~95% |
| 3 | 全局 Stop Hook（`engaku check-update`） | **确定性** | ~100% |

### 写入质量控制

- 模块知识文件 ≤ 300 字，覆盖式更新（不追加）
- `engaku validate` 拒绝空话内容
- 知识文件在 repo 内走 git，PR review 时可审查

---

## 知识分层

- **热层**（自动注入）：`rules.md` + `overview.md`，总计 ≤ 1000 字
- **温层**（按需检索）：`modules/*.md`，每个 ≤ 300 字，AI 用 `read` 或 `@workspace` 访问
- **冷层**（低频访问）：`decisions/*.md`，超过 6 个月且无引用的归档

---

## Agent 定义

### dev agent

```yaml
# .github/agents/dev.agent.md
---
name: dev
description: 标准开发任务执行器，自动维护项目知识
tools: ['agent', 'edit', 'read', 'search', 'execute', 'create_file', 'replace_string_in_file']
agents: ['knowledge-keeper']
---

执行开发任务。完成后调用 knowledge-keeper subagent 更新项目知识。
执行期间遵循已注入的 rules.md 中的所有约束。
```

### knowledge-keeper subagent

```yaml
# .github/agents/knowledge-keeper.agent.md
---
name: knowledge-keeper
description: 项目知识维护者，分析代码变更并更新知识文件
user-invocable: false
model: ['Claude Haiku 4.5 (copilot)', 'Gemini 3 Flash (Preview) (copilot)']
tools: ['read', 'search', 'edit', 'create_file', 'replace_string_in_file']
hooks:
  Stop:
    - type: command
      command: engaku validate --recent
      timeout: 10
---

分析传入的任务描述和代码变更：
1. 编辑 .ai/modules/{module}.md 更新受影响模块（必须具体，禁止空话，≤300字，覆盖式）
2. 如有重要技术选择，在 .ai/decisions/ 创建新决策记录（格式：{id}-{title}.md）
3. 如用户表达了约束/偏好，追加到 .ai/rules.md 对应分类下
4. 如有进行中的计划，更新 .ai/tasks/ 内对应文件的 task checkbox
```

> `hooks.Stop` 在 knowledge-keeper 完成时运行 `engaku validate --recent`，若最近修改的 `.ai/` 文件不达标则阻断，要求重写。此 hook 仅在 knowledge-keeper 激活时生效（agent-scoped hook）。

### planner agent（含 Handoff）

```yaml
# .github/agents/planner.agent.md
---
name: planner
description: brainstorming + 实施计划生成
tools: ['read', 'search', 'edit', 'create_file']
agents: []
handoffs:
  - label: 开始实施
    agent: dev
    prompt: 计划已确认，请按计划执行第一个 task。
    send: false
---

引导用户完成 brainstorming，产出具体实施计划：
1. 理解目标，逐一提问澄清约束
2. 提出 2-3 个方案及权衡，说明推荐理由
3. 确认方案后，在 .ai/tasks/{date}-{slug}.md 创建实施计划文件
4. 展示 Handoff 按钮「开始实施」
```

流程示意：

```
@planner brainstorming 完成
  → 创建 .ai/tasks/{date}-{slug}.md
  → 展示 Handoff 按钮「开始实施」
  → 用户点击 → 切换到 @dev，携带计划上下文

@dev 执行循环
  → 读取 .ai/tasks/ 获取当前计划
  → 执行 task → 调用 knowledge-keeper subagent 更新知识
  → Stop Hook 验证知识已更新
  → 继续下一个 task，直到全部完成
```

### 实施文档格式

```markdown
---
plan_id: {date}-{slug}
title: {功能名称}
status: in-progress | completed
created: {date}
---

## 背景
{为什么要做这件事}

## 设计要点
{关键技术选择和原因}

## Tasks

- [ ] 1. {具体文件路径} - {具体修改内容} - {验证方式}
- [ ] 2. ...
```

---

## Stop Hook：确定性知识检查

```json
// .github/hooks/knowledge-check.json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "engaku check-update",
        "timeout": 10
      }
    ]
  }
}
```

`engaku check-update` 检测本次会话是否有代码变更但 `.ai/modules/` 未更新。若检测到遗漏则退出码 2，注入阻断消息给 AI。内置 `stop_hook_active` 检查防止无限循环。

---

## 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| CLI | Python + stdlib（`argparse`/`pathlib`） | 无额外依赖 |
| 存储 | 纯文件系统（Markdown） | 零依赖，git 版本控制 |
| 检索 | AI 直接用 `@workspace` / `read` 工具 | 知识量小（<100 文件），无需中间层 |
| 部署 | `pipx install engaku` | 一次安装，全局可用，不污染项目环境 |

预估代码量：~150 行 Python（4 个 CLI 命令 + 2 个度量命令）

**移除**：MCP Server 代码、`mcp` SDK 依赖、`.vscode/settings.json` MCP 配置

---

## 发布与部署

### 发布策略

| 阶段 | 方式 | 理由 |
|---|---|---|
| MVP 验证中 | `pip install git+https://github.com/me/engaku` | 无需 PyPI，pip 直接从 GitHub 安装 |
| 验证通过后 | 发布到 PyPI，`pip install --user engaku` | 对更广范围的分享更友好 |

### 兼容性约束

- Python `>=3.8`：Windows 工作笔记本只有 3.8.4，必须兼容
- 仅使用 stdlib：不引入第三方依赖
- 不用 3.9+ 语法：`str.removeprefix()`、`dict | dict`、`match/case`、`X | Y` 类型注解均禁止

### 部署方式

每个使用 engaku 的目标 repo，只需：

1. `pip install git+https://github.com/me/engaku`（一次性，全局 `--user`）
2. `engaku init`（在 repo 目录内运行，生成 `.ai/` + `.github/hooks/` + `.github/agents/`）

无需任何 `.vscode/settings.json` 配置。

---

## 验证计划

验证分两层：**过程指标**（CLI 可自动采集，回答"engaku 有没有在工作"）和**效果指标**（回答"engaku 有没有在帮助 Copilot"）。两层都需要通过，缺一不可。

---

### 层 1：过程指标（自动采集）

由 `engaku stats` 命令读取 git log + hook 日志后输出。

| 指标 | 计算方式 | 目标 |
|---|---|---|
| **知识覆盖率** | 有对应 `.ai/modules/*.md` 的模块数 / 总模块数 | ≥ 60% |
| **知识时效性** | 有代码变更但知识超过 7 天未更新的模块数 | ≤ 20% |
| **Stop Hook 阻断率** | 被 `check-update` 阻断的会话数 / 总会话数 | 记录即可（基线数据） |
| **validate 一次通过率** | knowledge-keeper 首次写入通过 `validate` 的比例 | ≥ 80% |

**Stop Hook 阻断率不设目标值**，只做记录。它回答的问题是"没有 Hook 时会漏掉多少次知识更新"——无论是 10% 还是 50%，都是有价值的基线数据。

#### 数据采集方式

`engaku stats` 需要以下数据来源：
- git log：推算本次会话的文件变更时间窗口
- `.ai/access.log`：知识文件被读取记录（由 PostToolUse Hook 写入，见下）
- Stop Hook 的退出码日志：VS Code 输出到 `GitHub Copilot Chat Hooks` output channel

---

### 层 2：效果指标（自动采集 + 人工记录）

#### 2a. 知识访问日志（自动）

通过 PostToolUse Hook 追踪 Copilot 主动读取 `.ai/` 文件的行为：

```json
// .github/hooks/access-log.json
{
  "hooks": {
    "PostToolUse": [
      {
        "type": "command",
        "command": "engaku log-read \"$TOOL_INPUT_FILE_PATH\""
      }
    ]
  }
}
```

`engaku log-read` 判断读取路径是否在 `.ai/` 下，若是则追加记录到 `.ai/access.log`：

```
2026-04-07T10:32:00Z  modules/auth.md  session:abc123
2026-04-07T10:32:01Z  rules.md         session:abc123
```

由此可回答：
- 每次会话 Copilot 平均主动访问多少个知识文件？（说明注入是否真的被用到）
- SessionStart 之后的访问是否比之前多？（说明自动注入有没有减少"主动检索"的需要）

目标：每会话平均 ≥ 1 次 `.ai/modules/` 主动访问（排除 SessionStart 的自动注入）。

#### 2b. 开发者会话日志（人工，每次会话 ~30 秒）

在 `.ai/session-log.md` 每次开发结束后追加一条记录，格式极简：

```markdown
## 2026-04-07

- 任务：实现用户登录失败重试限制
- Copilot 是否用上了已有知识？是 / **否（说明：没读 auth.md，重新描述了 AuthService 结构）**
- 是否需要重新解释背景？否 / **是（需要几句话 / 详细解释）**
- Copilot 是否提出了违反 rules.md 的建议？否 / **是（说明：建议用 inline style）**
```

这不是严格测量，是快速判断信号。填写时间 ≤ 30 秒，坚持记录比精确更重要。

两周后统计：
- "用上了已有知识"占比 → 目标 ≥ 60%
- "需要重新解释背景"占比 → 目标 ≤ 30%
- "提出违反 rules.md 建议"次数 → 目标 ≤ 2 次/周

---

### 部署步骤

1. 在一个真实项目中运行 `engaku init`
2. 手写 3-5 个核心模块的种子知识文件（`.ai/modules/`）
3. 在 `.github/hooks/` 加入 `session.json`（SessionStart）、`knowledge-check.json`（Stop）、`access-log.json`（PostToolUse）
4. 正常开发两周，每次会话后填写 session-log.md
5. 两周后运行 `engaku stats` + 统计 session-log.md

---

### 判定标准

| 场景 | 结论 |
|---|---|
| 层 1 + 层 2 均达标 | ✅ 继续投入，推进 `engaku scan`、质量规则扩展 |
| 层 1 达标，层 2 不达标（Copilot 不用知识）| 问题在注入方式或知识质量，调整 SessionStart hook 的 additionalContext 格式，或知识文件结构 |
| 层 1 不达标（validate 通过率低）| 加强 `validate` 规则，或重写 knowledge-keeper instructions |
| Stop Hook 阻断率极高（>60%）| knowledge-keeper subagent 触发逻辑有问题，调整 dev.agent.md |
| 整体不达标 | 考虑加回 MCP Server（写入前拦截），或终止项目 |

---

## 后续扩展（不在 MVP 范围内）

### DSL 工作流引擎

> 前提：CLI 方案稳定运行 4 周以上，有真实数据证明条件分支逻辑是瓶颈。

原生 Hooks + Subagents 解决了"可靠性"问题，但无法表达复杂的条件分支工作流：

- "如果是 bugfix，只更新模块知识；如果是新功能，还需要更新架构概览"
- "如果变更超过 5 个文件，先走 review subagent，再触发知识更新"
- "如果在 feature branch，知识标记 `unverified`；如果在 main，需要人工确认"

这类逻辑写在 Instructions 文本里脆弱，写在 Hook 脚本里可维护性差。DSL 引擎的价值：把工作流条件逻辑集中到一个可读、可版本控制、可调试的 YAML 配置文件。预计 +400 行代码。

### 其他扩展

- `engaku scan`：扫描存量代码生成初始知识文件
- Jira/Confluence 集成：通过 REST API 网关（post-MVP）
- 知识过期检测：`engaku verify` 对比源文件变更时间戳
- 团队推广：统一部署、权限控制

---

## 与已有方案的关系

| 方案 | 关系 |
|------|------|
| copilot-instructions.md | 互补——instructions 引导 Copilot 使用知识库 |
| CLAUDE.md | 类似理念，但本方案增加了动态写入和工作流追踪 |
| Cursor Rules | 类似理念的约束层，但本方案让 AI 自己维护约束 |
| Continue.dev @codebase | 本方案不做代码向量化，专注 Why 层 |
