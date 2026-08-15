---
name: Zero-WYM-meta-skill
description: 把重复工作流/想法做成 WorkBuddy Skill 包的全链路工厂：需求收敛→查重→生成→量化门禁（结构校验/三桶触发评测/密钥扫描）→安装→GitHub 发布。当用户说"把这个流程做成 skill""帮我做个 skill 专门干 X""我的 skill 触发不了/过一遍质检/打个分""把我的 skill 发到 GitHub"时使用。不处理：从市场安装某个 skill（走 marketplace）、skillhub 每日推荐、整理第二大脑（走 second-brain-organizer）、读/卸载已有 skill（直接文件操作）。
---

# Zero-WYM-meta-skill · Skill 工厂

> 提取自开源 `qiaomu-meta-skill`（MIT）的可执行机制，按 WorkBuddy 平台与你的 `Zero-WYM-*` 生态独立重写。**不 fork、不继承其品牌/自引用逻辑**，只搬机制。

## 这是什么

一个**自包含**的 Skill 工厂：把你口述的流程、已有提示词、旧 Skill 目录或脚本片段，转化为一个结构合规、触发词精准、无密钥泄露、可一键安装、可开源发布的 WorkBuddy Skill 包。

核心卖点不是又一套方法论（你已有 `skill-crafting` 的五阶段自检与 11 维评分），而是**可执行的量化门禁**——用脚本真实跑出来的 pass_rate、结构校验结果、密钥扫描结论，而不是"感觉应该没问题"。

## 路由规则（重要）

- 本包是你自建 Skill 生态的**唯一创建权威**。
- 一旦本包激活（用户表达"做 / 改造 / 质检 / 发布 skill"意图），**不并行调用内置 `skill-creator`**，避免双源冲突。仅在用户显式要求"和 skill-creator 对比"时例外。
- 与 `skill-crafting`（技能匠人专家）的关系：选中该专家时以其为权威；日常未选专家时以本包为权威。两者按会话场景天然分层，不打架。
- 本包**所有脚本零依赖**（仅用 Python 标准库），不要求 `pyyaml`；frontmatter 用包内自写解析器。

## 何时使用 / 何时不用

**用：**
- "把这个流程做成 skill" / "帮我做个 skill 专门干 X"
- "我的 skill 触发不了，看看描述" / "给我这个 skill 过一遍质检" / "打个分"
- "把我的 skill 发到 GitHub 上"

**不用（交给其他能力）：**
- 从推荐市场安装某个 skill → `marketplace` / `skillhub-daily`
- 整理第二大脑素材 → `second-brain-organizer`
- 读 / 卸载 / 改一个已装 skill → 直接文件操作

## 六环节流程

1. **需求收敛**：把模糊诉求收敛成「要做什么 / 谁用 / 输入 / 输出 / 边界 / 绝不做什么」六要素。输出一份需求确认（不代表同意写入，先对齐）。
2. **查重**：扫 `~/.workbuddy/skills/` 已装的 14+ 个技能 + 工作区技能目录 + WorkBuddy 推荐市场（`marketplace search`）。命中同名/同义则提醒用户，避免和你自己的生态撞车。
3. **生成**：写 `SKILL.md`（frontmatter + 路由规则 + 流程 + 触发词）+ `references/`（按需）+ `scripts/`（按需，零依赖）+ `evals/trigger_cases.json`（三桶用例）。
4. **量化门禁**（见下）：结构校验、三桶触发评测、密钥扫描、SKILL.md ≤ 14KB 预算。任一不过则回到生成环节修正，不带着红灯交付。
5. **安装**：备份已装同名目录 → 原子替换（失败回滚）→ 验证加载。**绝不静默覆盖**。
6. **发布**（按需）：密钥扫描 → 特性分支 → PR → Release → 安装验证。**禁止直推主分支**；需 `gh` 且已登录。

## 量化门禁标准

| 门禁 | 工具 | 通过线 |
|---|---|---|
| 包结构 | `scripts/validate_skill.py` | SKILL.md 存在、frontmatter 合法、无嵌套 SKILL.md、≤ 14KB |
| 触发力 | `scripts/trigger_eval.py` | 三桶 `pass_rate` 100%（该触发全中、不该触发/近邻全不误触） |
| 密钥安全 | `scripts/secret_scan.py` | 零命中（无 api_key / token / ghp_ / 私钥 / 个人凭据） |
| 环境 | `scripts/check_env.py` | gh（如需发布）、Python 标准库可用、已装清单可读 |

> **触发评测的诚实边界（重要）**：`trigger_eval.py` 是**概念词袋命中**的启发式代理指标——它验证 `description` 的关键词覆盖用例文本，**不等于模型真的会路由到本 Skill**。README/报告里写"触发评测通过"时，必须附带这句免责说明，不得假装它等于真实路由力。

## 输入与输出

- **输入**：口述流程 / 已有提示词 / 旧 Skill 目录 / 脚本片段。
- **输出**：完整 Skill 目录（含 `SKILL.md` + `references/` + `scripts/` + `evals/`）+ ZIP 打包 + 一份质检报告（结构校验 / 触发评测 pass_rate / 密钥扫描结论 / 11 维评分 / 未覆盖范围）。

## 绝不做什么

- 不静默覆盖已装技能（必先备份并验证）。
- 不直推主分支（发布走 PR）。
- 不把你的凭据 / 个人信息写进包。
- 不生成 TODO 占位模板（每个交付文件都应是完整可用的）。
- 不删除你的文件（清理只做只读扫描或移到备份）。
- **未实跑的验证一律标"未实测"，不假报通过。**

## 脚本索引（全部零依赖，用 managed Python 跑）

```bash
PY="C:/Users/33754/.workbuddy/binaries/python/versions/3.13.12/python.exe"

# 1. 环境预检（gh 定位/登录、Python 标准库、已装清单查重）
"$PY" scripts/check_env.py --skills-dir "D:/.agent/skills" --user-skills "C:/Users/33754/.workbuddy/skills"

# 2. 包结构校验 + 嵌套检测 + 体积预算
"$PY" scripts/validate_skill.py --skill-dir .

# 3. 三桶触发评测
"$PY" scripts/trigger_eval.py --skill-dir . --cases evals/trigger_cases.json

# 4. 密钥泄露扫描
"$PY" scripts/secret_scan.py --skill-dir .

# 5. 安装（备份+原子替换+回滚）
"$PY" scripts/install_skill.py --skill-dir . --target "C:/Users/33754/.workbuddy/skills"

# 6. 发布（需 gh 已登录；未登录自动降级为本地打包+步骤清单）
"$PY" scripts/publish_skill.py --skill-dir . --repo Owner/Repo --dry-run
```

## References

- `references/making-method.md` — 五阶段制作方法 + 11 维评分卡
- `references/trigger-eval-method.md` — 三桶触发用例设计与词袋评测原理、局限
- `references/publish-pipeline.md` — gh 发布链路（密钥扫描→分支→PR→Release→验证），禁止直推主分支
- `references/workbuddy-conventions.md` — WorkBuddy 平台约定（SKILL.md 契约、frontmatter 解析、用户级/项目级目录、零依赖、中文触发词）
