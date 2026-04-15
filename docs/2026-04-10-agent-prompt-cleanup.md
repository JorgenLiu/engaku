---
plan_id: 2026-04-10-agent-prompt-cleanup
title: Agent prompt 精简 + template rules.md 预填 + module quality 硬规则
status: done
created: 2026-04-10
---

## Background

Agent prompt 存在跨 agent 重复内容（module file format 代码块、forbidden phrases 列表），
浪费上下文窗口。template rules.md 几乎为空，新项目 init 后 dev agent 缺少 engaku 调度流
约束。knowledge-keeper 不要求先读源码就写知识文件，导致事实性错误。

## Design

- rules.md 定位为"仓库级约束 + engaku 调度流规则"，注入给 dev agent。
- subagent prompt 中的重复规则用精简一句话替代（validate 兜底）。
- knowledge-keeper 加"先读源码"硬规则。
- scanner 改为包含测试文件。
- 本项目 live rules.md 清理过时条目。

## Tasks

每个 task 都需要同时修改 template 版和 live 版（如果都存在的话）。

- [x] 1. **Template rules.md 预填初始规则**
  - 文件：`src/engaku/templates/ai/rules.md`
  - 替换整个文件内容为：
    ```markdown
    # Project Rules

    ## Code Style
    <!-- Add code style constraints here. Examples: -->
    <!-- - "Always use 2-space indentation in TypeScript." -->
    <!-- - "Never use inline styles — use Tailwind utility classes." -->

    ## Project Constraints
    - When updating any agent or hook file, always update BOTH the live version
      (`.github/`) AND the template version (`src/engaku/templates/`) in the same operation.
    - Module knowledge files must have `paths:` frontmatter listing covered source paths.

    ## Forbidden
    - Do not overwrite existing `.ai/` or `.github/` files during `engaku init`.
    - Do not let any hook command exit non-zero unless it is intentionally blocking.
    - Do not add agent-specific rules to `.github/copilot-instructions.md` — that file
      is global. Agent-specific behaviour belongs in the agent's own `.agent.md` file.

    ## Agent Configuration
    <!-- Model assignments live in .ai/engaku.json. Run `engaku apply` to push them. -->
    - MAX_CHARS for module knowledge body: 1500 (frontmatter excluded).
    - Always call `@scanner-update` before `@knowledge-keeper`. Assign unclaimed files
      first, then update module knowledge.
    ```
  - 注意：MAX_CHARS 初始值 1500（与 Python constants.py 一致），后续由 `engaku apply` 根据 engaku.json 覆写。
  - 验证：`cat src/engaku/templates/ai/rules.md` 内容正确。

- [x] 2. **Live rules.md 清理过时条目**
  - 文件：`.ai/rules.md`
  - 删除第 20 行：`- check-update Stop hook is agent-scoped to 'dev' only — brainstorming/planner agents must not trigger it.`
  - 修改第 9 行：`Knowledge files must be ≤1500 characters` → `Knowledge files must be ≤1600 characters`（与第 18 行 canonical value 对齐）
  - 在 Agent Configuration 末尾追加：`- Always call @scanner-update before @knowledge-keeper. Assign unclaimed files first, then update module knowledge.`
  - 验证：确认 rules.md 中没有"1500"（除非 MAX_CHARS 行本身），没有"check-update Stop hook is agent-scoped"。

- [x] 3. **dev.agent.md 精简**（template + live 各一份）
  - 文件：`src/engaku/templates/agents/dev.agent.md`、`.github/agents/dev.agent.md`
  - 删除"Before starting work"一节（与 copilot-instructions.md 重复）。
  - 删除"Stop hook guidance"一节（5 行；Stop hook 自身 systemMessage 已足够清晰）。
  - 精简 step 3 "Update project-level files"，从 4 个 bullet 改为一句话。
  - 目标 body（frontmatter 下方）：
    ```markdown
    You have two responsibilities. Both are mandatory — a task is not complete until both are done.

    1. **Execute the user's development task.**
    2. **Update project knowledge for any source files you changed.**

    **Before responding that work is done** (applies to every session where you edited source files):

    1. **Assign unclaimed files.** For each new source file created this session that is not listed in any module's `paths:` frontmatter:
       - **Decide** whether it belongs to an existing module or needs a new one.
       - Call `scanner-update` with your decision stated explicitly (e.g. "assign `src/foo.py` to the scaffolding module" or "create a new module named `auth` covering `src/foo.py`").
       - If you are unsure, ask the user before calling.
    2. **Update module knowledge.** Call `knowledge-keeper` once per affected module — do NOT batch multiple modules into a single call. Pass the module name and a brief description of what changed.
    3. **Update project-level files** (`.ai/overview.md`, `.ai/rules.md`, `.ai/decisions/`, `.ai/tasks/`) if the changes affect architecture, constraints, or an in-progress plan.
    ```
  - 验证：template 和 live body 一致（忽略 `model:` 行）。

- [x] 4. **knowledge-keeper.agent.md 加硬规则 + 精简**（template + live 各一份）
  - 文件：`src/engaku/templates/agents/knowledge-keeper.agent.md`、`.github/agents/knowledge-keeper.agent.md`
  - 在 Scope 之后、Rules 之前，新增一条：
    > Before writing a module overview, read every source file listed in the module's `paths:` frontmatter. Do NOT describe behavior you have not verified in the code.
  - 删除 "Module file format" 代码块（6 行）。
  - 将 forbidden phrases 和 time-relative phrases 两段合并为一句：
    > Use concrete, specific, timeless language. `engaku validate` will reject vague or time-relative descriptions.
  - 删除 "Frontmatter with paths: ... is required"（scanner-update 负责）。
  - 目标 body：
    ```markdown
    Analyze the incoming task description and code changes, then update the specified module knowledge file.

    **Scope — you may ONLY edit:**
    - The `## Overview` body of existing `.ai/modules/*.md` files. Do NOT create new module files — that is the scanner agent's job.
    - Do NOT modify `paths:` frontmatter — adding or removing paths is scanner-update's exclusive responsibility.

    **Do NOT touch** `.ai/overview.md`, `.ai/rules.md`, `.ai/decisions/`, or `.ai/tasks/`.

    Before writing a module overview, read every source file listed in the module's `paths:` frontmatter. Do NOT describe behavior you have not verified in the code.

    **Rules:**
    - Must include `## Overview` heading. Body ≤ MAX_CHARS (see `.ai/rules.md`). Overwrite, do not append.
    - Format: YAML frontmatter with `paths:` list, then `## Overview` heading, then body.
    - Use concrete, specific, timeless language. `engaku validate` will reject vague or time-relative descriptions.
    ```
  - 验证：template 和 live body 一致（忽略 `model:` 行）。

- [x] 5. **scanner.agent.md 包含测试文件 + 精简**（template + live 各一份）
  - 文件：`src/engaku/templates/agents/scanner.agent.md`、`.github/agents/scanner.agent.md`
  - Step 1 改为：`**Discover source files** — list source files and their corresponding test files (e.g. src/**/*.py and tests/**/*.py, excluding __init__.py, __main__.py).`
  - 删除 step 2 中的示例表格（agent 知道怎么做表格），保留表格列名说明。
  - 删除 "Module file format" 代码块（6 行），改为一句话。
  - 目标 body：
    ```markdown
    Scan this repository and build or refresh the `.ai/modules/` knowledge index.

    **Workflow:**

    1. **Discover source files** — list source files and their corresponding test files (e.g. `src/**/*.py` and `tests/**/*.py`, excluding `__init__.py`, `__main__.py`).
    2. **Propose logical groupings** — cluster files into 3–6 cohesive modules by responsibility (NOT one file = one module). Present as a table with columns: Module name, Files covered, Rationale. Wait for user approval before writing any files.
    3. **Create module files** — for each approved group, create `.ai/modules/{name}.md` with `paths:` frontmatter, `## Overview` heading, and one concrete paragraph. Body ≤ MAX_CHARS (see `.ai/rules.md`).
    4. **Update overview.md** — patch or initialise the `## Overview` and `## Directory Structure` sections. Do NOT rewrite the whole file.

    **Rules:**
    - Do NOT generate or modify `.ai/rules.md`.
    - Do NOT create module files before the user approves groupings.
    - Format: YAML frontmatter with `paths:` list, then `## Overview` heading, then body.
    - Use concrete, specific language. `engaku validate` will reject vague descriptions.
    ```
  - 验证：template 和 live body 一致（忽略 `model:` 行）。

- [x] 6. **scanner-update.agent.md 精简**（template + live 各一份）
  - 文件：`src/engaku/templates/agents/scanner-update.agent.md`、`.github/agents/scanner-update.agent.md`
  - 删除 "Module file format" 相关的格式要求（代码块已隐含在 workflow 步骤中）。
  - 合并 forbidden phrases 为一句话引用。
  - 将 3 条 "Body ≤ MAX_CHARS" 引用合并为 workflow 步骤中的一句。
  - 目标 body：
    ```markdown
    Execute the module assignment decision made by the dev agent (or user). You will receive unclaimed source files along with an explicit instruction: assign each file to a named existing module, or create a new module with a given name.

    **You are an executor, not a decision-maker.**

    **Workflow:**

    1. **Read the dev agent's instruction** — it will specify, for each unclaimed file, either:
       - "assign to module X" — add the file path to the module's `paths:` frontmatter and append a concrete sentence to the `## Overview`.
       - "create new module named X covering these files" — create `.ai/modules/{name}.md` with `paths:` frontmatter, `## Overview` heading, and one concrete paragraph.
    2. Body ≤ MAX_CHARS (see `.ai/rules.md`). Format: YAML frontmatter with `paths:` list, then `## Overview`, then body.
    3. **If no explicit decision was provided** for a file — do NOT guess. Ask the dev agent for clarification.

    **Rules:**
    - Do NOT make structural decisions yourself.
    - Do NOT touch `.ai/rules.md`, `.ai/decisions/`, or `.ai/tasks/`.
    - Only process the files explicitly listed. Do not scan the whole repo.
    - Use concrete, specific, timeless language. `engaku validate` will reject vague descriptions.
    - After completing, report which files were assigned and to which modules.
    ```
  - 验证：template 和 live body 一致（忽略 `model:` 行）。

- [x] 7. **Live overview.md 修正**
  - 文件：`.ai/overview.md`
  - 修改 hook 列表，补充 `PostToolUse`：`Agent hooks now cover SessionStart, PreCompact, UserPromptSubmit, Stop, SubagentStart, and PostToolUse.`
  - 修改 `.github/` 描述：`Agent definitions for this repo` → 删去 "hook"（hooks 目录已不存在）。
  - 验证：`cat .ai/overview.md` 内容正确。

- [x] 8. **Live module files 修正**
  - `quality.md`：删除 "Hard-block conditions (unclaimed stale modules) produce non-zero exits"，改为准确描述 JSON decision block 机制。
  - `scaffolding.md`：删除 "it verifies the hooks directory exists" 过时描述。
  - 验证：`engaku validate` 全部 `[OK]`。

- [x] 9. **运行全套测试**
  - `python -m unittest discover -s tests`
  - `engaku validate`
  - 确认全部通过。
