# Engaku CLI Implementation Plan

**Goal:** 实现 engaku CLI 工具，让 Copilot 通过 VS Code 原生能力（Hooks + Subagents）实现跨会话持久记忆。

**Architecture:** 纯 Python stdlib CLI，6 个子命令（`init`、`inject`、`check-update`、`validate`、`log-read`、`stats`），通过 VS Code Agent Hooks 在会话生命周期的关键点被调用。AI 直接用 `edit`/`create_file` 读写 `.ai/` 知识文件，CLI 负责初始化、注入上下文、事后校验和度量采集。

**Tech Stack:** Python ≥3.8，仅 stdlib（`argparse`、`pathlib`、`subprocess`、`json`、`sys`、`re`、`datetime`）

**Constraints:**
- 不使用 3.9+ 语法（无 `str.removeprefix()`、`dict | dict`、`match/case`、`X | Y` 注解）
- 零第三方依赖
- 发布方式：`pip install git+https://github.com/me/engaku`

---

## File Map

### Create（engaku repo）

```
engaku/
├── pyproject.toml
├── README.md                          （已存在，需更新）
├── src/
│   └── engaku/
│       ├── __init__.py
│       ├── __main__.py                ← python -m engaku 入口
│       ├── cli.py                     ← argparse 主路由
│       ├── cmd_init.py                ← engaku init
│       ├── cmd_inject.py              ← engaku inject
│       ├── cmd_check_update.py        ← engaku check-update
│       ├── cmd_validate.py            ← engaku validate
│       ├── cmd_log_read.py            ← engaku log-read
│       ├── cmd_stats.py               ← engaku stats
│       └── templates/                 ← init 生成的模板文件
│           ├── rules.md
│           ├── overview.md
│           ├── dev.agent.md
│           ├── knowledge-keeper.agent.md
│           ├── planner.agent.md
│           ├── copilot-instructions.md
│           ├── session.json
│           ├── knowledge-check.json
│           └── access-log.json
└── tests/
    ├── __init__.py
    ├── test_inject.py
    ├── test_check_update.py
    ├── test_validate.py
    ├── test_log_read.py
    └── test_init.py
```

### 目标 repo 生成的文件（由 `engaku init` 创建）

```
<target-repo>/
├── .ai/
│   ├── rules.md
│   ├── overview.md
│   ├── modules/               （空目录，含 .gitkeep）
│   ├── decisions/             （空目录，含 .gitkeep）
│   └── tasks/                 （空目录，含 .gitkeep）
└── .github/
    ├── agents/
    │   ├── dev.agent.md
    │   ├── knowledge-keeper.agent.md
    │   └── planner.agent.md
    ├── hooks/
    │   ├── session.json
    │   ├── knowledge-check.json
    │   └── access-log.json
    └── copilot-instructions.md
```

---

## Tasks

### Task 1: 项目骨架 + pyproject.toml

**Files:**
- Create: `pyproject.toml`, `src/engaku/__init__.py`, `src/engaku/__main__.py`, `src/engaku/cli.py`

- [ ] 1.1 创建 `pyproject.toml`，配置：
  ```toml
  [build-system]
  requires = ["setuptools>=45"]
  build-backend = "setuptools.backends._legacy:_Backend"

  [project]
  name = "engaku"
  version = "0.1.0"
  description = "AI persistent memory layer for VS Code Copilot"
  requires-python = ">=3.8"
  dependencies = []

  [project.scripts]
  engaku = "engaku.cli:main"
  ```
- [ ] 1.2 创建 `src/engaku/__init__.py`（空文件）
- [ ] 1.3 创建 `src/engaku/__main__.py`：
  ```python
  from engaku.cli import main
  main()
  ```
- [ ] 1.4 创建 `src/engaku/cli.py`：argparse 主路由，注册 6 个子命令（`init`、`inject`、`check-update`、`validate`、`log-read`、`stats`），每个调用对应的 `cmd_*.py` 模块
- [ ] 1.5 Verify: `pip install -e .` → `engaku --help` 输出 6 个子命令

---

### Task 2: `engaku inject`

最先实现，因为它最简单、最容易测试，且是 SessionStart Hook 的核心。

**Files:**
- Create: `src/engaku/cmd_inject.py`, `tests/test_inject.py`

- [ ] 2.1 实现 `cmd_inject.py`：
  - 读取 `.ai/rules.md` 和 `.ai/overview.md`
  - 若文件不存在，输出空 `additionalContext`
  - JSON 输出到 stdout：`{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}`
- [ ] 2.2 写测试 `tests/test_inject.py`：
  - 测试 1：两个文件都存在 → 输出包含两者内容
  - 测试 2：只有 rules.md → 只输出 rules 内容
  - 测试 3：两个文件都不存在 → 输出空 additionalContext
  - 测试 4：输出是合法 JSON
- [ ] 2.3 Verify: `cd /tmp/test-repo && mkdir -p .ai && echo "# Rules" > .ai/rules.md && engaku inject` → 输出合法 JSON
- [ ] 2.4 Verify: `python -m pytest tests/test_inject.py -v`

---

### Task 3: `engaku validate`

第二个实现，因为 `check-update` 依赖它的校验逻辑。

**Files:**
- Create: `src/engaku/cmd_validate.py`, `tests/test_validate.py`

- [ ] 3.1 实现 `cmd_validate.py`：
  - 默认扫描 `.ai/modules/*.md` 全部文件
  - `--recent` 参数：只检查最近 10 分钟内修改的文件（用 `os.path.getmtime`）
  - 校验规则：
    - 正文 ≥ 50 字（中文算字，英文算词 → 简化为 `len(content) >= 50`  字符数）
    - 包含 `## 概览` 标题
    - 不含禁用词：`更新了业务逻辑`、`修改了代码`、`进行了优化`
    - 文件总字符数 ≤ 300 字（中文字符 + 英文词）
  - 校验通过：exit 0
  - 校验失败：exit 2，stderr 输出每个文件的具体违规内容
- [ ] 3.2 写测试 `tests/test_validate.py`：
  - 测试 1：合格文件 → exit 0
  - 测试 2：缺少 `## 概览` → exit 2
  - 测试 3：内容 < 50 字 → exit 2
  - 测试 4：含禁用词 → exit 2
  - 测试 5：超 300 字 → exit 2
  - 测试 6：`--recent` 跳过旧文件
- [ ] 3.3 Verify: `python -m pytest tests/test_validate.py -v`

---

### Task 4: `engaku check-update`

**Files:**
- Create: `src/engaku/cmd_check_update.py`, `tests/test_check_update.py`

- [ ] 4.1 实现 `cmd_check_update.py`：
  - 从 stdin 读取 JSON（VS Code Hook 输入）
  - 检查 `stop_hook_active`：为 `true` 时 exit 0，直接返回
  - 执行 `git diff --name-only HEAD`（未 commit 的变更列表）
  - 过滤出 `.ai/` 外的代码文件变更（忽略 `.md`、`.json`、`.gitignore` 等配置文件）
  - 若有代码变更：检查 `.ai/modules/` 下是否有文件在最近 10 分钟内被修改
  - 若有变更但知识未更新：exit 2，stderr 输出提示消息
  - 若无变更或已更新：exit 0
- [ ] 4.2 写测试 `tests/test_check_update.py`：
  - 测试 1：`stop_hook_active: true` → exit 0
  - 测试 2：有代码变更且 modules 已更新 → exit 0
  - 测试 3：有代码变更但 modules 未更新 → exit 2
  - 测试 4：无代码变更 → exit 0
- [ ] 4.3 Verify: `python -m pytest tests/test_check_update.py -v`

---

### Task 5: `engaku log-read`

**Files:**
- Create: `src/engaku/cmd_log_read.py`, `tests/test_log_read.py`

- [ ] 5.1 实现 `cmd_log_read.py`：
  - 从 stdin 读取 JSON（PostToolUse Hook 输入，含 `tool_input`）
  - 从命令行参数或 stdin JSON 中提取文件路径
  - 判断路径是否在 `.ai/` 下
  - 若是：追加一行到 `.ai/access.log`，格式 `{ISO8601}\t{relative_path}\t{session_id}`
  - session_id 从 stdin JSON 的 `sessionId` 字段获取
  - exit 0（log-read 永远不阻断）
- [ ] 5.2 写测试 `tests/test_log_read.py`：
  - 测试 1：读取 `.ai/modules/auth.md` → access.log 追加一行
  - 测试 2：读取 `src/main.py` → 不写入 access.log
  - 测试 3：access.log 不存在时自动创建
- [ ] 5.3 Verify: `python -m pytest tests/test_log_read.py -v`

---

### Task 6: `engaku init`

**Files:**
- Create: `src/engaku/cmd_init.py`, `src/engaku/templates/*`（全部模板文件）, `tests/test_init.py`

- [ ] 6.1 创建模板文件（`src/engaku/templates/`）：
  - `rules.md`：带分类骨架（代码风格 / 项目约束 / 禁忌）
  - `overview.md`：带占位符（项目名 / 语言 / 框架 / 目录结构）
  - `dev.agent.md`：从 design.md 复制
  - `knowledge-keeper.agent.md`：从 design.md 复制
  - `planner.agent.md`：从 design.md 复制
  - `copilot-instructions.md`：引导 Copilot 使用 `.ai/` 知识库
  - `session.json`：SessionStart Hook
  - `knowledge-check.json`：Stop Hook
  - `access-log.json`：PostToolUse Hook
- [ ] 6.2 实现 `cmd_init.py`：
  - 检查当前目录是否是 git repo（`git rev-parse --git-dir`）
  - 若不是 git repo：报错退出
  - 创建 `.ai/` 目录结构（`rules.md`、`overview.md`、`modules/.gitkeep`、`decisions/.gitkeep`、`tasks/.gitkeep`）
  - 创建 `.github/agents/` 目录 + 3 个 agent 文件
  - 创建 `.github/hooks/` 目录 + 3 个 hook 文件
  - 创建 `.github/copilot-instructions.md`
  - 已存在的文件：**跳过，不覆盖**，打印 `[skip] .ai/rules.md already exists`
  - 新创建的文件：打印 `[create] .ai/rules.md`
- [ ] 6.3 写测试 `tests/test_init.py`：
  - 测试 1：空 git repo → 生成全部文件
  - 测试 2：已有 `.ai/rules.md` → 跳过不覆盖
  - 测试 3：非 git repo → 报错退出
- [ ] 6.4 Verify: `cd /tmp && mkdir test-init && cd test-init && git init && engaku init` → 验证目录结构
- [ ] 6.5 Verify: `python -m pytest tests/test_init.py -v`

---

### Task 7: `engaku stats`（MVP 简化版）

**Files:**
- Create: `src/engaku/cmd_stats.py`

- [ ] 7.1 实现 `cmd_stats.py`（MVP 简化版，只做能自动算的指标）：
  - **知识覆盖率**：列出 `src/` 或项目根目录下的一级子目录作为"模块"候选，比较 `.ai/modules/` 下已有文件
  - **知识时效性**：对每个 `.ai/modules/*.md`，用 `git log -1 --format=%ct` 取最后修改时间，标记超过 7 天未更新的
  - **access.log 统计**：读取 `.ai/access.log`，输出总读取次数 / 唯一 session 数 / 按文件分布
  - 输出格式：纯文本报表，打印到 stdout
- [ ] 7.2 Verify: 在一个有 `.ai/` 目录的 repo 中运行 `engaku stats` → 输出可读报表

---

### Task 8: 模板文件内容

**Files:**
- Create: `src/engaku/templates/` 下全部模板

- [ ] 8.1 `templates/rules.md`：
  ```markdown
  # 项目规则

  ## 代码风格
  <!-- 在此添加代码风格约束 -->

  ## 项目约束
  <!-- 在此添加项目约束 -->

  ## 禁忌
  <!-- 在此添加禁止做的事 -->
  ```
- [ ] 8.2 `templates/overview.md`：
  ```markdown
  # 项目概览

  ## 概览
  <!-- 项目名称、技术栈、核心功能 -->

  ## 目录结构
  <!-- 关键目录及其职责 -->

  ## 核心模块
  <!-- 模块列表及一句话描述 -->
  ```
- [ ] 8.3 `templates/copilot-instructions.md`：
  ```markdown
  # Copilot 使用指引

  本项目使用 `.ai/` 目录管理项目知识。

  ## 规则
  - 开发时遵循 `.ai/rules.md` 中的所有约束
  - 完成任务后，调用 knowledge-keeper subagent 更新 `.ai/modules/` 下对应模块的知识文件
  - 知识文件格式：≤300字，覆盖式更新，必须包含 `## 概览` 标题，禁止空话

  ## 知识结构
  - `.ai/rules.md`：项目规则（每次对话自动注入）
  - `.ai/overview.md`：项目概览（每次对话自动注入）
  - `.ai/modules/*.md`：模块知识（按需读取）
  - `.ai/decisions/*.md`：决策记录（按需读取）
  - `.ai/tasks/*.md`：任务计划（按需读取）
  ```
- [ ] 8.4 3 个 agent 模板文件：从 design.md 中的定义直接复制
- [ ] 8.5 3 个 hook 模板文件：从 design.md 中的 JSON 直接复制
- [ ] 8.6 Verify: `python -c "from importlib.resources import files; print(list(files('engaku.templates')))"` → 列出全部模板

---

### Task 9: 端到端验证

- [ ] 9.1 卸载本地开发版：`pip uninstall engaku`
- [ ] 9.2 从 git 安装：`pip install git+https://github.com/me/engaku`
- [ ] 9.3 创建测试 repo：
  ```bash
  cd /tmp && mkdir e2e-test && cd e2e-test && git init
  ```
- [ ] 9.4 运行 `engaku init` → 检查生成的全部文件
- [ ] 9.5 手写一个模块知识文件测试 `validate`：
  ```bash
  echo "## 概览\n\n这是 auth 模块，负责用户认证，包括 JWT token 生成、验证、刷新等功能。" > .ai/modules/auth.md
  engaku validate
  # 预期 exit 0
  ```
- [ ] 9.6 测试 `inject`：
  ```bash
  engaku inject
  # 预期输出 JSON，含 rules.md + overview.md 的内容
  ```
- [ ] 9.7 测试 `check-update`：
  ```bash
  echo '{"stop_hook_active": false}' | engaku check-update
  # 在没有代码变更时，预期 exit 0
  ```
- [ ] 9.8 打开 VS Code，在该 repo 中启动新的 Copilot agent 会话 → 确认 SessionStart Hook 注入了 rules + overview 内容
- [ ] 9.9 用 @dev agent 执行一个小任务 → 确认 Stop Hook 在会话结束时触发 `check-update`
- [ ] 9.10 在 Windows 3.8.4 环境中重复 9.2-9.7（验证跨平台兼容性）

---

### Task 10: 在真实项目部署、开始两周验证

- [ ] 10.1 选择一个活跃开发中的真实项目
- [ ] 10.2 在该项目中运行 `engaku init`
- [ ] 10.3 手写 3-5 个核心模块的种子知识文件（`.ai/modules/`）
- [ ] 10.4 填写 `.ai/rules.md` 和 `.ai/overview.md` 的实际内容
- [ ] 10.5 提交初始知识文件到 git
- [ ] 10.6 开始正常开发，每次会话后填写 `.ai/session-log.md`
- [ ] 10.7 两周后运行 `engaku stats`，统计 session-log.md，对照判定标准评估

---

## Scope Boundaries

**In scope:**
- 6 个 CLI 子命令（`init`、`inject`、`check-update`、`validate`、`log-read`、`stats`）
- init 生成的全部模板文件（3 agents + 3 hooks + 3 knowledge 文件 + copilot-instructions）
- 单元测试
- 端到端验证（macOS + Windows 3.8.4）

**Out of scope（不做）:**
- DSL 工作流引擎
- `engaku scan`（存量代码扫描）
- PyPI 发布
- CI/CD pipeline
- 向量搜索 / 外部 AI 调用
- Jira/Confluence 集成
