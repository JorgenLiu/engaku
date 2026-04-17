# Engaku 项目迭代史与决策全录

related_task: none
created: 2026-04-17

---

## 项目缘起

Engaku 的出发点是一个简单的观察：**GitHub Copilot 每次新对话都不记得上一次聊了什么。**

2026 年 4 月初，项目创建者面对三个现实痛点：

1. **AI 跨会话失忆** — Copilot 不记得项目结构和历史决策
2. **项目约束不持久** — 开发者说过"不要用 inline style"，下次对话 Copilot 就忘了
3. **工作流无连续性** — brainstorming 产出的实施计划，后续执行时无法追踪

2026-04-07 日的初始设计文档（`docs/design.md`）明确划出了边界：**不做全量代码向量化，不做外部系统集成，不做团队协作功能。先个人验证，再考虑推广。**

GitHub 官方的 Agentic Memory 当时仅限 Cloud Agent / Code Review / Copilot CLI，不支持 VS Code 本地 Agent 模式，且 28 天过期、黑盒不可控。Engaku 要做的是一个**可 git 版本控制、可审查、不过期的本地持久记忆层**。

---

## 第零阶段：MCP 还是 CLI？

项目创立之初最关键的架构决策是**放弃 MCP Server，选择纯 CLI 工具**。

逆向分析了 MCP 的三个核心作用：

| MCP 原职责 | CLI 替代方案 | 等效性 |
|---|---|---|
| Resources 确定性注入 rules + overview | SessionStart Hook + `engaku inject` | ✅ 完全等效且更可靠 |
| AI 调用 tool 写文件 + 校验 | AI 直接用 `edit` 写文件，Stop Hook 事后校验 | ✅ 基本等效 |
| `search_knowledge` 检索 | AI 用 `@workspace` / `read` 直接访问 `.ai/` | ✅ 完全等效（知识体量 <100 文件） |

MCP Server 的额外成本不值得：依赖 Python SDK 和持续运行的进程，每个项目都需要配置 `.vscode/settings.json`。

**保留的 fallback**：若 Stop Hook 事后校验导致"修了又坏"循环，MCP 的写入前拦截才有决定性价值。但这个 fallback 在整个项目生命周期中从未被需要过。

---

## 第一阶段：MVP 实现（V1, ~2026-04-07）

### 架构

纯 Python stdlib CLI，6 个子命令：`init`、`inject`、`check-update`、`validate`、`log-read`、`stats`。通过 VS Code Agent Hooks 在会话生命周期的关键点被调用。

核心约束从第一天起就确立：
- Python ≥3.8，不使用 3.9+ 语法
- 零第三方依赖
- 发布方式：`pip install git+https://github.com/...`

### 文件存储

知识文件存储在 `.ai/` 目录下，跟随 git 版本控制：
- `.ai/rules.md` — 项目规则（约束、偏好、禁忌）
- `.ai/overview.md` — 项目全局架构概览
- `.ai/modules/*.md` — 模块知识
- `.ai/decisions/*.md` — 决策记录
- `.ai/tasks/*.md` — 工作流计划

### Agent 体系

- `dev.agent.md` — 主开发 agent
- `knowledge-keeper.agent.md` — 知识更新 subagent（用户不可见）
- `planner.agent.md` — brainstorming 和实施计划

### 写入可靠性三层叠加

| 层 | 机制 | 类型 | 可靠性 |
|---|------|------|--------|
| 1 | dev.agent.md 指令 + knowledge-keeper subagent | 概率性 | ~90% |
| 2 | Agent-scoped Stop hook in knowledge-keeper | 概率性 | ~95% |
| 3 | 全局 Stop Hook（`engaku check-update`） | 确定性 | ~100% |

### 教训

MVP 实测暴露了多个核心缺陷——git 依赖导致变更检测静默失败、知识冷启动 friction 过高、长 session 知识丢失——这些直接驱动了 V2 的设计。

---

## 第二阶段：实测修补（V2, ~2026-04-08）

V2 是对 MVP 实测痛点的针对性修补，6 项改进：

### P0 修复

1. **Session 内编辑追踪（解除 git 依赖）** — `check-update` 当时依赖 `git diff --name-only HEAD`，若 repo 从未 commit（HEAD 不存在），变更检测**静默失败**。解决方案：PostToolUse hook 捕获文件写入操作，追加到 `.ai/.session-edits.tmp`，Stop hook 优先读此文件而非 git diff。

2. **check-update 附带变更文件列表** — 原先 block 消息是固定文字，agent 不知道该更新哪些模块。改为输出具体文件列表 + 建议模块映射。

### P1 改进

3. **知识冷启动 `/seed` 触发** — 空模板问题的第一次尝试。提供 `seed.prompt.md` 让用户通过 `/seed` 触发 agent 扫描 repo 并生成知识文件。

4. **模块 `paths:` frontmatter** — 引入路径声明，让模块知识和源文件之间建立显式映射。

5. **字符限制放宽** — frontmatter 不计入字符限制。

6. **PreCompact 注入** — 防止长 session 中知识在上下文压缩时丢失。

### 教训

V2 的修补是正确方向，但暴露了更深层的架构问题：**module knowledge 的写入和消费两端都不健康**。写入端依赖多个 agent 的复杂编排，消费端——dev agent 在编码时**从未真正读取过** module 文件。

---

## 第三阶段：架构重构（V3, ~2026-04-08）

V3 是第一次大重构。经过多轮设计讨论（brainstorming agent + GPT / Gemini / Claude 交叉审核），识别出 6 个结构性问题：

### 六个核心发现

| # | 问题 | 根因 |
|---|------|------|
| 1 | Module files 从未被 dev 在编码时读取 | 消费侧缺失 — 没有机制告诉 agent 什么时候读哪个 module |
| 2 | copilot-instructions.md 混入了项目描述和格式模板 | 控制面与数据面未分离 |
| 3 | knowledge-keeper 承担过多职责 | 一个 mini model 同时做 modules/rules/decisions/tasks |
| 4 | 一源文件一 module 粒度过细 | 6 个碎片化微文件无人消费 |
| 5 | 规则在多处重复声明 | 违反单一事实源原则 |
| 6 | check-update Stop hook 对所有 agent 生效 | brainstorming/planner 等非编码 agent 也被阻断 |

### 关键决策

**D1: 控制面与数据面严格分离** — `.github/` 下的文件是控制面（行为指令），`.ai/` 下的文件是数据面（项目知识）。

**D4: inject 承担路由器角色** — 动态生成 module index table，告诉 agent"修改这些文件前先读对应 module"。

**D5: module 粒度改为逻辑单元** — 不再一源文件一 module，改为逻辑分组。引入 scanner agent 负责分组。

**D6: 职责重新分配** — 创建 module 文件归 scanner，更新内容归 knowledge-keeper，rules/decisions 归 dev agent（因为需要完整对话上下文）。

**D9: check-update 改为 agent-scoped hook** — 从全局 hook 迁移到 `dev.agent.md` frontmatter，避免非编码 agent 被阻断。

### check-update 行为重设计

V3 过程中的一个重要子设计（`docs/check-update-redesign.md`）重新定义了阻断逻辑：

> `paths:` 是用户的显式声明——"我决定跟踪这些文件"。未声明 = 没有承诺，不应阻断。

三种输出：硬阻断（claimed 但未更新）、软提醒（unclaimed files）、放行。
同时引入 scanner-update agent 处理增量文件分配。

### 教训

V3 修复了 hook scoping 和职责混乱，但核心问题——**module knowledge 的维护成本远超其价值**——并没有真正解决。module index 路由器虽然看起来优雅，但现实是：VS Code 原生的 `.instructions.md` + `applyTo` glob **完全覆盖了**这个路由功能，而且零维护成本。这个认识直接导致了 V4。

---

## 配套改进：Hook 整合与提醒增强（~2026-04-09）

在 V3 框架下，还进行了两项重要的子设计：

### Hook 架构整合（`docs/hook-consolidation-plan.md`）

发现所有 5 个全局 hook 文件都应仅对 dev 生效：

| 文件 | 事件 | 结论 |
|------|------|------|
| `session.json` | SessionStart | ❌ dev-only |
| `access-log.json` | PostToolUse | ❌ dev-only |
| `precompact.json` | PreCompact | ❌ dev-only |
| `prompt-check.json` | UserPromptSubmit | ❌ dev-only，且与 dev.agent.md 重复 |
| `subagent-start.json` | SubagentStart | ❌ dev-only，且与 dev.agent.md 重复 |

全部迁移入 dev.agent.md frontmatter，全局 hook JSON 清空。

### Stale Module Reminder（`docs/stale-module-reminder-plan.md`）

用 UserPromptSubmit hook 层叠提醒机制替代 Stop hook 的阻断式强制：
- `prompt-check` 在每次用户输入时检查是否有 stale module
- `check-update` Case 2 从 exit 2（blocking）改为 exit 0 + systemMessage（non-blocking）
- 新增 SubagentStart hook 为 knowledge-keeper 注入上下文

### Transcript-Based Edit Detection（`docs/transcript-edits-design.md`）

废弃 PostToolUse 路径（`engaku log-edit`），改用 VS Code 的 `transcript_path` 字段。原因是 **VS Code 的 `toolNames` 过滤器不可靠**，`read_file` 等非编辑操作也触发 hook，产生大量假阳性。新方案在 Stop hook 中直接解析 JSONL transcript，提取实际成功的编辑操作。经过与实际 git 状态对比验证，零假阳性零漏报。

---

## 项目审计 I：2026-04-09

第一次正式审计（`docs/project-audit-2026-04-09.md`）发现 12 个问题，分为 4 个优先级：

**P0** — `prompt-check` hook 模板从未存在（功能已实现但从未在 init 中安装过）；`cmd_stats` 的覆盖率分析对实际项目无效（module name ≠ package directory name）。

**P1** — 4 个 `cmd_*.py` 缺少 `main()` 入口；`cmd_stats` 无测试文件；knowledge-keeper 模板硬编码 model 字段。

**P2** — check-update 输出格式不一致；mtime 判断逻辑重复；MAX_CHARS 值在四处不一致。

**P3** — README 完全为空；overview.md 仍为空模板；pyproject.toml 缺 license。

### Config 统一与代码去重（`docs/config-refactor-plan.md`）

审计的一个重要产出是决定提取 `constants.py` 和 `utils.py`。当时 4 份 `read_hook_input()`、3 份 `parse_frontmatter()`、2 份 `is_code_file()` 散落在各 `cmd_*.py` 中。引入 `engaku.json` 作为统一项目配置。

---

## Agent 工作流修复（2026-04-10）

2026-04-10 是密集的 agent 设计修复日，产出了 4 个任务和 1 个决策记录：

### 决策 001：Planner 编辑范围限制

**触发事件**：planner agent 在执行任务时**直接编辑了源代码文件**（cmd_init.py、测试文件、agent 模板文件），而不是写计划让 dev 执行。更严重的是，在被告知修正边界后，planner **再次犯同样的错误**。

**根因**："You do NOT" 列表太窄，仅禁止"application or test code"，其余默认可编辑。

**决策**：`edit` 工具仅允许用于 `.ai/tasks/`、`.ai/decisions/`、`.ai/docs/` 和 `.ai/overview.md`。

### Planner 完全重设计

planner 从"分析+派发"变为纯**分析-规划-归档 agent**：
- 移除 `handoffs` 和 `agents` 字段
- 不再自动 handoff 到 dev（消除 planner → dev → scanner-update → knowledge-keeper 的 subagent 链爆炸）
- 拥有 `.ai/tasks/`、`.ai/decisions/`、`.ai/docs/` 的排他写权限
- 用户手动在 planner 和 dev 之间切换

### Reviewer Agent 引入

**问题**：任务生命周期所有权分裂——planner 既规划又审核，用户必须手动切换到 planner 请求审批。

**解决**：引入 reviewer agent 作为 `status: done` 的唯一授权方。验证协议：运行验证命令 → 读输出 → 逐项判定 PASS/FAIL。全部 PASS → `status: done`。任何 FAIL → 重置 `[x]` 为 `[ ]` 并附注失败原因。

配套创建了 `cmd_task_review.py` 作为 Stop hook，检测所有 checkbox 已勾选的任务并提示用户使用 handoff。

### Task Lifecycle Clarity

明确了 dev 和 planner 在任务文件上的分工：
- dev **可以** tick `[ ]` → `[x]`（机械进度跟踪）
- dev **不能** 修改 `status:`、创建/删除任务文件、更改任务结构
- planner 拥有 `status:` 和任务结构的排他权限
- reviewer 拥有 `status: done` 的排他权限

### Agent Prompt 精简

清除跨 agent 重复内容（module file format 代码块、forbidden phrases 列表），对 knowledge-keeper 加"先读源码"硬规则，对 scanner 改为包含测试文件。

---

## 第四阶段：原生简化（V4, ~2026-04-10 设计，2026-04-13 实施）

### 为什么 Module Knowledge 失败了

V4 的设计文档（`docs/v4-native-simplification.md`）以一张成本表终结了 module knowledge 体系：

| 机制 | 用途 | 代价 |
|------|------|------|
| knowledge-keeper agent | subagent 调用更新 module | 专用 agent + subagent-start hook + dev 中的调用规则 |
| scanner / scanner-update agents | 发现未覆盖文件、创建 module | 两个专用 agent + 复杂分类逻辑 |
| check-update Stop hook | 强制检测 stale module | 最大源文件 271 行，对非编码 agent 误触发 |
| prompt-check hook | 提醒 unclaimed/stale | stale/unclaimed 提醒逻辑 |
| validate / stats 命令 | 校验 module 格式、统计覆盖率 | 两个专用命令 |

**而 VS Code 原生的 `.github/instructions/*.instructions.md` + `applyTo` glob 完全覆盖了 module index 的路由功能** — 当 agent 打开匹配文件时，VS Code 自动注入对应 instructions，无需 engaku 扫描、索引、提醒。

### 外部参考

- **Claude Code** 的 CLAUDE.md 体系：多级层次 + `.claude/rules/*.md` 支持 `paths:` glob。关键启示：路径条件知识注入是成熟方案，不需要自建。
- **Hermes Agent** 的 SQLite + FTS5 跨 session 记忆：关键启示：跨 session 记忆是独立能力，不依赖 module knowledge。
- **VS Code 原生特性**：`copilot-instructions.md`（全局）+ `.instructions.md`（`applyTo` 路径条件）已完全覆盖需求。

### 关键删除

- `.ai/modules/` 目录和所有 module 文件
- `.ai/rules.md`（合并入 `copilot-instructions.md`）
- knowledge-keeper agent、scanner-update agent
- `cmd_validate.py`、`cmd_stats.py`、`cmd_subagent_start.py`
- 所有 stale/unclaimed 检测逻辑

### 关键新增

- `.github/instructions/*.instructions.md` — 替代 module knowledge
- `.github/skills/` — 捆绑安装工作流方法论
- inject 注入改为 overview + active-task（删除 module index）
- scanner 转型为生成 `.instructions.md` 的工具

### 捆绑 Skills

V4 决定将 `.github/skills/` 纳入 init 生成结构。初始切入点：
- `systematic-debugging` — bug/测试失败的系统化调试方法
- `verification-before-completion` — 声明完成前的证据验证
- `frontend-design` — 前端页面/组件设计

### 教训

V4 是项目的**战略转折点**：从"知识管理框架"收缩为"工作流守卫 + 上下文注入器"。这个收缩是正确的——减少了约 750-800 行代码的净删除，同时用 VS Code 原生能力完全覆盖了被删除功能。

---

## 项目审计 II：2026-04-13

V4 实施后的第二次审计（`.ai/docs/2026-04-13-project-audit.md`）发现项目**尚未达到"开箱即用"水平**，综合评分 2.6/5。

### 最严重的问题

1. **`subagent-start` 幽灵引用** — V4 删除了 `cmd_subagent_start.py`，但 dev.agent.md 的 SubagentStart hook 仍然调用 `engaku subagent-start`。**每次 SubagentStart 事件都会报 `command not found`。** P0 级阻断。

2. **README 文档失真** — 列出 9 个子命令，其中 3 个（subagent-start, validate, stats）不存在。

3. **check-update 是空壳** — 读 stdin、检查 stop_hook_active、return 0。每次 Stop 事件白白启动一次 Python 进程。

4. **残留 V3 常量** — `FORBIDDEN_PHRASES`、`MIN_CHARS`、`MAX_CHARS` 等没有任何代码使用。

### V4 后清理（2026-04-14）

`2026-04-14-post-v4-consistency-cleanup` 任务修复了 V4 遗留的一致性问题：移除 SubagentStart ghost hook、同步 README、删除 check-update 空逻辑、清理死常量、改善 overview.md 模板。

---

## 下一步分析与外部调研（2026-04-14）

`.ai/docs/2026-04-14-next-iteration-analysis.md` 对三个外部项目和 VS Code 最新特性进行了深度调研：

### Agent Plugins（最重要发现）

VS Code 推出了完整的 **plugin 系统**（Preview）— 可从 marketplace 安装或从 Git URL 直接安装。Engaku 理论上可以转型为 Agent Plugin，但需要放弃 Python 实现（hooks 只能是 shell commands），当前 85+ 个 Python 测试全部失去意义。保留为 hybrid 方案（plugin 格式 + CLI 实现）或纯 CLI 架构。

### 三项可选迭代方向

| 方向 | 风险 | 收益 |
|------|------|------|
| A: 渐进改良 | 低 | 中等 — 修补已知问题 + engaku update |
| B: 转型 Agent Plugin | 中等 | 高 — 一键安装 |
| C: 生成集中式 hooks.json | 低 | 中等 — Chat Customizations Editor 集成 |

### Skills 与外部能力研究

`.ai/docs/skills-and-features-research.md` 研究了：
- **anthropics/skills** — 文档处理 Skills（PDF/docx/xlsx），但 License: Proprietary 且依赖链重
- **tanweai/pua** — "施压修辞"提升 AI 问题解决能力。可借鉴的模式：spin detection、assumption inversion、anti-rationalization
- **thedotmack/claude-mem** — SQLite + Chroma 向量数据库的跨 session 记忆，过重但架构有参考价值

---

## 决策 002：删除 check-update 和 log-read 命令（2026-04-15）

V4 之后最重要的一个删减决策：

- `check-update` — 变成空壳（读 stdin → 检查 stop_hook_active → return 0），每次 Stop 事件白白启动 Python 进程
- `log-read` — 写 `.ai/access.log` 但没有任何命令或工作流消费这个日志

**决策**：两个命令全部删除。Stop hook 从 2 个减为 1 个（仅 `task-review`）。如果未来需要 Stop hook 功能，扩展 `task-review` 而非复活 `check-update`。

---

## 第五阶段：清理与发布准备（V5 / v0.2.0, 2026-04-15）

`2026-04-15-v5-cleanup-and-publish` 是一个综合性任务：

### 核心变更

1. **删除 check-update + log-read** — 连带清除所有 `IGNORED_*` 常量、`ACCESS_LOG`、`is_code_file()`、`parse_transcript_edits()` 及其 ~200 行测试
2. **增强 prompt-check** — 在关键词匹配之外，注入当前 active-task 的未完成步骤
3. **PyPI 发布准备** — 版本号升至 0.2.0，添加 classifiers/URLs/`--version`，创建 CHANGELOG.md
4. **README 全面重写**

### Reviewer SubagentStart 上下文注入

同日的 `2026-04-15-reviewer-subagent-context` 任务为 reviewer agent 添加了 SubagentStart hook：当 dev handoff 到 reviewer 时，自动注入 overview + active-task 上下文，避免 reviewer 在空白上下文中启动。

### Skill 增强

`2026-04-15-skill-enhancements` 基于 PUA 研究结果增强了现有 skill 并创建了新 skill：
- `systematic-debugging` 新增 "Phase 0: Spin Detection" + Assumption Inversion
- `verification-before-completion` 新增 Anti-Rationalization 表
- 新建 `proactive-initiative` skill — "修一个 bug，检查一类 bug"

---

## 第六阶段：发布与打磨（v0.3.0 – v0.5.0, 2026-04-16 – 04-17）

### v0.3.0（2026-04-16）

`2026-04-16-v0.3.0-release-and-skills` — 首次正式 PyPI 发布：
- 新增 `mcp-builder` skill（适配自 anthropics/skills，指导构建 MCP 服务器）
- 新增 `doc-coauthoring` skill（3 阶段协作文档工作流）
- 创建 `.gitignore`
- GitHub Actions CI/CD：CI 矩阵 Python 3.8/3.9/3.11，Trusted Publisher 发布

### CI/CD 基础设施（2026-04-16）

`2026-04-16-cicd-and-pypi-publish` 建立了完整的发布管线：
- `ci.yml` — 每次 push/PR 运行测试
- `publish.yml` — tag `v*.*.*` → build + publish to PyPI via OIDC Trusted Publisher（无需 API token）
- 发现并修复了 `pyproject.toml` 的 package-data 问题（模板子目录未打包）

### v0.3.1（2026-04-16）

`2026-04-16-agent-cleanup-v0.3.1` — 发现 v0.3.0 发布后的手动清理未同步到 live 文件：
- planner agent 仍引用已删除的 `.ai/rules.md`
- reviewer agent 仍引用 `.ai/modules/`

### Template 去污染（v0.3.2 → v0.4.0, 2026-04-16）

`2026-04-16-template-decontamination` 揭示了一个被忽视的问题：**engaku init 的模板文件包含了大量 engaku 自身特定的内容**。

- `copilot-instructions.md` 模板包含"Run `engaku apply` to push changes"——对目标项目来说毫无意义
- `overview.md` 模板预填了 `src/` / `tests/` 目录——engaku 自身的目录结构
- 3 个 `.instructions.md` stub（hooks、templates、tests）——engaku 特定的分类

决策：
- 删除预安装的 `.instructions.md` 存根——scanner agent 已负责按项目生成
- 清理 `copilot-instructions.md` 和 `overview.md` 模板中所有 engaku 特定内容
- v0.4.0 版本号（init 输出变更，3 个文件不再生成）

### v0.5.0（2026-04-17）

`2026-04-17-v050-update-command` — 解决**最后也是最重要的用户体验缺口**：

**问题**：`engaku init` 不覆盖已有文件，所以已安装用户无法获得更新的 agent 定义、新 skills 或 bug 修复。

**解决**：`engaku update` 命令：
- 强制覆盖所有 agent 模板（`.github/agents/`）
- 强制覆盖所有 skill 模板（`.github/skills/`）
- 跳过用户内容（`copilot-instructions.md`、`overview.md`、`engaku.json`）
- 完成后自动调用 `engaku apply` 恢复用户的 model 配置

同时修复 `engaku.json` 模板——从空对象变为包含 4 个 agent 的默认 model 配置。新增 `brainstorming` skill。

---

## 主要教训总录

### 1. 不要自建平台已有的能力

Module knowledge 从 V1 到 V3 经历了三次迭代，最终被 VS Code 原生的 `.instructions.md` 零成本替代。750+ 行代码白写了。**教训：在自建前先彻底调研平台原生能力。**

### 2. 消费侧比生产侧更重要

Module knowledge 的写入端有三层强制机制（概率指令 + agent-scoped hook + 全局 Stop hook），但消费端——**没有人读这些文件**。没有消费者的数据就是废数据。**教训：先验证消费路径再建生产管线。**

### 3. Agent 边界必须是显式 allowlist 而非隐式 blacklist

Planner 两次越权编辑源文件，都因为 "You do NOT" 列表太窄而非 "You may only" 列表太宽。**教训：对 AI agent 的权限控制用 allowlist，不用 blacklist。**

### 4. 全局 hook 是 code smell

所有 5 个全局 hook 最终都被迁移为 agent-scoped hook。全局 hook 导致 subagent 被污染、非编码 agent 被阻断。**教训：默认使用 agent-scoped hook，仅在有明确跨 agent 需求时才用全局 hook。**

### 5. 空壳命令要尽早删除

`check-update` 在 V4 后变成空壳，每次 Stop 事件启动一次 Python 进程什么都不做。它在代码中存活了两天后才被删除。`log-read` 的 access log 从未被任何消费者使用。**教训：没有消费者的功能不是"可选功能"，是技术债务。**

### 6. 模板文件必须通用

engaku 的模板文件在三个版本中都包含了自身特定的内容（engaku.json 引用、src/tests 目录、instruction 分类）。这对目标项目来说是噪音。直到 v0.4.0 才彻底清理。**教训：模板是给用户的，不是给自己的。每次修改模板都要问"其他项目看到这个有意义吗？"**

### 7. Transcript 比 Hook 过滤更可靠

PostToolUse hook 的 `toolNames` 过滤器不可靠，`read_file` 也会触发。改用 transcript 解析后，零假阳性零漏报。**教训：VS Code hook 的过滤能力有限，对于需要精确性的场景，优先使用 transcript 事后分析。**

### 8. Dogfooding 是最好的验证

engaku 始终用自己的工具开发自己。V4 清理阶段发现的所有问题（ghost hook、空壳命令、模板污染）都是在 dogfooding 过程中暴露的。**教训：如果你自己不是第一个用户，你不会发现真正的问题。**

### 9. 审计驱动的开发节奏

项目经历了两次正式审计（04-09、04-13），每次都产出了分级问题清单和优先执行建议。没有审计的迭代是盲目的。**教训：定期对项目做全面审计，用 P0-P3 分级清单驱动下一轮迭代。**

### 10. 三角色分工是稳态

经过 4 次迭代，最终稳定在 planner / dev / reviewer 三角色分工：
- planner 拥有分析、规划、决策记录
- dev 拥有代码实现、checkbox 进度
- reviewer 拥有验证和 `status: done`

这个分工消除了之前 planner 越权编辑、dev 和 knowledge-keeper 职责交叉等问题。

---

## 版本演进时间线

| 日期 | 版本 | 里程碑 |
|------|------|--------|
| 04-07 | — | 项目缘起，架构决策（CLI over MCP），初始设计 |
| 04-07 | V1 | MVP 实现：6 子命令 + 3 agent + module knowledge |
| 04-08 | V2 | 实测修补：git 依赖解除、变更文件列表、冷启动 /seed |
| 04-08 | V3 | 架构重构：控制面/数据面分离、module index 路由、职责重分配 |
| 04-09 | — | 项目审计 I：12 个问题、config 统一、代码去重 |
| 04-10 | — | Agent 工作流修复：planner 边界、reviewer 引入、task lifecycle |
| 04-10 | V4 设计 | 原生简化设计：删除 module knowledge，拥抱 .instructions.md |
| 04-13 | v0.1.0 | V4 实施：首次可发布版本 |
| 04-13 | — | 项目审计 II：发现 ghost hook、空壳命令、模板污染 |
| 04-14 | — | Post-V4 清理 + 外部调研（Agent Plugins、Skills 研究） |
| 04-15 | v0.2.0 | V5 清理：删除 check-update/log-read、增强 prompt-check、PyPI 准备 |
| 04-15 | — | Skill 增强：spin detection、anti-rationalization、proactive-initiative |
| 04-16 | v0.3.0 | 正式 PyPI 发布 + CI/CD + mcp-builder/doc-coauthoring skills |
| 04-16 | v0.3.1 | 修复 planner/reviewer agent 中的残留引用 |
| 04-16 | v0.4.0 | 模板去污染：删除 instruction 存根，清理 engaku 特定内容 |
| 04-17 | v0.5.0 | `engaku update` 命令 + engaku.json 默认配置 + brainstorming skill |

---

## 当前状态（v0.5.0, 2026-04-17）

Engaku 已从最初的"知识管理框架"收缩为精准的**"工作流守卫 + 上下文注入器"**：

**5 个子命令**：`init`、`inject`、`prompt-check`、`task-review`、`apply`、`update`

**4 个 agent 角色**：dev、planner、reviewer、scanner

**7 个捆绑 skills**：systematic-debugging、verification-before-completion、frontend-design、proactive-initiative、mcp-builder、doc-coauthoring、brainstorming

**Hook 管线**：SessionStart → inject、SubagentStart → inject、PreCompact → inject、UserPromptSubmit → prompt-check、Stop → task-review

**零第三方依赖，Python ≥3.8，70+ 测试全部通过，PyPI 发布。**
