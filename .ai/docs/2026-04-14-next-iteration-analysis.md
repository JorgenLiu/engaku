# Engaku 下一步迭代分析
related_task: none
created: 2026-04-14

## 研究来源

- 项目现状：全量代码审阅 + 80 个测试全通过 + `.ai/docs/2026-04-13-project-audit.md`
- VS Code Copilot 最新文档（2026-04-08 更新）：hooks、agent-plugins、agent-skills、customization overview
- Claude Code 仓库（github.com/anthropics/claude-code）：插件系统、CLAUDE.md + auto memory 双重记忆、`.claude/rules/` 路径规则、hookify 插件

---

## 一、当前项目健康度

| 维度 | 状态 | 说明 |
|------|------|------|
| 核心功能 | ✅ | init、inject、prompt-check、task-review、log-read、apply 全部工作 |
| 测试 | ✅ | 80 tests passing，覆盖所有命令 |
| V4 清理 | ✅ | post-v4 cleanup 已完成，无幽灵引用 |
| 代码卫生 | ✅ | 零依赖、Python ≥3.8、constants 已清理 |
| `check-update` | ⚠️ | **空壳命令**：读 hook_input → 检查 stop_hook_active → return 0。每次 Stop 事件白白启动一次 Python 进程 |
| 可分发性 | ⚠️ | `pip install git+...` 可用但非主流；没有升级路径 |
| 文档 | ⚠️ | README 已同步但偏简略；没有面向新用户的 Quick Start Guide |

**总结**：骨架完整，核心管线稳定。最大的问题是 `check-update` 空转 和 缺少面向外部用户的价值主张。

---

## 二、VS Code Copilot 新特性（2026-04 文档）

### 2.1 Agent Plugins（Preview）— 最重要的新发现

VS Code 现在有一个完整的 **插件系统**：

```
my-plugin/
  plugin.json              # 元数据
  skills/                  # 技能
  agents/                  # 自定义 agent
  hooks/hooks.json         # 生命周期钩子
  .mcp.json                # MCP 服务器
  commands/                # 斜杠命令
```

- 可从 marketplace 安装（`@agentPlugins` 搜索）
- 可从 Git URL 直接安装（`Chat: Install Plugin From Source`）
- 可配置推荐插件让团队自动发现
- 兼容 Claude Code 插件格式（`.claude-plugin/plugin.json`）

**对 engaku 的意义**：engaku 目前是一个需要 `pip install` 的 Python CLI，然后由 agent-scoped hooks 调用。如果转型为 Agent Plugin，可以：
- 一键安装、无需 Python 环境
- Hooks 用 shell 脚本替代 Python CLI
- Skills/agents/hooks 原生打包
- 但需要放弃 Python 实现（hooks 只能是 shell commands）

### 2.2 `.github/hooks/*.json` — 集中式 Hook 配置

VS Code 现在从 `.github/hooks/*.json` 发现 hooks（默认位置之一）。当前 engaku 使用 agent-scoped hooks（写在 `.agent.md` frontmatter 里），这仍然有效且更精细，但集中式配置是更主流的做法。

### 2.3 八个生命周期事件

VS Code 现在支持 8 个 hook events：

| 事件 | engaku 是否使用 | 备注 |
|------|----------------|------|
| SessionStart | ✅ inject | 注入 project context |
| UserPromptSubmit | ✅ prompt-check | 关键词检测 |
| PreToolUse | ❌ | **未使用** — 可用于安全策略 |
| PostToolUse | ✅ log-read | 记录 .ai/ 文件访问 |
| PreCompact | ✅ inject | 注入 context |
| SubagentStart | ❌ | V4 删除后未替换 |
| SubagentStop | ❌ | 未使用 |
| Stop | ✅ check-update + task-review | check-update 是空壳 |

**机会**：`PreToolUse` 和 `SubagentStart`/`SubagentStop` 完全未利用。

### 2.4 `/create-*` 命令

VS Code 内置了 `/create-hook`、`/create-skill`、`/create-agent`、`/create-instruction` AI 生成命令。这部分取代了 engaku 的 `scanner` agent 的职责。

### 2.5 Chat Customizations Editor

可视化管理所有自定义配置的 UI。engaku 生成的文件会自动出现在这里。

---

## 三、Claude Code 可借鉴之处

### 3.1 双重记忆系统（CLAUDE.md + Auto Memory）

| | CLAUDE.md | Auto Memory |
|---|-----------|-------------|
| 谁写 | 用户 | AI |
| 内容 | 规则和指令 | 学习和发现 |
| 作用域 | 项目/用户/组织 | 每个工作树 |
| 加载 | 每次会话 | 首 200 行/25KB |

**engaku 的对应**：
- CLAUDE.md ≈ `.github/copilot-instructions.md` + `.ai/overview.md`
- Auto Memory ≈ **无对应**

**启示**：engaku 的 `inject` hook 在 SessionStart 注入 `.ai/overview.md`，但这个文件是静态的、需要人工维护的。可以考虑：
- 让 Stop hook 自动提取本次会话的关键决策/发现，追加到 `.ai/overview.md` 或一个新的 `.ai/learnings.md`
- 但这需要分析 transcript，复杂度高

### 3.2 `.claude/rules/` 路径规则

Claude Code 的 `.claude/rules/` 支持 YAML frontmatter `paths:` 字段做路径作用域。VS Code 的 `.instructions.md` 用 `applyTo:` 做同样的事。**两者已经功能等价**，engaku 的 scanner agent 和 `init` 生成的 `.github/instructions/` 已经覆盖了这个能力。

### 3.3 Hookify 插件

Claude Code 的 `hookify` 插件允许用 markdown 描述规则，自动生成 hook 脚本来拦截不良行为。这是一个有趣的模式：**声明式规则 → 自动化强制执行**。

engaku 可以学习这个思路：让用户在 `.ai/` 里写声明式策略（比如 "不允许直接修改 production 分支"），由 engaku 生成对应的 `PreToolUse` hook。

### 3.4 Claude Code 的 `/init` 交互式流程

Claude Code 的 `/init`（特别是 `CLAUDE_CODE_NEW_INIT=1` 模式）：
1. 用 subagent 探索代码库
2. 通过追问收集信息
3. 展示可审阅的提案
4. 用户确认后写文件

engaku 的 `init` 是静态模板复制，没有代码库分析能力。但这更像是交给 `scanner` agent 的职责。

### 3.5 插件架构

Claude Code 的插件标准结构值得参考：
- `plugin.json` 元数据
- 独立的 `commands/`、`agents/`、`skills/`、`hooks/` 目录
- VS Code 已经兼容这个格式

---

## 四、可选的迭代方向（按可行性和影响排序）

### 方向 A：渐进改良（低风险，中等收益）

保持现有 Python CLI 架构，修补已知问题，增加实用功能。

| 任务 | 描述 | 工作量 |
|------|------|--------|
| A1. 删除或重新利用 `check-update` | 当前是空壳。选项：(a) 彻底删除，从 dev agent Stop hook 移除；(b) 赋予新功能，比如检查 `.ai/overview.md` 是否为空并提醒填写 | 小 |
| A2. 添加 `engaku update` | 对比当前模板和已安装文件的差异，提示用户更新。解决升级路径问题 | 中 |
| A3. 添加 `--dry-run` 到 `init` | 预览将创建的文件，不实际写入 | 小 |
| A4. 增强 `overview.md` 模板 | 提供有意义的 scaffold 而非空注释 | 小 |
| A5. 利用 PreToolUse hook | 添加 `engaku guard` 命令，在 PreToolUse 时检查安全策略（如阻止删除 `.ai/` 文件） | 中 |
| A6. 优化 `frontend-design` skill 为可选 | 从默认 bundle 中移除，或改为通用 `code-quality` skill | 小 |

### 方向 B：转型为 Agent Plugin（中等风险，高收益）

将 engaku 重构为 VS Code Agent Plugin 格式，使其可从 marketplace 一键安装。

**架构变化**：
```
engaku-plugin/
  .claude-plugin/
    plugin.json
  agents/
    dev.agent.md
    planner.agent.md
    reviewer.agent.md
    scanner.agent.md
  skills/
    systematic-debugging/SKILL.md
    verification-before-completion/SKILL.md
  hooks/
    hooks.json           # 定义所有 hook → shell 脚本
  scripts/
    inject.sh            # SessionStart/PreCompact
    prompt-check.sh      # UserPromptSubmit
    task-review.sh       # Stop
    log-read.sh          # PostToolUse
  .ai/                   # init 仍需要某种方式创建
```

**优势**：
- 不需要 Python 环境
- `Chat: Install Plugin From Source` → 输入 GitHub URL 即可安装
- 原生 VS Code 集成
- 兼容 Claude Code 插件生态

**挑战**：
- Hook 脚本只能是 shell 命令，不是 Python — 当前的 `inject`、`task-review` 需要解析 YAML frontmatter、扫描目录，用 shell 实现会很丑
- `init` 功能（创建 `.ai/` 目录结构）无法通过插件 hooks 实现，需要额外途径（比如 slash command）
- 需要放弃 Python 测试套件（80 个测试），或保持 Python 作为 hook 脚本的实现语言
- **混合方案**：插件格式 + hook 命令仍然调用 `engaku` CLI（需要 pip install），只是发现和注册通过插件机制

### 方向 C：生成 `.github/hooks/*.json`（低风险，中等收益）

在保持 Python CLI 的同时，让 `engaku init` 同时生成 `.github/hooks/engaku.json` 集中式 hook 配置。这样即使不用 agent-scoped hooks，标准 VS Code 也能发现和加载 engaku 的 hooks。

**好处**：
- 用户可以在 Chat Customizations Editor 里看到和管理 engaku 的 hooks
- 兼容非 engaku agents（用户自己定义的 agent 也能享受 inject、prompt-check 等功能）
- 与 agent-scoped hooks 共存

**实现**：`engaku init` 额外生成：
```json
// .github/hooks/engaku.json
{
  "hooks": {
    "SessionStart": [{"type": "command", "command": "engaku inject", "timeout": 5}],
    "PreCompact": [{"type": "command", "command": "engaku inject", "timeout": 5}],
    "UserPromptSubmit": [{"type": "command", "command": "engaku prompt-check", "timeout": 5}],
    "Stop": [{"type": "command", "command": "engaku task-review", "timeout": 5}],
    "PostToolUse": [{"type": "command", "command": "engaku log-read", "timeout": 5}]
  }
}
```

### 方向 D：添加声明式策略引擎（高风险，高收益）

受 Claude Code 的 hookify 启发，让用户在 `.ai/policies/` 里写声明式规则，engaku 在 `PreToolUse` 和 `Stop` 时自动执行。

例子：
```markdown
# .ai/policies/no-force-push.md
---
event: PreToolUse
tool: terminal
---
Block any command containing `git push --force` or `git push -f`.
Reason: Force push to shared branches is prohibited by team policy.
```

engaku 解析这些 markdown 策略文件，在 hook 事件时检查 tool_input 是否匹配，返回 `permissionDecision: "deny"`。

**这个方向过于超前**，建议等核心功能稳定后再考虑。

---

## 五、推荐的优先级

综合考虑投入产出比、用户痛点和项目阶段：

### 第一优先级（立即做）

1. **A1 — 处理 `check-update` 空壳**：要么删除、要么赋予新功能（如检查 overview.md 是否为空）。每次 Stop 都启动空进程是浪费。
2. **C — 生成 `.github/hooks/engaku.json`**：低成本高收益，让 engaku 的 hooks 对非 agent-scoped 场景也可用，且在 Chat Customizations Editor 里可见。

### 第二优先级（本周内）

3. **A2 — `engaku update`**：没有升级路径是面向外部用户的核心阻碍。
4. **A4 — 改善 overview.md scaffold**：新用户 init 后看到有引导性的模板，而不是空文件。

### 第三优先级（下次迭代）

5. **A5 — PreToolUse guard hook**：利用 VS Code 的 `UserPromptSubmit` 机制实现安全策略。
6. **B（调研） — Agent Plugin 可行性验证**：制作一个最小化 engaku 插件原型，验证 hook 脚本调用 Python CLI 的模式是否可行。如果可行，作为 V5 的核心方向。

### 暂不建议做

- **D — 声明式策略引擎**：过于复杂，等核心功能和分发问题解决后再考虑。
- **完全去 Python 化**：shell 脚本实现 frontmatter 解析和目录扫描太脆弱，不值得。

---

## 六、待讨论的关键问题

1. **`check-update` 的命运**：删除还是赋予新功能？如果赋予新功能，哪个方向？
   - 选项 a：检查 `.ai/overview.md` 是否为空，提醒用户填写
   - 选项 b：检查本次会话是否编辑了源码但没更新 `.ai/` 相关文件
   - 选项 c：彻底删除，减少 Stop hook 开销

2. **是否从 agent-scoped hooks 迁移到 `.github/hooks/*.json`**，还是两者共存？

3. **Agent Plugin 方向**：是否值得投入精力做可行性验证？还是继续以 `pip install` CLI 为主？

4. **分发策略**：PyPI 发布还是继续 `git+https://...`？是否需要 `engaku --version` 和版本管理？

5. **目标用户画像**：engaku 面向 engaku 开发者自用？还是面向外部团队？这决定了文档、分发、升级体验的投入。
