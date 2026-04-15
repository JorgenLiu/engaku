Related task: none (research document)

# Skills & Features Research — 2026-04-15

三个外部项目 + Copilot 最新文档的调研分析，评估对 engaku 的适用性。

---

## 1. anthropics/skills — 文档处理 Skills

**仓库**: https://github.com/anthropics/skills/tree/main/skills

### 概述

Anthropic 官方维护的 skill 集合，包含文档类 skill（docx、pdf、pptx、xlsx）以及其他通用 skill（canvas-design、frontend-design、mcp-builder 等）。

### 文档 Skills 内容分析

| Skill | 读取 | 创建 | 编辑 | 依赖 |
|-------|------|------|------|------|
| **pdf** | pypdf, pdfplumber, pdftotext | reportlab | 有限（watermark、merge） | pypdf, pdfplumber, reportlab, pytesseract |
| **docx** | pandoc, unpack XML | docx-js (npm) | unpack→edit XML→repack | pandoc, npm docx, LibreOffice |
| **pptx** | markitdown | pptxgenjs (npm) | unpack→edit→repack | npm pptxgenjs, LibreOffice, Poppler |
| **xlsx** | pandas, openpyxl | openpyxl | openpyxl | pandas, openpyxl, LibreOffice |

### 与 engaku 的适配性评估

**可以引入的**:
- **pdf skill** — 最适合引入。读取依赖（pypdf、pdfplumber）可通过 pip 安装，不需要 LibreOffice。纯读取场景（提取文本、表格）是最常见需求。
- **xlsx skill** — pandas + openpyxl 是 Python 生态常用工具，纯读取和数据分析场景适用。

**引入有困难的**:
- **docx skill** — 创建依赖 npm docx-js，编辑需要 pandoc + LibreOffice，工具链较重。
- **pptx skill** — 创建依赖 npm pptxgenjs，需要 LibreOffice 做 PDF 转换和 QA。

**关键问题**:
1. **License: Proprietary** — anthropics/skills 的文档 skill 标注为 `license: Proprietary. LICENSE.txt has complete terms`，不能直接复制。
2. **依赖链重** — 这些 skill 依赖 LibreOffice、pandoc、npm packages 等，与 engaku "零三方依赖" 的约束冲突。注意：此约束仅针对 engaku CLI 本身（Python stdlib only），如果将 skill 作为模板分发到用户项目中，skill 内容可以引用外部工具（由用户项目自行安装）。
3. **scripts/ 目录** — anthropics 的 skill 引用了大量 `scripts/` 辅助脚本（unpack.py、pack.py、recalc.py、validate.py、soffice.py 等），这些是 skill 的关键组成部分，没有它们 skill 无法工作。

### 建议

| 方案 | 描述 | 可行性 |
|------|------|--------|
| **A. 精简版 PDF 读取 skill** | 只保留读取（pypdf/pdfplumber/pdftotext），去掉创建和编辑 | ★★★★★ 推荐 |
| **B. 精简版 Excel 读取/分析 skill** | pandas + openpyxl 纯读取和分析 | ★★★★☆ |
| **C. 完整引入** | 照搬 anthropics 的完整 skill + scripts | ★★☆☆☆ License 问题 + 过重 |
| **D. 提供安装指引** | 在 engaku 文档中指导用户自行从 anthropics/skills 复制 | ★★★☆☆ 低成本 |

**推荐方案**: A + B。按照 SKILL.md 标准自行撰写精简版的 PDF 和 Excel 读取 skill，作为 engaku 模板的一部分。不碰 license 问题，同时满足最常见需求。

---

## 2. tanweai/pua — 提升模型处理能力

**仓库**: https://github.com/tanweai/pua (16.1k ⭐)

### 概述

PUA (Performance Under Assessment) 通过"施压修辞"+"系统方法论"+"主动性强制"三个维度来提升 AI coding agent 的问题解决能力。其 benchmark 数据显示：修复数 +36%，验证次数 +65%，工具调用 +50%。

### 核心机制

1. **三条红线**:
   - 闭环意识 — 交付必须有验证输出
   - 事实驱动 — 禁止未验证的归因
   - 穷尽一切 — 通用方法论 5 步走完前禁止放弃

2. **压力升级 (L0-L4)**: 根据失败次数逐级加压，强制切换方案

3. **方法论智能路由**: 按任务类型自动选择最优方法论（13 种"味道"）

4. **能动性等级**: 被动(3.25) vs 主动(3.75) 的行为对比表

5. **抗合理化表**: 针对常见借口的反击和触发机制

### 与 engaku 现有 skill 的对比

| PUA 机制 | engaku 现有 | 差距分析 |
|----------|------------|---------|
| 三条红线 (闭环/事实/穷尽) | verification-before-completion 覆盖了"闭环" | 缺少"事实驱动"和"穷尽一切"的强调 |
| 压力升级 L0-L4 | 无 | engaku 的 skill 是纯方法论，没有"施压"维度 |
| 通用方法论 5 步 | systematic-debugging 的 4 phases | 高度重叠，PUA 的步骤更精炼 |
| 7 项检查清单 | systematic-debugging 的 Red Flags | PUA 的清单更明确可执行 |
| 能动性等级 | 无 | engaku 缺少主动性方面的指导 |
| 抗合理化表 | 无 | PUA 独有，直接针对模型的常见逃避行为 |
| 方法论智能路由 | 无 | 过于复杂，不适合 engaku 的简洁理念 |
| 味道/修辞 | 无 | 娱乐性质，不适合 engaku |

### 可借鉴的模式

1. **强化 systematic-debugging**: 借鉴 PUA 的"5 步方法论"来精炼我们的 4 phases，特别是：
   - "闻味道" — 先识别是否在原地打转
   - "反转假设" — 主动尝试相反的假设
   - "复盘" — 解决后检查同类问题

2. **强化 verification-before-completion**: 借鉴 PUA 的"抗合理化表"，增加常见虚假完成模式的检测：
   - "should pass now" — 信心不是证据
   - "似乎已修复" — 没跑测试不算
   - "差不多就行" — 模糊完成不是完成

3. **新 skill 候选 — proactive-initiative (主动性)**:
   - 从 PUA 的"能动性等级"表和"Owner 意识"章节提炼
   - 每次任务完成后的自检清单：修复验证了吗？同模块有类似问题吗？上下游受影响吗？
   - 核心思路："修一个 bug，检查一类 bug"

4. **不建议引入的**:
   - 压力修辞/PUA 语气 — 与 engaku 的专业、简洁风格不符
   - 13 种味道/方法论路由 — 过度工程化
   - L0-L4 升级机制 — 需要状态追踪，不适合 SKILL.md 的纯指令格式
   - 失败计数持久化 — 需要 hooks 配合，engaku hooks 目前是 Python 脚本，不用于 PUA 式状态管理

---

## 3. thedotmack/claude-mem — 记忆系统

**仓库**: https://github.com/thedotmack/claude-mem (56.4k ⭐)

### 概述

为 Claude Code 设计的持久化记忆压缩系统。自动捕获工具使用观察，生成语义摘要，注入到未来 session 中。

### 核心架构

1. **5 个 Lifecycle Hooks**: SessionStart、UserPromptSubmit、PostToolUse、Stop、SessionEnd
2. **Worker Service**: 独立的 HTTP API (port 37777)，基于 Bun 运行
3. **SQLite 数据库**: 存储 sessions、observations、summaries
4. **Chroma 向量数据库**: 混合语义 + 关键词搜索
5. **Progressive Disclosure**: 三层检索 — search (索引) → timeline (上下文) → get_observations (全文)
6. **MCP 搜索工具**: 4 个 MCP tools 提供记忆查询

### 与 engaku 的对比

| claude-mem 功能 | engaku 现有方案 | 差距分析 |
|----------------|---------------|---------|
| 跨 session 记忆持久化 | `.ai/overview.md` + `.ai/decisions/` | engaku 用文件做手动记忆，claude-mem 是自动化的 |
| 自动观察捕获 | 无 | engaku 不做自动捕获 |
| 语义搜索 | 无 | engaku 依赖 agent 的文件搜索能力 |
| SessionStart 注入 | `cmd_inject.py` 注入 overview.md | 相似思路，但 engaku 注入的是静态文件 |
| PreCompact 保存 | engaku `cmd_inject.py` PreCompact 处理 | 相似思路 |
| MCP 搜索工具 | 无 | claude-mem 需要独立服务 |

### 可借鉴的模式

1. **SessionStart 注入增强**: claude-mem 在 SessionStart 注入相关的历史观察摘要。engaku 目前只注入 `overview.md`。可以考虑：
   - 在 SessionStart 时扫描 `.ai/tasks/` 中 status=in-progress 的任务，自动注入相关上下文
   - 注入最近的 `.ai/decisions/` 内容

2. **PreCompact 状态保存**: claude-mem 在 PreCompact 时保存重要状态。engaku 已有类似机制，可以增强：
   - 保存当前任务进度的快照
   - 保存重要的决策上下文

3. **观察/学习记录**: claude-mem 自动记录 agent 的观察。可以借鉴的思路：
   - (轻量级) 在 Stop hook 中提示 agent 更新 `.ai/overview.md` 和相关文档
   - (进阶) 自动追踪本次 session 修改的文件，在 Stop 时生成简要总结

4. **不建议引入的**:
   - SQLite + Chroma 向量数据库 — 过重，违反 engaku 零依赖原则
   - 独立 Worker Service — engaku 是纯 CLI 工具 + 模板，不应该有运行时服务
   - MCP 服务器 — engaku 目前不涉及 MCP
   - `<private>` 标签隐私控制 — 场景过于特殊

---

## 4. VS Code Copilot 最新功能 (v1.115, 2026-04-08)

### 新功能概览

| 功能 | 状态 | 与 engaku 相关性 |
|------|------|-----------------|
| **VS Code Agents App** (Preview) | 新 | 并行 agent sessions、跨 repo 任务、自定义文件仍可用 |
| **Agent Plugins** (Preview) | 新 | 标准化的 plugin 打包和分发机制 |
| **Agent-scoped Hooks** (Preview) | 新 | 在 agent.md frontmatter 中定义 hooks |
| **Agent Skills 标准** (agentskills.io) | 稳定 | 开放标准，跨工具兼容 |
| **SubagentStart / SubagentStop hooks** | 新 | 子 agent 生命周期管理 |
| **Background terminal notifications** | 实验 | agent 自动收到后台终端通知 |
| **BYOK for Business/Enterprise** | 新 | 自带 API key |
| **Chat Customizations editor** | Preview | UI 管理全部自定义配置 |
| **`/create-skill`, `/create-agent`, `/create-hook`** | 稳定 | AI 辅助生成自定义文件 |
| **Plugin marketplaces** | Preview | github/copilot-plugins, anthropics/claude-code |
| **Parent repository discovery** | 稳定 | monorepo 中发现父目录的自定义文件 |

### 对 engaku 有直接影响的

#### 4.1 Agent Plugins — engaku 可以变成 Plugin

VS Code 现在支持 agent plugin 格式，一个 plugin 可以包含:
- skills/
- agents/
- hooks/
- .mcp.json

engaku 当前通过 `engaku init` 复制模板文件到项目中。未来可以同时提供 **plugin 格式分发**，让用户通过 `Chat: Install Plugin From Source` 直接安装，或者通过 marketplace 发现。

**Plugin 格式要求**:
```
engaku-plugin/
  plugin.json              # 插件元数据
  skills/
    systematic-debugging/SKILL.md
    verification-before-completion/SKILL.md
  agents/
    dev.agent.md
    planner.agent.md
    reviewer.agent.md
  hooks/
    hooks.json             # hook 配置
  scripts/
    inject.py              # hook 脚本
```

**影响**: 这是一个较大的架构变更。engaku 目前的 `init` + 文件复制模式适合需要深度定制的用户。Plugin 模式更适合"开箱即用"的用户。两者可以共存。

#### 4.2 Agent-scoped Hooks — 简化 hook 分发

当前 engaku 的 hooks 放在 `.github/hooks/` 下。新的 agent-scoped hooks 可以直接在 `.agent.md` frontmatter 中定义：

```yaml
---
name: "dev"
hooks:
  SessionStart:
    - type: command
      command: "python -m engaku inject SessionStart"
  PreCompact:
    - type: command
      command: "python -m engaku inject PreCompact"
---
```

**影响**: 可以将 hooks 逻辑内联到 agent 定义中，减少分散的配置文件。但也降低了灵活性（hooks 绑定到特定 agent）。

#### 4.3 SubagentStart / SubagentStop Hooks

新的生命周期事件，在子 agent 创建/结束时触发。这对 engaku 的 planner → dev → reviewer 工作流可能有用：
- SubagentStart: 注入额外的项目上下文
- SubagentStop: 验证子 agent 的输出

**影响**: 目前非关键，但可以为 engaku 的 reviewer agent 增加自动化能力。

#### 4.4 Skills 存放位置扩展

VS Code 现在支持更多的 skills 存放位置:
- `.github/skills/` (engaku 现有)
- `.claude/skills/`
- `.agents/skills/`
- `~/.copilot/skills/` (个人级别)
- `chat.skillsLocations` 自定义路径

**影响**: engaku 目前只生成 `.github/skills/`，与最广泛的兼容路径一致。无需变更。

#### 4.5 `/create-skill`, `/create-agent` 等命令

VS Code 内置了 AI 辅助生成自定义文件的命令。这与 engaku 的 `init` 功能部分重叠，但 engaku 提供的是完整的、经过调试的模板集合，而 `/create-*` 是从零开始生成。

**影响**: engaku 的价值在于"经过实战验证的完整配方"，与 VS Code 的通用生成器互补而非竞争。

---

## 5. 综合建议与优先级

### 短期可执行 (当前版本可做)

| # | 建议 | 来源 | 工作量 | 价值 |
|---|------|------|--------|------|
| 1 | **增强 systematic-debugging skill** — 加入"反转假设"步骤和"原地打转检测" | PUA | 小 | 高 |
| 2 | **增强 verification-before-completion skill** — 加入"抗合理化"模式列表 | PUA | 小 | 高 |
| 3 | **新 skill: proactive-initiative** — 任务完成后的主动性自检清单 | PUA | 中 | 高 |
| 4 | **增强 SessionStart hook** — 注入 in-progress tasks 上下文 | claude-mem | 中 | 中 |

### 中期可规划

| # | 建议 | 来源 | 工作量 | 价值 |
|---|------|------|--------|------|
| 5 | **新 skill: pdf-reading** — 精简版 PDF 读取 skill | anthropics/skills | 中 | 中 |
| 6 | **新 skill: spreadsheet-analysis** — 精简版 Excel/CSV 分析 skill | anthropics/skills | 中 | 中 |
| 7 | **探索 Plugin 格式** — 将 engaku 同时以 agent plugin 形式分发 | Copilot docs | 大 | 高 |
| 8 | **Stop hook 增强** — 提示 agent 更新 .ai/ 文件 | claude-mem | 小 | 中 |

### 不建议引入

| 项目 | 来源 | 原因 |
|------|------|------|
| PUA 修辞/施压语气 | PUA | 与 engaku 的专业风格不符 |
| 13 种味道/方法论路由 | PUA | 过度工程化 |
| L0-L4 压力升级状态机 | PUA | 需要状态追踪，不适合纯 SKILL.md |
| SQLite/Chroma 向量数据库 | claude-mem | 违反零依赖原则 |
| Worker Service / MCP 服务 | claude-mem | engaku 是纯 CLI+模板 |
| 直接复制 anthropics 的 docx/pptx skill | anthropics/skills | Proprietary License + 依赖过重 |

---

## 6. 下一步

如果以上分析获得认可，后续可以为具体建议项创建 task plan：
- #1-3 可以合并为一个 "skill enhancement" 任务
- #4, #8 可以合并为一个 "hook enhancement" 任务
- #5-6 是独立的新 skill 创建任务
- #7 是一个较大的架构探索，建议先写 decision record
