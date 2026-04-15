# check-update Hook 行为重设计

> 设计调整，整理自 2026-04-08 对话。作为 V3 计划的补充，影响 Task 7（原 check-update 逻辑）以及新增的 scanner-update agent。

---

## 问题背景

V3 Task 4 执行后 `.ai/modules/` 为空，发现当前 `cmd_check_update.py` 有三个结构性问题：

1. **空 modules 目录必然阻断** — `_knowledge_updated_after()` 在无 `.md` 文件时直接返回 `False`，导致任何代码变更都被阻断，无论是否有 module 体系
2. **阻断条件过宽** — 只要有任意文件 unclaimed（未被任何 module `paths:` 声明），精确匹配就降级为 "任意 module 比代码新就放行"，逻辑有漏洞
3. **unclaimed files 缺乏引导** — 发现新文件时只报错，没有可操作的结构更新路径

---

## 新阻断逻辑

### 核心原则

> `paths:` 是用户的显式声明——"我决定跟踪这些文件"。未声明 = 没有承诺，不应阻断。

```
claimed_files   = 变更文件中被某 module paths: 覆盖的部分
unclaimed_files = 其余文件

block 条件 = claimed_files 非空 AND 对应 modules 中没有任何一个比代码新
```

废弃旧的 fallback 逻辑（`all_claimed = False` 时降级为"任意 module 比代码新"）。

### 三种输出情况

| 情况 | 判断条件 | 输出 |
|------|----------|------|
| **硬阻断** | claimed_files 非空 且对应 module 未更新 | `exit 2`（现有行为不变） |
| **软提醒** | unclaimed_files 非空 | `exit 0` + stdout JSON `systemMessage` |
| **空 modules 提示** | `.ai/modules/` 为空或只有 `.gitkeep` | `exit 0` + stdout JSON `systemMessage` |
| **放行** | 无 claimed_files 变更 OR 对应 module 已更新 | `exit 0`，无输出 |

软提醒的 stdout JSON 格式：
```json
{
  "systemMessage": "Unclaimed files detected: src/foo.py, src/bar.py\nTo add coverage, start a new chat with @scanner-update:\n  \"Add coverage for these unclaimed files: src/foo.py, src/bar.py\""
}
```

空 modules 提示的 stdout JSON：
```json
{
  "systemMessage": "No module knowledge files found.\nRun the scanner agent to build the initial module index."
}
```

---

## scanner-update Agent（新增）

### 定位

| Agent | 触发 | 职责 | 模型 |
|-------|------|------|------|
| `scanner` | 用户主动 | 全局分析 → 提议分组 → 用户确认 → 写入 | 高级模型 |
| `scanner-update` | check-update systemMessage 引导 | 增量：处理指定 unclaimed 文件 | 轻量模型 |
| `knowledge-keeper` | dev 自动调用 | 更新已声明 module 的内容 | 轻量模型 |

### scanner-update 行为规则

**输入：** 用户提供的 unclaimed 文件列表

**决策逻辑（按优先级）：**
1. 文件路径与某现有 module 的 `paths:` 条目**同目录前缀** → 自动追加，直接执行，不等确认
2. 文件路径无明显归属 → 提问用户：归入 [existing module] 还是新建 [suggested name]？
3. 用户选择新建 → 创建新 module 文件，**不修改**任何现有 module

**硬性约束：**
- 只处理传入的文件列表，不扫描其他文件
- 绝不修改未涉及的现有 module 的内容或 paths:
- 不生成或修改 `.ai/rules.md`

### 执行顺序

check-update 发现 unclaimed files 时，通过 `decision: "block"` + `reason` 让 dev 在当前对话中按序执行：

```
Stop hook (stop_hook_active=false)
  → 检测到 unclaimed files
  → stdout JSON: decision:"block", reason:"Call @scanner-update for [files], then call @knowledge-keeper"
  ↓
dev 继续（stop_hook_active=true）
  → call scanner-update（结构确定）
  → call knowledge-keeper（内容更新）
  ↓
Stop hook 再次触发（stop_hook_active=true）→ exit 0，不检测
```

**理由：** scanner-update 必须在 knowledge-keeper 之前完成。module 结构确定后，knowledge-keeper 才能写入正确的文件。反序执行会导致 knowledge-keeper 更新错误的 module 或漏更新新建的 module。

---

## `paths:` 支持 glob 模式（新增）

现有匹配仅支持精确路径和目录前缀。需扩展为通过 stdlib `fnmatch` 支持 glob 模式：

```yaml
paths:
  - src/engaku/cmd_*.py      # fnmatch glob
  - src/engaku/              # 目录前缀（现有）
  - src/engaku/cli.py        # 精确路径（现有）
```

匹配顺序：精确路径 → 目录前缀 → fnmatch 模式。`fnmatch` 不支持 `**`，但目录前缀已覆盖递归场景。

---

## 实施影响（新增/修改文件）

### 修改
- `src/engaku/cmd_check_update.py` — 实现新三分支逻辑 + glob 支持 + unclaimed 软提醒
- `tests/test_check_update.py` — 补充测试：空 modules / unclaimed / claimed-only 三种情况
- `.github/agents/dev.agent.md` — 增加一句：unclaimed files 时 Stop hook 会指示先调 scanner-update 再调 knowledge-keeper

### 新增
- `.github/agents/scanner-update.agent.md`
- `src/engaku/templates/scanner-update.agent.md`
- `src/engaku/templates/engaku.json` — 新增 scanner-update 条目
- `src/engaku/cmd_init.py` — 拷贝 scanner-update.agent.md
- `tests/test_init.py` — 更新 EXPECTED_FILES
