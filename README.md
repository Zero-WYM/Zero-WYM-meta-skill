# Zero-WYM Skill 品牌体系

本仓库是 `Zero-WYM` 品牌下 WorkBuddy Skill 的集合仓：

- 仓库根目录为 **`Zero-WYM-meta-skill`**：把重复工作流固化为可实测、可发布 Skill 包的全链路工厂。
- `skills/` 目录下为品牌体系中的其他 9 个 Skill，覆盖操作手册、上下文守护、OCR、整理、同步、PowerShell 执行等场景。

所有 Skill 均经过结构校验、密钥泄露扫描与触发评测（如有 evals），可直接安装到 WorkBuddy 使用。

## Skill 一览

| Skill | 路径 | 一句话说明 |
|---|---|---|
| Zero-WYM-meta-skill | 仓库根目录 | Skill 工厂：需求收敛 → 查重 → 生成 → 量化门禁 → 安装 → GitHub 发布 |
| Zero-WYM-brain-skill | `skills/Zero-WYM-brain-skill` | 品牌操作手册与总指挥，调度表 + 进化模式 |
| Zero-WYM-rules-skill | `skills/Zero-WYM-rules-skill` | AI 对话规则「行为宪法」权威源 |
| Zero-WYM-context-skill | `skills/Zero-WYM-context-skill` | 上下文守护 · 会话记忆继承 |
| Zero-WYM-organize-skill | `skills/Zero-WYM-organize-skill` | 第二大脑（Obsidian）素材归档与知识点提炼 |
| Zero-WYM-sync-skill | `skills/Zero-WYM-sync-skill` | 第二大脑 → 飞书知识库同步管线 |
| Zero-WYM-ocr-skill | `skills/Zero-WYM-ocr-skill` | 本地 easyocr 离线图片文字识别 |
| Zero-WYM-lint-skill | `skills/Zero-WYM-lint-skill` | PowerShell 5.1 语法兼容性静态检查 |
| Zero-WYM-runner-skill | `skills/Zero-WYM-runner-skill` | WorkBuddy 沙箱内 PowerShell 可靠执行器 |
| Zero-WYM-lnk-skill | `skills/Zero-WYM-lnk-skill` | Windows .lnk 快捷方式可靠生成器 |

## 安装方式

将任意 Skill 目录复制到 WorkBuddy 的 skills 加载路径即可：

- 用户级：`C:\Users\<用户名>\.workbuddy\skills\`
- 项目级：`<workspace>\.workbuddy\skills\`

例如：

```bash
cp -r skills/Zero-WYM-organize-skill ~/.workbuddy/skills/
```

## 质量门禁

每个 Skill 在发布前均执行：

1. `scripts/validate_skill.py` — 结构校验、frontmatter 解析、体积 ≤14KB。
2. `scripts/secret_scan.py` — 密钥/凭据泄露扫描，要求零命中。
3. `scripts/trigger_eval.py` — 三桶触发评测（如有 `evals/trigger_cases.json`），要求 100% pass_rate。

运行方式（以 `Zero-WYM-meta-skill` 为例）：

```bash
cd Zero-WYM-meta-skill
python scripts/validate_skill.py --skill-dir .
python scripts/secret_scan.py --skill-dir .
```

## 发布纪律

- 所有变更走 PR，禁止直推 `main`。
- 密钥扫描未通过 = 阻断发布。
- 不在包内写入任何个人凭据。
