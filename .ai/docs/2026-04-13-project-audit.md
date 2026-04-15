# Engaku 项目现状评估
related_task: none

## 总体判断

**Engaku 尚未达到"开箱即用"水平。** 核心骨架已经搭好（init、inject、agent 模板、hook 管线、task lifecycle），但存在若干断裂点——已删除命令仍被引用、README 与代码不一致、模板对新项目来说不够自描述、缺少端到端验证。一个全新用户在自己的项目里执行 `pip install` → `engaku init` → 打开 VS Code 后，会立即遇到报错或困惑。

---

## 一、可以工作的部分（✅）

| 能力 | 状态 | 评价 |
|------|------|------|
| `engaku init` | ✅ | 正确生成 `.ai/`、`.github/agents/`、`.github/instructions/`、`.github/skills/`、`.vscode/settings.json`。不覆盖已有文件。 |
| `engaku inject` (SessionStart / PreCompact) | ✅ | 正确输出 `hookSpecificOutput` 或 `systemMessage`，包含 overview + active-task。 |
| `engaku prompt-check` | ✅ | 关键词匹配中英文，正确输出 systemMessage。始终 exit 0。 |
| `engaku task-review` | ✅ | 扫描 `.ai/tasks/`，检测 all-checked plan，输出 handoff 提醒。 |
| `engaku log-read` | ✅ | PostToolUse 钩子，记录 `.ai/` 文件访问日志。 |
| `engaku apply` | ✅ | 正确将 `engaku.json` model 配置推送到 agent frontmatter。 |
| Agent 模板（dev/planner/reviewer/scanner） | ✅ | 角色清晰、权限边界明确、handoff 机制可用。 |
| Skill 模板（3 个） | ✅ | systematic-debugging 和 verification-before-completion 质量好，可直接使用。 |
| 测试套件 | ✅ | 86 个测试全部通过，覆盖所有现有命令。 |
| 零依赖 / Python ≥3.8 | ✅ | 严格遵守。 |

## 二、明确的问题（❌）

### 2.1 幽灵命令：`subagent-start` 已删除但仍被引用

V4 明确删除了 `cmd_subagent_start.py`，但以下位置仍引用它：
- **`src/engaku/templates/agents/dev.agent.md`** — SubagentStart hook: `engaku subagent-start`
- **`.github/agents/dev.agent.md`** — 同上（live 版本）
- **`README.md`** — subcommand 表和 "How it works" 段落都提到了 `subagent-start`

**后果：** 任何使用 dev agent 的项目，每次 SubagentStart 事件都会报 `command not found` 错误。这是一个 **P0 级阻断问题**。

### 2.2 README 文档失真

README 列出了 9 个子命令，其中 3 个不存在于代码中：
- `subagent-start` — 已删除
- `validate` — 已删除
- `stats` — 已删除

`inject` 的 help text 说 "Output rules.md + overview.md" 但 `.ai/rules.md` 已经被 V4 删除，inject 实际只读 `overview.md`。

### 2.3 残留的 V3 常量

`constants.py` 仍包含 V3 时代的遗留常量：
- `FORBIDDEN_PHRASES`、`MIN_CHARS`、`MAX_CHARS`、`REQUIRED_HEADING` — 这些是 module-knowledge validation 的参数，现在没有任何代码使用它们
- `STALE_DAYS` — stats 的参数，stats 已删除
- `load_config` 仍然解析 `max_chars` 和 `check_update.uncovered_action`，但 `check-update` 已经是一个空壳

这不会导致运行时错误，但增加维护负担和代码理解难度。

### 2.4 `check-update` 是一个空壳

`cmd_check_update.py` 的 `run()` 调用 `_get_changed_files()` 但**完全不用返回值**，然后直接 return 0。这个命令实际上什么都不做。

dev agent 的 Stop hook 仍然调用它（每次响应后都会执行），白白消耗一次进程启动和 transcript 解析。

### 2.5 模板 overview.md 是空壳

`src/engaku/templates/ai/overview.md` 只有 HTML 注释占位符，没有任何实际内容。`engaku inject` 注入的 `<project-context>` 会是空的。新用户不会意识到需要手动填写它，因为没有任何提示或引导。

### 2.6 `engaku.json` 模板有无用配置

模板中的 `engaku.json` 包含 `max_chars`、`check_update` 配置，但这些配置在 V4 中已经没有消费者。新项目初始化后会看到一个有误导性的配置文件。

## 三、缺失的关键能力（⚠️）

### 3.1 没有 `engaku update` / 升级机制

用户 `pip install` 新版后，已有项目的 `.github/` 模板不会自动更新。没有 diff、没有 patch、没有 `--force` 选项。这对一个 "工具箱" 来说是基本需求。

### 3.2 没有 `--dry-run` 或 `--verbose`

`engaku init` 没有任何 dry-run 模式。用户无法预览将会创建什么文件。

### 3.3 scanner agent 没有对应的 hook/CLI 命令

scanner 是一个纯提示词 agent（"扫描代码库，提议 .instructions.md 分组"），它的工作流完全依赖用户手动触发和手动操作。这是设计意图，但与 "开箱即用" 的定位有距离——新项目 init 后的 `.github/instructions/` 只有 3 个 engaku 自身的模板，对目标项目毫无价值。

### 3.4 没有 uninstall/clean 命令

没有办法一键移除 engaku 生成的所有文件。

### 3.5 没有版本管理

`pyproject.toml` version 仍是 `0.1.0`，没有 changelog。

## 四、小问题 / 打磨项

1. **CLI help text 过时** — `inject` 说 "Output rules.md + overview.md"，实际只有 overview + active-task
2. **`.github/prompts/` 空目录** — 已创建但没有内容，也没被 init 管理
3. **`engaku.json` 的 `agents` 默认为空对象** — 新用户不知道怎么填
4. **`frontend-design` skill** 不是通用技能，对大多数后端项目没意义，不该作为默认 bundle
5. **init 不检查 engaku 是否已安装** — 如果用户在 PATH 中没有 engaku，hook 会在运行时静默失败
6. **没有 `.gitignore` 建议** — `.ai/access.log` 应该被 ignore

## 五、总结：离"开箱即用"还有多远

| 维度 | 评分（1-5） | 备注 |
|------|------------|------|
| 安装体验 | 3 | `pip install git+` 可行，但没有 PyPI |
| Init 体验 | 3.5 | 文件生成正确，但模板内容空洞 |
| Hook 管线 | 2 | subagent-start 幽灵引用会直接报错 |
| 文档准确性 | 2 | README 与代码严重脱节 |
| 代码整洁度 | 3 | 有残留常量和空壳命令 |
| Agent 协作 | 4 | dev/planner/reviewer 三角色分工明确 |
| 新项目接入 | 2.5 | 需要手动填写 overview.md、instructions、engaku.json |
| 升级/维护 | 1 | 没有 update 机制 |

**综合评分：约 2.6 / 5。**

最紧急的 3 件事（按优先级）：
1. **修复 subagent-start 幽灵引用** — 从 dev.agent.md 模板和 live 版本中移除
2. **同步 README** — 删除已移除命令的描述，更新 inject 的说明
3. **清理死代码** — 移除 constants.py 中无消费者的常量，让 check-update 做有意义的事或移除它
