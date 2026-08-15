# WorkBuddy 平台约定

> 让生成的 Skill 在 WorkBuddy 里能被正确加载、路由、评分。移植时按本平台规则重写，不沿用 `skills.sh`/`npx` 生态假设。

## SKILL.md 契约

- **必须**有 YAML frontmatter，至少含 `name` 与 `description`。
- `name`：字母/数字/连字符，本生态统一 `Zero-WYM-<短名>`。
- `description`：**路由核心**。必须自然嵌入用户真实会说的短语（中文），并写明"何时不用"以划清近邻边界。WorkBuddy 据此路由，写得好不好直接决定触发力。
- 可选 `license`（如 MIT）。
- 正文写：角色定位、路由规则、流程、输入/输出、脚本索引、references 索引。
- **体积预算 ≤ 14KB**：Agent 加载 Skill 要进上下文，过大挤占预算。超了拆进 `references/`。

## frontmatter 解析（零依赖）

不装 `pyyaml`。包内 `validate_skill.py` 用自写解析器，仅支持：
- 顶层 `key: value`（value 可为带引号字符串）
- `description` 支持 `>-` / `|` 折叠块（多行）
- 不支持嵌套映射 / 复杂结构（Skill frontmatter 不需要）

## 技能目录位置

| 级别 | 路径 | 说明 |
|---|---|---|
| 用户级 | `C:\Users\33754\.workbuddy\skills\` | 跨项目生效，已装 14+ 个 |
| 项目级 | `<workspace>\.workbuddy\skills\` | 仅当前项目 |
| 本工作区根 | `D:\.agent\skills\` | 本会话 workspace 即技能根，`Zero-WYM-*` 同族并列于此 |

> `install_skill.py` 默认装到用户级；可用 `--target` 指定工作区根。装前先备份同名目录，原子替换，失败回滚。

## 零依赖原则

- 所有脚本仅用 Python 标准库，不 `pip install`（managed 环境隔离，不污染）。
- 用 managed Python：`C:\Users\33754\.workbuddy\binaries\python\versions\3.13.12\python.exe`。
- 需要外部二进制（如 `gh`）时，脚本自带 `find_gh()` 定位（PATH → winget 包目录 → 用户可 `--gh-path` 覆盖），不依赖 shell PATH 已刷新。

## 中文触发词

- `description` 用中文、含用户原话（"做成 skill""触发不了""发到 GitHub"）。
- references 与 evals 也用中文，便于你本人维护。

## 可用工具补充

- 想让模型在对话中主动调用本包：依赖 description 路由即可，无需额外注册。
- 管理/查看已装 Skill：`SkillManage` 工具（list/create/modify）。
- 发布到推荐市场：走 `workbuddy_marketplace_skill`，不在本包职责内。
