---
name: Zero-WYM-brain-skill
keywords: [brain, 大脑]
description: 'AI 对话规则总指挥（操作手册）。纯调度/进化中心：引用 Zero-WYM-rules-skill（行为宪法）作为规则权威源，按意图派发专家 Skill（Zero-WYM-organize-skill / skillhub-daily / llm-wiki / tutor-skills / material-organizer / Zero-WYM-sync-skill），并在遇到未覆盖任务域时按「检索→安装→适配→新建→卸载」进化。不内嵌任何 operational 工作流细节。 / AI dialogue-rules commander (operations manual). A pure dispatch and evolution hub: references Zero-WYM-rules-skill (the constitution) as the authoritative ruleset, routes tasks to the right expert Skill by intent (Zero-WYM-organize-skill / skillhub-daily / llm-wiki / tutor-skills / material-organizer / Zero-WYM-sync-skill), and evolves via the retrieve -> install -> adapt -> create -> uninstall loop when facing uncovered task domains. Embeds no operational workflow details itself.'
version: 1.1.0
agent_created: true
---

# 操作手册 · 技能调度总指挥（Commander Only）

> 本 Skill 是用户 AI 协作的**顶层调度与进化中心**。它**只做三件事**：
> 1. **引用规则**——行为宪法见 `Zero-WYM-rules-skill` Skill（本手册不重复内嵌）。
> 2. **派发任务**——按下方调度表把任务交给正确的专家 Skill 执行。
> 3. **进化生态**——遇到未覆盖任务域，按第三部分把通用能力进化成贴合用户的专属 Skill。
>
> 它**不内嵌任何 operational 工作流**（整理归档步骤在 `Zero-WYM-organize-skill`、同步架构在 `Zero-WYM-sync-skill`、对话规则在 `Zero-WYM-rules-skill`）。司令官只下指令，不自己干活。

---

# 新对话启动协议（Boot Protocol）

> **每次新开对话，无脑执行**：先加载 `Zero-WYM-rules-skill`（行为宪法）与本 `Zero-WYM-brain-skill`（总指挥），再听需求。**两 skill 不加载，不干活。**
> 加载方式：Skill 工具分别调用 `Zero-WYM-rules-skill`、`Zero-WYM-brain-skill`。

## 启动顺序
1. **加载规则**：Skill → `Zero-WYM-rules-skill`（对话全程行为宪法，13 节规则生效）。
2. **加载总指挥**：Skill → `Zero-WYM-brain-skill`（即本 skill，建立调度与三层查找能力）。
3. **听需求**：用户陈述任务，按规则补全 6 要素；信息够先出 MVP 意图。

## 需求落地的三层技能查找（自上而下，命中即停）
- **L1 现有 Zero-WYM-\***：查下方「技能触发总表」，按职能词（中 / 英 / 品牌词）命中 → 直接加载该 skill 执行 → 按规则 5 维声明 + 验收。
- **L2 已安装 skill**：在已安装的社区 / 内置 skill 中检索适用者（如 `skillhub-daily`、`llm-wiki`、`tutor-skills`、`material-organizer` 等）→ 调用执行 → 验收。
- **L3 市场适配（find-skill + 改造品牌化 + 发布开源）**：若 L1 / L2 均无适配，用 **Skill 工具 `find-skills`** 搜索市场适配任务域的 skill → 安装（仅获取，归 marketplace）→ 走 `Zero-WYM-meta-skill`（造 skill 工厂）**改造品牌化**：查重 → 改名 `Zero-WYM-<单职能词>-skill` → 加 `keywords:[英,中]` → 量化门禁质检 → **发布开源（GitHub，走 meta-skill 第 6 环节：密钥扫描 → 特性分支 → PR → Release → 安装验证；禁止直推主分支）** → 纳入体系 → 执行 → 验收。

> 进化闭环：L3 改造并**发布开源**的 skill 既是下一次对话的 L1 候选（自用），也是对外可见的社区资产（对外）；体系自我生长、对外可复用。

---

# 技能触发总表（中文 / 品牌词路由）

> 用户可用**自然语言 + 中文职能词**直接点名触发某个 Zero-WYM Skill。格式：
> `[品牌词][职能词]skill [指令]`
> - **品牌词（任选其一，大小写 / 组合不限）**：`望月明` / `zero` / `Zero` / `ZERO` / `WYM` / `wym` / `Zero-WYM`
> - **职能词**：下表第二列（中英文均可）
> - 例：`望月明大脑skill 帮我把这段素材归档` → 加载 `Zero-WYM-brain-skill`（总指挥）；`zero整理skill 提炼这张截图` → 加载 `Zero-WYM-organize-skill`

| 职能词(中) | 职能词(英) | Skill 名 | 负责什么 |
|-----------|-----------|----------|---------|
| 规则 | rules | `Zero-WYM-rules-skill` | 行为宪法 / 对话规则（13 节） |
| 上下文 | context | `Zero-WYM-context-skill` | 上下文守护 / 会话记忆继承 |
| 元 | meta | `Zero-WYM-meta-skill` | 把流程做成 Skill 的工厂 |
| 同步 | sync | `Zero-WYM-sync-skill` | 第二大脑 → 飞书知识库同步 |
| 识图 | ocr | `Zero-WYM-ocr-skill` | 本地离线 OCR 读图 |
| 大脑 | brain | `Zero-WYM-brain-skill` | 操作手册 / 总指挥调度 |
| 整理 | organize | `Zero-WYM-organize-skill` | 第二大脑素材整理归档 |
| 语法检查 | lint | `Zero-WYM-lint-skill` | PowerShell 5.1 语法检查 |
| 沙箱执行 | runner | `Zero-WYM-runner-skill` | 沙箱内 PowerShell 可靠执行 |
| 快捷方式 | lnk | `Zero-WYM-lnk-skill` | Windows .lnk 快捷方式生成 |

> **路由规则**：剥掉品牌词与 `skill` 后缀，剩余职能词命中上表即加载对应 Skill；品牌词可有可无、大小写不限。各 Skill 的 `keywords:` 字段也登记了中英触发词，供 agent 直接匹配。

---

# 第一部分：行为宪法（引用，不内嵌）

- **规则权威源 = `Zero-WYM-rules-skill` Skill**（13 节：选型 / 6 要素+需求翻译 / 上下文 / 5 维 / 任务推进 / 5 件前置 / UI验收 / 留痕 / L1-L4 / Prompt法则 / Eval / 禁止项 / 输出风格）。
- **常驻精简版**：WorkBuddy「自定义指令」框粘贴的是 `Zero-WYM-rules-skill` 的精简核心（约 1100 字），永远自动生效；本手册是其完整增强版，复杂任务或用户要求「按规则来」时加载。
- 加载本 Skill 后，如需完整规则细节，引用 `Zero-WYM-rules-skill` 即可。

---

# 第二部分：技能调度表（总指挥派发）

> 检测到下列意图时，**先加载本 Skill（操作手册），再用 Skill 工具派发对应的专家 Skill** 执行，而非在对话里从零手搓。专家 Skill 已内化 `Zero-WYM-rules-skill` 宪法，无需重复约束。

| 用户意图 | 派发 Skill | 说明 |
|----------|------------|------|
| 整理 / 归档第二大脑（Obsidian）、课程截图、提炼知识点（新素材录入） | `Zero-WYM-organize-skill` | 用户的专属仓库工作流（**新素材录入/整理，不负责同步**；同步归 `Zero-WYM-sync-skill`） |
| 把第二大脑**同步到飞书(分享+更新回推)**、超限 pptx 处理 | `Zero-WYM-sync-skill` | 同步管线权威细节源（从 Zero-WYM-organize-skill 抽出的独立 Skill） |
| 发现 / 推荐好用的 Skill、每日技能雷达 | `skillhub-daily` | 已设每晚 23:00 定时推送 |
| 把知识点导出成可浏览的 Wiki | `llm-wiki` | 对外展示版知识库 |
| 课件 / 学习资料转学习库、出题自测 | `tutor-skills` | 配合 `2_待掌握/` 掌握度跟踪 |
| 通用资料提炼 / 研究笔记（非仓库专属） | `material-organizer` | 已装，作通用兜底 |

### 暂不接入的任务域（留待迭代）

> **注记**：以下能力用户**当前尚未实际使用**，为避免提前占用调度表与堆积用不上的 Skill，**暂不派发、暂不写进上表**。待用户真正用到时，按「第三部分 · 新任务适配模式」接入。

- **PPT 生成**（`tencent-pptx` 等）—— 暂不使用
- **Excel / 表格处理**（`sheetagent` 等）—— 暂不使用
- **Word 文档 / 报表**（`tencent-docx` 等）—— 暂不使用

---

# 第三部分：新任务适配模式（Skill 生态进化流程）

> 当用户触发**调度表未覆盖**的任务域（例如上面「暂不接入」的 PPT / Excel / Word 报表，或任何新出现的专业任务），**不要临时手搓一套**，**按以下生命周期把通用能力进化成贴合用户的专属 Skill**：

## 进化六步

1. **检索（find）**：用 `marketplace-skill-installer` 在市场搜索适配的通用 Skill，挑出 1–2 个候选。
2. **安装（install）**：把候选通用 Skill 装到本地，先按默认能力跑通一次，确认它真能干活。
3. **适配（adapt）**：基于**用户的工作习惯与个人偏好**（见 `Zero-WYM-rules-skill` 宪法，尤其六要素、5 维声明、留痕、红线），把通用 Skill 包装 / 改写为贴合用户的版本——确定它的命名、触发词、铁律与输出风格。
4. **新建（build）**：把定制版写成一个**独立专属 Skill**（命名清晰，内含用户偏好与铁律）。
5. **卸载（uninstall）**：确认定制版可用、覆盖原通用能力后，**卸载原通用 Skill**，避免功能重复与规则漂移。
6. **回填（backfill）**：把新任务类型补进本操作手册「第二部分 · 技能调度表」，并把本次进化记入工作记忆日志。

## 原则

- 此模式确保 Skill 生态**随用户实际工作持续演化**，始终贴合个人偏好，而不是堆积一堆用不上的通用 Skill。
- 任何新建的专属 Skill 都必须**内化 `Zero-WYM-rules-skill` 宪法**（至少对齐：6 要素、5 维声明、复杂度闸门、Eval 驱动、事实/判断分开、不替关键决定拍板）。
- 若适配过程中发现通用 Skill 已足够好、无需定制，则跳过第 3–5 步，仅做第 6 步回填并注明「用通用版即可」。

---

# 第四部分：记忆沉淀（Memory Sedimentation · 司令官 mandate）

> 对话记忆需**双写沉淀**：既存进个人知识库（Obsidian `D:\第二大脑\记忆沉淀\`），也存进 WorkBuddy 记忆系统。本部分是司令官对该机制的**授权与规范**，具体执行由每日自动化「记忆沉淀 · 每日对话蒸馏」驱动。

## 双写目标

1. **Obsidian 第二大脑** `D:\第二大脑\记忆沉淀\`
   - `索引.md`：总索引（倒序条目表 + 长期架构总览）。
   - `YYYY-MM-DD_对话纪要.md`：当日决策、Skill 体系、命名规范、偏好、待办、踩坑。
2. **WorkBuddy 记忆系统**（三层）
   - 工作区 `.../memory/YYYY-MM-DD.md`：每日要点追加。
   - 工作区 `.../memory/MEMORY.md`：长期项目笔记（≤3000 字，去重）。
   - 用户级 `C:\Users\33754\.workbuddy\MEMORY.md`：跨项目偏好（≤4000 字）。

## 沉淀原则

- 只留可复用决策 / 偏好 / 结构，不记临时路径与工具报错细节。
- Obsidian 用标准 markdown 语法，目录链接指向 `README.md`。

---

# 触发与协同

- **触发**：用户提到「操作手册」「按规则来」「按对话规则」，或任何复杂 / 多步 / 涉及上述意图的任务，立即加载本 Skill。
- **协同**：本 Skill 是顶层，不替代专家 Skill；它派发专家、监督其遵循 `Zero-WYM-rules-skill` 宪法、并在空白处进化新 Skill。
- **与自定义指令的关系**：设置在 WorkBuddy 中的「自定义指令」（精简核心版，源于 `Zero-WYM-rules-skill`）永远自动生效；本 Skill 是其「完整增强版」，在复杂任务或用户要求时加载，二者不冲突、互补。
