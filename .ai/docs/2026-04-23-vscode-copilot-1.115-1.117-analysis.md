# VS Code Copilot 1.115 – 1.117 — 对 Engaku 的影响分析

Related task: none yet (analysis only)
Date: 2026-04-23
Sources:
- [VS Code 1.115 release notes](https://code.visualstudio.com/updates/v1_115) (2026-04-08)
- [VS Code 1.116 release notes](https://code.visualstudio.com/updates/v1_116) (2026-04-15)
- [VS Code 1.117 release notes](https://code.visualstudio.com/updates/v1_117) (2026-04-22)

## TL;DR

近三个版本里，**只有 1.116 的两项更新**与 engaku 的核心定位（用 `.ai/` + agent customizations 给 Copilot 加持久记忆）直接相关：

1. **Chat Customizations 欢迎页 + "Customize Your Agent" 草拟器** — Microsoft 开始官方做我们做的事，需要重新审视差异化定位。
2. **Agent Debug Logs 持久化到磁盘** — 给 engaku 排查 hook / 注入失败提供了官方手段，可以写进 `troubleshoot` 文档或 reviewer agent。

其余都是体验/Enterprise/Insiders 配套，对 engaku 没有改造压力，但有几条值得记录为长期监控项。

---

## 一、直接相关（应当响应）

### 1.1 Customizations 欢迎页 + 自动草拟（1.116）

> "Creating customizations might be daunting at first, so you can now use the **Customize Your Agent** input on the welcome page to let VS Code draft customizations like **agents, skills, and instructions** based on a natural language description."

**含义**
- 官方第一次提供"一句话生成 agent / skill / instruction 文件"的入口。
- 这是 engaku `init` 工作的子集 —— 我们的核心价值不再是"帮你写出第一份 .agent.md"，而是：
  - 一套**互相协作**的 agent 集合（planner / coder / reviewer / scanner）；
  - 跨 agent 的**hooks 编排**（SessionStart / PreCompact / UserPromptSubmit / Stop）；
  - 任务文件 + 决策文件 + 文档的**生命周期**约定；
  - 失败记忆 (`lessons.instructions.md`) 与 MCP server 的开箱即用。

**建议**
- README / overview 里需要一段"engaku vs. VS Code Customize Your Agent"的定位说明，强调"协作 + 生命周期 + 记忆"而非单文件生成。
- 不要进入"engaku init 自动写 prompt"这种和官方草拟器重叠的方向。
- 可以考虑提供一条 `engaku doctor` / `engaku status` 提示用户：你已通过 engaku 安装的 customizations 有哪些，避免和欢迎页里的草拟件冲突。

### 1.2 Agent Debug Logs 写入磁盘（1.116）

> Setting `github.copilot.chat.agentDebugLog.fileLogging.enabled` — 历史会话日志现在持久化到本地，可在 Agent Debug Logs 面板查看。

**含义**
- 这正是我们调试 hook 是否触发、`PreCompact` / `UserPromptSubmit` 注入内容是否生效时最缺的工具。
- 我们目前 `troubleshoot` skill 已经在用 JSONL debug logs；新版本把"历史 session"也持久化了，可以排查"上一轮哪个 hook 没跑"。

**建议**
- 在 `.github/skills/troubleshoot/`（或 reviewer agent）里追加一条：当 hook 行为可疑时，先开启 `github.copilot.chat.agentDebugLog.fileLogging.enabled` 并查阅历史 session 日志。
- `engaku init` 不需要写这个 setting（属于用户偏好，不是 repo 配置）。
- 在 `lessons.instructions.md` 模板里可以加一句"hook 静默失败时优先看 Agent Debug Logs"。

---

## 二、间接相关（监控但不改）

### 2.1 VS Code Agents 伴随 App（1.115 引入，1.116/1.117 持续打磨）

> "Custom instructions, prompt files, **custom agents, MCP servers, hooks**, and plugins all work in the Agents app."

- 官方明确承诺：engaku 写入 `.github/` 与 `.vscode/mcp.json` 的产物会原封不动地被 Agents app 加载。
- 1.117 加入"sub-sessions"：在父 session 里 spin up 子 session 做并行研究/code review。和 engaku 的 planner / scanner 分工天然契合，未来可考虑在 planner agent 里引导用户："对于探索性子任务，可在 Agents app 里 spawn sub-session 跑 scanner"。

**建议**：暂不动代码；在 v1.x roadmap 里记一条"Agents app 兼容性验证"。

### 2.2 Background terminal notifications 默认开启（1.116）

> 1.116 之后 background 终端命令完成 / 需要输入会自动通知 agent，无需轮询 `get_terminal_output`。

- 与 engaku 自身没有直接关系（我们不是 hook 内部跑长命令的工具）。
- 但 coder/reviewer agent 在跑 `pytest` 等长命令时会受益。可以更新 coder agent 的 prompt：删除任何"记得轮询终端输出"的旧表述（如果存在）。

### 2.3 Foreground terminal 也支持 send_to_terminal / get_terminal_output（1.116）

- Tools 描述变化对 agent 没有破坏性影响，无需改动。

### 2.4 BYOK for Business / Enterprise（1.117）

- 企业用户可能用自带 key 的模型代替 `engaku.json` 里指定的 GitHub-hosted 模型。
- `engaku apply` 仍然只是把名字写进 frontmatter，模型解析交给 VS Code，**不需要改造**。
- 文档里可以加一句 caveat："`engaku.json` 中的模型名需是你的 Copilot 账户/BYOK provider 实际可用的名字。"

### 2.5 JS/TS Chat Features 内置技能（1.116 Preview）

> Setting `jsts-chat-features.skills.enabled`，由 VS Code 官方贡献的内置 skill。

- 说明 **skill** 已被 Microsoft 视为一等公民。我们捆绑的 `templates/skills/*` 路径与契约（SKILL.md）和官方一致，方向正确。
- 长期来看可以观察官方是否会发布"skill schema / 验证器"，届时 engaku 可考虑加 `engaku validate` 做 lint。

---

## 三、与 engaku 无关（仅记录）

| 更新 | 类别 | 备注 |
|---|---|---|
| Incremental chat rendering (1.117) | UX | 无影响 |
| Sort agent sessions / system notifications (1.117) | UX | 无影响 |
| Agents app theming / inline diff / sub-sessions UI (1.117) | UX | 无影响 |
| Tool confirmation carousel (1.116, 实验) | UX | 无影响 |
| Group policy network filter (1.116, 企业) | Enterprise | 若 engaku 用户开启 `chat.agent.networkFilter`，需把 `context7.com` / `dbhub` / chrome-devtools 域名加到 allowed list。可在 mcp.json 模板里加一条注释提醒。 |
| Integrated browser entry points / 拉缩放 (1.116/1.115) | UX | 无影响 |
| Copilot CLI thinking effort (1.116) | CLI | 与 engaku 无交集 |
| TypeScript 6.0.3 (1.117) | Language | 无影响 |

---

## 四、行动建议（按优先级）

**P0 — 值得做一次小改动**
1. 在 `.github/skills/troubleshoot/SKILL.md`（或新建一条 lesson）里，记录"打开 `github.copilot.chat.agentDebugLog.fileLogging.enabled` 查阅历史 session 日志"作为 hook 静默失败的一线排查手段。
2. README 中加一段定位说明：engaku 提供的是**协作 + 生命周期 + 记忆**，并非与 VS Code 内置 "Customize Your Agent" 草拟器竞争。

**P1 — 文档级别，可顺手做**
3. `mcp.json` 模板加一条注释，提醒企业用户若启用 `chat.agent.networkFilter`，需把 MCP 用到的域名加入 allowed list。
4. `engaku.json` 的 README 段落补一句关于 BYOK 模型名要求的 caveat。

**P2 — 不做，仅监控**
5. Sub-sessions（1.117）成熟后，再决定是否在 planner agent prompt 中显式引导。
6. 关注官方是否发布 skill schema / 校验工具，届时再考虑 `engaku validate`。

**不做的事**
- 不重写 `engaku init` 去对标 "Customize Your Agent" 草拟器。
- 不在 hooks 里加任何关于终端通知的特殊处理 —— 1.116 已经默认开启。
- 不为 Agents app 做单独适配 —— 官方承诺自动兼容。

---

## 五、未决问题

- Agents app 在非 Insiders 是否会 GA？若 GA，需在 README 增加一节"engaku 在 Agents app 里的体验"。
- 官方"Customize Your Agent"草拟器是否会沉淀出一个官方 schema / 模板仓库？如果会，engaku 模板可以借鉴或对齐。
