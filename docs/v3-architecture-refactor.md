# Engaku V3 Architecture Refactor — Implementation Plan

> 整理自 2026-04-08 多轮设计讨论（brainstorming agent + GPT / Gemini / Claude 交叉审核）。

**Goal:** 解决 V2 审计发现的核心问题：module knowledge 是 write-only memory（只写不读）、
控制面与数据面混合、knowledge-keeper 职责过载、module 粒度过细。

**Architecture:** 纯 Python stdlib CLI + VS Code Hooks + Subagents。不引入新依赖。

---

## 诊断总结

V2 审计发现的六个结构性问题：

| # | 问题 | 根因 |
|---|------|------|
| 1 | Module files 从未被 dev agent 在编码时读取 | 消费侧缺失——没有机制告诉 agent 什么时候读哪个 module |
| 2 | copilot-instructions.md 混入了项目描述和格式模板 | 控制面（行为指令）与数据面（项目知识）未分离 |
| 3 | knowledge-keeper 承担过多职责，产出质量不一致 | 一个 mini 模型同时做 modules/rules/decisions/tasks，部分任务需要对话上下文但它看不到 |
| 4 | 一源文件一 module 粒度过细 | 6 个碎片化微文件无人消费，knowledge-keeper 自动为每个文件创建 module |
| 5 | 规则在多处重复声明（300 vs 600 字符） | 违反单一事实源原则 |
| 6 | check-update Stop hook 对所有 agent 生效 | `knowledge-check.json` 是 workspace 级 hook，brainstorming/planner 等非编码 agent 结束时也被阻断 |

---

## 设计决策

### D1: 控制面与数据面严格分离

控制面（极少变动，人工维护为主）：
- `.github/copilot-instructions.md` — 只写行为指令（10 行以内）
- `.github/agents/*.agent.md` — 各 agent 的职责定义
- `.github/hooks/*.json` — hook 配置
- `.github/instructions/*.instructions.md` — 可选的按文件类型编码规范

数据面（随代码演进，agent 维护）：
- `.ai/overview.md` — 项目架构描述
- `.ai/rules.md` — 项目约束（canonical source）
- `.ai/modules/*.md` — 模块知识
- `.ai/decisions/*.md` — 架构决策记录
- `.ai/tasks/*.md` — 任务计划

### D2: overview.md 保留为独立文件

不合并进 copilot-instructions.md。原因：overview 是高变频的项目描述，
instructions 是高信任度的行为指令，让 knowledge-keeper 频繁改 instructions file 会导致
指令漂移和注意力稀释。

### D3: copilot-instructions.md 精简为纯行为指令

清除当前的 Knowledge Structure 表格、format template、字符限制重复声明。
只保留工作流指令，所有项目约束回归 rules.md 一处定义。

### D4: inject 承担路由器角色——动态生成 module index

`engaku inject` 在 SessionStart/PreCompact 时，除注入 rules + overview 外，
自动扫描 `.ai/modules/` 的 paths: frontmatter，生成 Markdown table 索引追加到注入内容。

格式示例：
```markdown
## Module Knowledge Index
| Module | Paths | Knowledge File |
|--------|-------|----------------|
| hooks | src/engaku/cmd_inject.py, src/engaku/cmd_log_edit.py, ... | .ai/modules/hooks.md |
| quality | src/engaku/cmd_validate.py, src/engaku/cmd_stats.py | .ai/modules/quality.md |

Before modifying files listed above, read the corresponding knowledge file.
```

### D5: module 粒度改为逻辑单元

paths: frontmatter 变为 required。scanner agent 按逻辑单元（而非源文件）推荐分组。
knowledge-keeper 不再有创建新 module 文件的权限。

### D6: 职责重新分配

| 职责 | 原归属 | 新归属 | 理由 |
|------|--------|--------|------|
| 创建 module 文件 | knowledge-keeper | scanner agent | 需要全局视角和用户审核 |
| 更新 module 文件内容 | knowledge-keeper | knowledge-keeper | 不变 |
| patch overview.md 过时事实 | 无人 | knowledge-keeper | 新增，仅限 patch 不是重写 |
| 更新 rules.md | knowledge-keeper | dev agent | 需要完整对话上下文 |
| 创建 decisions | knowledge-keeper | dev agent | 需要完整对话上下文 |
| 维护 tasks checkbox | knowledge-keeper | dev agent | 不变（本已由 dev 执行） |

### D7: 多层强制机制

| 层级 | 手段 | 覆盖场景 |
|------|------|----------|
| 硬强制 | Stop hook (check-update exit 2) | 代码改了但无 module 更新 |
| 硬强制 | validate (knowledge-keeper Stop hook) | module 格式：无 paths: / 超字符限制 / 缺 heading |
| 软强制 | UserPromptSubmit hook → systemMessage | 关键词检测提示"可能有新规则" |
| 纯指令 | copilot-instructions.md + dev.agent.md | 架构决策记录等语义判断 |

### D8: 注入链路终态

```
VS Code 原生                → copilot-instructions.md（行为指令）
engaku inject SessionStart  → rules.md + overview.md + 动态 module index
engaku inject PreCompact    → 同上（systemMessage 格式）
UserPromptSubmit hook       → 关键词检测 → "可能有新规则" 软提醒
Stop hook (check-update)    → 阻断未更新 module 的会话（仅 dev agent）
```

### D9: check-update Stop hook 改为 agent-scoped

`knowledge-check.json`（workspace 级）导致所有 agent 结束时都触发 check-update，
包括 brainstorming、planner 等不写代码的 agent。

修复：将 check-update 的 Stop hook 从 `.github/hooks/knowledge-check.json` 移到
`dev.agent.md` 的 frontmatter `hooks:` 字段。VS Code 文档明确：
"Agent-scoped hooks only run when that custom agent is active."

同时删除 `.github/hooks/knowledge-check.json`，避免重复触发。

### D10: Agent model 和关键参数可配置

当前 knowledge-keeper 硬编码 `model: ['GPT-5 mini (copilot)']`，
dev/scanner 未指定 model（使用默认）。不同用户可能希望为各 agent 选择不同的模型，
也可能需要调整 MAX_CHARS 等参数。

方案：在 `.ai/rules.md` 中增加 `## Agent Configuration` 段，声明推荐的 model
和关键参数。agent.md 模板引用 rules.md 而非 hardcode。
这样用户只需修改 rules.md 一处即可调整配置。

对于 engaku init 生成的模板文件，model 字段使用合理的默认值，
用户在 init 后可根据 rules.md 中的说明自行调整。

---

## File Map

### 创建

- `.github/agents/scanner.agent.md` — 新 agent
- `.github/hooks/prompt-reminder.json` — UserPromptSubmit hook 配置
- `src/engaku/cmd_prompt_check.py` — UserPromptSubmit 关键词检测
- `src/engaku/templates/scanner.agent.md` — scanner 模板
- `src/engaku/templates/prompt-reminder.json` — prompt-reminder 模板
- `tests/test_prompt_check.py`

### 修改

- `src/engaku/cmd_inject.py` — 增加动态 module index 生成
- `src/engaku/cmd_validate.py` — 增加 frontmatter required 检查
- `src/engaku/cmd_check_update.py` — 适配 unmapped paths 处理逻辑
- `src/engaku/cmd_init.py` — 拷贝新模板、移除旧模板
- `src/engaku/cli.py` — 注册 prompt-check 子命令
- `.github/copilot-instructions.md` — 精简为纯行为指令
- `.github/agents/dev.agent.md` — 增加 agent-scoped check-update hook + 消费侧指令 + rules/decisions 职责
- `.github/agents/knowledge-keeper.agent.md` — 收紧职责，移除 rules/decisions/创建权，引用 rules.md 配置
- `.ai/rules.md` — 修复 300→600 + 统一为唯一事实源 + 增加 Agent Configuration 段
- `.ai/overview.md` — 移除 Core Modules 段
- `tests/test_inject.py` — module index 生成测试
- `tests/test_validate.py` — frontmatter required 检查测试
- `tests/test_init.py` — 更新期望文件列表

### 删除

- `.github/hooks/knowledge-check.json` — check-update 改为 dev agent-scoped hook
- `.github/prompts/seed.prompt.md` — 被 scanner agent 取代
- `.ai/modules/cmd_inject.md` — 重组后由 scanner 重新生成
- `.ai/modules/cmd_stats.md` — 同上
- `.ai/modules/cmd_check_update.md` — 同上
- `.ai/modules/cmd_validate.md` — 同上
- `.ai/modules/cmd_init.md` — 同上
- `.ai/modules/cmd_log_edit.md` — 同上
- `src/engaku/templates/seed.prompt.md` — 被 scanner agent 模板取代

---

## Tasks

设计原则：**dogfooding 优先**——尽早修好 engaku 自身的 agent 配置和工作流，
使后续 task 在 dev agent 中执行时即可受益于新的规则和流程。

### Task 1: 修复 check-update hook scoping（紧急）

**问题：** `knowledge-check.json` 是 workspace 级 Stop hook，所有 agent（包括
brainstorming/planner）结束时都会触发 check-update 阻断。

**Files:**
- Modify: `.github/agents/dev.agent.md` — 增加 agent-scoped Stop hook
- Delete: `.github/hooks/knowledge-check.json`
- Modify: `src/engaku/templates/dev.agent.md` — 同步模板
- Modify: `src/engaku/cmd_init.py` — 从 hooks 拷贝列表中移除 knowledge-check.json
- Modify: `tests/test_init.py` — 从 EXPECTED_FILES 中移除

- [x] 在 dev.agent.md frontmatter 增加 `hooks:` 字段，将 check-update Stop hook 移入：
      ```yaml
      hooks:
        Stop:
          - type: command
            command: engaku check-update
            timeout: 10
      ```
- [x] 删除 `.github/hooks/knowledge-check.json`
- [x] 同步更新 `src/engaku/templates/dev.agent.md`
- [x] 更新 cmd_init.py 移除 knowledge-check.json 拷贝
- [x] 更新 tests/test_init.py EXPECTED_FILES
- [x] Verify: `python -m pytest tests/test_init.py -v`

---

### Task 2: 精简 copilot-instructions.md + 统一 rules.md + Agent 配置

**Files:**
- Modify: `.github/copilot-instructions.md`
- Modify: `.ai/rules.md`
- Modify: `src/engaku/templates/rules.md` — 同步模板

- [x] 重写 `.github/copilot-instructions.md` 为纯行为指令（约 10 行）：
      ```markdown
      # Copilot Instructions
      - Follow all constraints in `.ai/rules.md`.
      - Before modifying code, check the injected module index for relevant
        knowledge files and read them.
      - After completing code changes, call the `knowledge-keeper` subagent.
      - If the user expressed a new constraint or preference, update `.ai/rules.md`.
      - If a significant architecture decision was made, record it in `.ai/decisions/`.
      ```
- [x] 更新 `.ai/rules.md`：修复 `≤300` → `≤600`
- [x] 在 rules.md 增加 `## Agent Configuration` 段：
      ```markdown
      ## Agent Configuration
      - knowledge-keeper model: a lightweight model (e.g. GPT-5 mini) is sufficient.
      - scanner model: use the default model for better reasoning.
      - MAX_CHARS for module knowledge body: 600 (frontmatter excluded).
      ```
- [x] 同步 `src/engaku/templates/rules.md`
- [x] Verify: `grep -rn "300 char\|≤300\|<=300" .github/ .ai/ src/engaku/templates/`

---

### Task 3: 重写 dev.agent.md + knowledge-keeper.agent.md

**Files:**
- Modify: `.github/agents/dev.agent.md`
- Modify: `.github/agents/knowledge-keeper.agent.md`
- Modify: `src/engaku/templates/dev.agent.md` — 同步模板
- Modify: `src/engaku/templates/knowledge-keeper.agent.md` — 同步模板

- [x] dev.agent.md 重写为：
      - 保留 agent-scoped check-update hook（Task 1 已加）
      - 增加 "Before modifying code, check the injected module index and
        read relevant knowledge files"
      - 增加 "If the user expressed a new constraint or preference, update `.ai/rules.md`"
      - 增加 "If a significant architecture decision was made,
        create `.ai/decisions/{id}-{slug}.md`"
      - 保留 agents: ['knowledge-keeper']
- [x] knowledge-keeper.agent.md 重写为：
      - 移除 rules / decisions / tasks 相关指令
      - 明确 "Only update existing `.ai/modules/*.md` files. Do NOT create new module files."
      - 增加 "If `.ai/overview.md` contains a description that is obviously stale
        given the current changes, patch that specific fact."
      - 强制 frontmatter 模板（paths: required）
      - 字符限制引用 rules.md：
        "Respect the MAX_CHARS limit defined in `.ai/rules.md` (body only; frontmatter excluded)."
      - model 字段引用 rules.md 推荐而非 hardcode
- [ ] 同步两个 templates/ 下的模板文件
- [ ] 确认 knowledge-keeper 的 tools 列表不包含 agent 调用权限

从本 task 完成起，后续所有 dev agent 执行即遵循新工作流。

---

### Task 4: overview.md 清理 + 删除旧 module 文件 + seed 模板

**Files:**
- Modify: `.ai/overview.md`
- Delete: `.ai/modules/cmd_inject.md`, `cmd_stats.md`, `cmd_check_update.md`,
          `cmd_validate.md`, `cmd_init.md`, `cmd_log_edit.md`
- Delete: `.github/prompts/seed.prompt.md`
- Delete: `src/engaku/templates/seed.prompt.md`
- Modify: `src/engaku/cmd_init.py` — 移除 seed.prompt.md 拷贝逻辑
- Modify: `tests/test_init.py` — 移除 seed 期望

- [x] 从 `.ai/overview.md` 移除 `## Core Modules` 段（由 inject 动态 index 替代）
- [x] 保留 `## Overview` 段和 `## Directory Structure` 段
- [x] 删除 6 个旧 module 文件（cmd_*.md）
- [x] 删除 seed.prompt.md（模板 + .github/prompts/ 下的拷贝）
- [x] 更新 cmd_init.py 移除 seed 相关拷贝
- [x] 更新 tests/test_init.py
- [x] Verify: `python -m pytest tests/ -v`

> **注意：** 删除旧 module 后到 Task 9 重建前，check-update 的 Stop hook 仍会在
> dev agent 中触发阻断。这是预期行为——Task 5 的 scanner agent 创建后立即执行
> Task 9 重建 module。

---

### Task 5: 创建 scanner agent

**Files:**
- Create: `.github/agents/scanner.agent.md`
- Create: `src/engaku/templates/scanner.agent.md`
- Modify: `src/engaku/cmd_init.py` — 拷贝 scanner.agent.md
- Modify: `tests/test_init.py` — 更新期望文件列表

- [x] 编写 scanner.agent.md：
      - user-invocable: true
      - tools: ['read', 'search', 'edit']
      - 职责：扫描仓库 → 按逻辑单元推荐 module 分组 → 展示给用户审核 →
        生成带 paths: frontmatter 的 module 文件
      - 明确 NOT 生成 rules.md
      - 可初始化或更新 overview.md 的项目描述
      - model 字段引用 rules.md 推荐
- [x] 复制为 `src/engaku/templates/scanner.agent.md`
- [x] 更新 `cmd_init.py` 将 scanner agent 纳入拷贝列表
- [x] 更新 `tests/test_init.py` EXPECTED_FILES
- [x] Verify: `python -m pytest tests/test_init.py -v`

---

### Task 6: 用 scanner agent 重新划分 module（dogfooding）

**前提：** Task 5 完成。

- [ ] 调用 scanner agent 对 engaku 自身仓库执行扫描
- [ ] 审核推荐的模块划分（预期约 3-4 个逻辑单元）
- [ ] 确认生成的 module 文件都有 paths: frontmatter 且 body ≤600 字符
- [ ] 运行 `engaku validate` 确认新 module 文件全部通过
- [ ] Verify: `python -m pytest tests/ -v`

> **从本 task 完成起，engaku 拥有完整的 module coverage。后续 task 在 dev agent
> 中执行时，inject 的动态 index 即可正确路由，knowledge-keeper 可正常更新 module。**

---

### Task 7: 修改 inject 生成动态 module index

**Files:**
- Modify: `src/engaku/cmd_inject.py`
- Modify: `tests/test_inject.py`

- [x] 新增 `_build_module_index(cwd)` 函数：扫描 `.ai/modules/*.md`，
      读取 paths: frontmatter，生成 Markdown table 字符串
- [x] 无 module 文件时返回空字符串（不注入 index 段）
- [x] module 文件缺 paths: frontmatter 时在 table 中 Paths 列显示 "(unscoped)"
- [x] 在 `run()` 中将 module index 追加到 `additional_context`，末尾加一句
      "Before modifying files listed above, read the corresponding knowledge file."
- [x] 编写测试：无 modules → 无 index；有 modules 带 paths → table 正确；
      有 modules 缺 paths → "(unscoped)" 标记
- [x] Verify: `python -m pytest tests/test_inject.py -v`

---

### Task 8: validate 增加 frontmatter required 检查

**Files:**
- Modify: `src/engaku/cmd_validate.py`
- Modify: `tests/test_validate.py`

- [ ] 增加检查：module 文件如果没有 `paths:` frontmatter，输出 warning（不阻断，exit 0）
- [ ] 增加检查：frontmatter 格式错误（前有空行、无 `---` closure）→ fail
- [ ] 增加检查：`paths:` 列表为空 → warning
- [ ] 编写测试覆盖上述三种情况
- [ ] Verify: `python -m pytest tests/test_validate.py -v`

---

### Task 9: 创建 UserPromptSubmit 关键词检测

**Files:**
- Create: `src/engaku/cmd_prompt_check.py`
- Create: `src/engaku/templates/prompt-reminder.json`
- Create: `tests/test_prompt_check.py`
- Modify: `src/engaku/cli.py`
- Modify: `src/engaku/cmd_init.py`

- [x] 创建 `cmd_prompt_check.py`：
      - `_read_hook_input()` 读取 stdin JSON
      - 从输入中提取 `prompt` 字段
      - 关键词列表：`["从现在开始", "不要用", "always", "never", "规则", "rule",
        "preference", "constraint", "禁止", "必须", "要求"]`
      - 命中时输出 `{"systemMessage": "The user's prompt may contain a new project
        rule or constraint. If confirmed, update .ai/rules.md after completing the task."}`
      - 未命中时输出 `{}`
      - 始终 exit 0（纯提醒，不阻断）
- [x] 创建 `prompt-reminder.json` hook 配置（UserPromptSubmit event）
- [x] 在 `cli.py` 注册 `prompt-check` 子命令
- [x] 在 `cmd_init.py` 加入拷贝列表
- [x] 编写测试：命中关键词 → systemMessage 存在；无命中 → 空 JSON；无 prompt → 空 JSON
- [x] Verify: `python -m pytest tests/test_prompt_check.py -v`

---

### Task 10: check-update 适配 unmapped paths

**Files:**
- Modify: `src/engaku/cmd_check_update.py`
- Modify: `tests/test_check_update.py`

- [x] 修改 `run()`：如果 changed files 中有文件不被任何 module 的 `paths:` 覆盖，
      在 stderr 中额外输出 "The following files are not covered by any module
      knowledge file: ... Consider running the scanner agent to add module coverage."
- [x] 仍然执行正常的 module 更新检查逻辑（行为不变，只是增加信息）
- [x] 编写测试覆盖 unmapped files 提示
- [x] Verify: `python -m pytest tests/test_check_update.py -v`

---

## 执行顺序

```
Phase 1: 修复 + 清理（让 engaku 自身工作流立即可用）
  Task 1  hook scoping 修复（紧急：解除非编码 agent 的误阻断）
  Task 2  精简 instructions + 统一 rules + Agent 配置
  Task 3  重写 dev + knowledge-keeper agent 指令
  Task 4  清理 overview + 删除旧 module + 删除 seed

  → 检查点：dev agent 指令正确，rules 统一，旧碎片清除。

Phase 2: 重建 module 体系（建立 dogfooding 基础）
  Task 5  创建 scanner agent
  Task 6  用 scanner 重新划分 engaku module（dogfooding）

  → 检查点：engaku 拥有按逻辑单元划分的 module，所有文件有 paths: 覆盖。
  → 从此刻起，后续代码修改可被正确路由和校验。

Phase 3: 消费侧 + 校验增强（在新 module 体系上开发）
  Task 7  inject 动态 module index
  Task 8  validate frontmatter required 检查

  → 检查点：inject 输出包含 module index table，validate 检查 frontmatter。

Phase 4: 新能力扩展
  Task 9  UserPromptSubmit 关键词检测
  Task 10 check-update unmapped paths 提示

全量验证：python -m pytest tests/ -v
```

**Dogfooding 策略说明：**
- Phase 1 只改配置文件和 agent 指令，不改 Python 代码逻辑，所以不会破坏现有测试。
- Phase 1 完成后即可用 dev agent 执行后续 task，新的 agent 指令立即生效。
- Phase 2 的 Task 6（scanner 重建 module）确保 Phase 3 开发时
  knowledge-keeper 能正确维护 module。
- Phase 3 的代码修改（inject/validate）在已有 module coverage 下进行，
  dev agent 可按 index 读取 module 知识。

---

## Out of Scope

- 不改变 engaku 的技术栈（仍然是 stdlib-only Python CLI）
- 不改变 hook 的生命周期事件使用方式（SessionStart / PostToolUse / Stop / PreCompact）
- 不实现 `.instructions.md` + `applyTo` 的方案（保持 module files 的职责边界）
- 不实现 transcript_path 深度分析（成本不可控，用 UserPromptSubmit 关键词替代）
- 不实现全量 module 注入到 SessionStart（context 爆炸风险）
- edit-log / access-log 的 PostToolUse hook 保持 workspace 级（它们对所有 agent 生效是正确的）
