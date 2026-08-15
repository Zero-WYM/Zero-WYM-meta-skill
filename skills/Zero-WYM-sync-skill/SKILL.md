---
name: Zero-WYM-sync-skill
keywords: [sync, 同步]
description: '第二大脑（Obsidian）知识库管线：本地 normalize.py 导出标准 MD；飞书知识库做对外分享/备份并支持旧笔记/附件更新回推；ima 仅作微信生态内容收口，经 extract_from_ima.py 单向抽到 Obsidian 真源。含超限 pptx 压缩（shrink_pptx.py / upload_shrunk_pptx.py）、sha256 变更检测、Windows/Git-Bash 路径陷阱与每日 23:00 自动化。当用户说把第二大脑同步到飞书 / 旧笔记改了怎么回传飞书 / 大 PPT 怎么传飞书 / 微信收藏怎么进第二大脑时加载。行为准则对齐 Zero-WYM-brain-skill。 / Second-brain (Obsidian) knowledge-base pipeline: local normalize.py exports standard Markdown; Feishu wiki handles external sharing and backup with update-pushback for old notes and attachments; ima acts only as a WeChat-ecosystem collector, pulled one-way into Obsidian (the single source of truth) via extract_from_ima.py. Includes oversized-pptx compression (shrink_pptx.py / upload_shrunk_pptx.py), sha256 change detection, Windows/Git-Bash path pitfalls, and a daily 23:00 automation. Load when the user says sync my second brain to Feishu / how to push edited notes back to Feishu / how to send a large PPT to Feishu / how to get WeChat favorites into my second brain. Behavior aligns with Zero-WYM-brain-skill.'
version: 1.1.0
agent_created: true
---

# 第二大脑 知识库管线（Obsidian → 飞书同步）

## 架构总览（2026-08-15 终态，已与用户确认）

```
D:/第二大脑 (Obsidian) —— 唯一真源（你随意改，零负担）
   └─ normalize.py → export/  (标准 MD + 附件 + manifest.json)
         └─ sync_to_feishu.py  → 飞书知识库（分享/备份：新增 + 旧笔记/附件更新回推，含 pptx 压缩）
```

> 管线脚本已内置到本 Skill 包 `scripts/`（纯 stdlib，无需 pip 安装）：`normalize.py` / `sync_to_feishu.py` / `shrink_pptx.py` / `upload_shrunk_pptx.py`。导出目录默认在包体**外**（`~/.cache/obsidian-kb-sync/export`，可用环境变量 `OBSIDIAN_SYNC_EXPORT_DIR` 覆盖），不再污染 Skill 包。

## 角色分工（务必记牢）

| 系统 | 角色 | 能否被程序改 | 说明 |
|------|------|--------------|------|
| **Obsidian `D:/第二大脑`** | **唯一真源** | 你本地随便改 | 所有精修、双链、结构都在这里 |
| **飞书知识库** | 对外分享 / 备份 | ✅ 完整 CRUD | 已支持新增 + 旧笔记/附件更新回推（见下） |

- **排除项**：另一 vault `D:\proj_novel\MyNove1` 是小说项目，**非知识库，不纳入**。
- 行为约束源自 `Zero-WYM-brain-skill`：6 要素、5 维声明、复杂度闸门、Eval 驱动、事实/判断分开。

## 何时触发

- 「把第二大脑同步到飞书」「旧笔记改了怎么回传飞书」「那两个大 PPT 怎么传飞书」
- 任何把 `D:/第二大脑` 内容同步到飞书知识库的请求

## 转换规则（normalize.py，纯 stdlib）

- wikilink / embed `[[x]]` / `![[x]]` → 标准相对链接 `[](x.md)` / `![](x.png)`
- callout `> [!note]` → 标准引用块
- frontmatter 保留

## 同步策略

- manifest 驱动增量；冲突 → `冲突待处理/` 双版本；删除默认不级联
- 变更检测：export 文件 sha256 存于 `manifest.json`，不一致即回推

## 平台硬限制（必看，踩坑结论）

| 平台 | 限制 | 应对 |
|------|------|------|
| 飞书上传 API | 单文件 **≤20MB 硬上限**（code 1061043）；multipart/分片**无法绕过** | 超限 pptx 用 `shrink_pptx.py` 压缩内部媒体（Pillow 重编码图 + imageio-ffmpeg 转码视频，缺失则安全降级提示）后再传；`upload_shrunk_pptx.py` 把压缩件上传到对应 wiki 节点；压缩件以 `shrunk_from` 标记，原件不再重推 |

## 飞书同步 `sync_to_feishu.py`

- 首轮全量：目录 57 + md 63 + 附件 127 = **247/251**；缺失 4 = 2 个超限 pptx ×2 路径（已压缩上传补齐，现 100%）
- **新增**：md `drive +import` → `wiki +move`；附件 `drive +upload`
- **更新（旧笔记 / 附件回推）**：
  - md 变更：`wiki +node-delete`（**obj-type 必须是 `wiki`**）→ `drive +import` 重导入 → `wiki +move`
  - 附件变更：`drive +upload --file-token <原token>` **原地覆盖**，token 不变
  - 首跑仅基线（存 sha256），不误删；`.bak/.tmp/.swp` 跳过

## 超限 pptx 压缩（`shrink_pptx.py` / `upload_shrunk_pptx.py`）

- `shrink_pptx.py <input.pptx> [--out <out.pptx>] [--quality 70]`：解开 pptx（zip），对 `ppt/media/` 内图片用 Pillow 重编码降体积、视频用 imageio-ffmpeg 转码；重打包为 `<原名>_shrunk.pptx`，并在包内 `customProps/shrunk.json` 标记 `shrunk_from` 原件路径。
  - **降级**：若环境无 Pillow / imageio-ffmpeg，脚本明确提示缺少依赖并退出（非零），**不静默产出损坏文件**；此时可手动用压缩软件降质后回传。
- `upload_shrunk_pptx.py <shrunk.pptx> [--node <wiki_node_id>]`：把压缩件经 `lark-cli` 导入并移动到指定 wiki 节点（逻辑同 `sync_to_feishu.py` 的 md 路径）；缺省时从 `shrunk_from` 反查 `feishu_remote_map.json` 找原件对应节点，跳过原件。

## 环境路径陷阱（Windows + Git-Bash，必记）

- 工作区目录 `workbuddy‘work` 的引号是**弯引号 `‘`（U+2018）**，非直引号 `'`；命令用直引号会 `No such file or directory`
- Git-Bash `/d/…` 虚拟路径 Windows 原生 Python 读不懂 → 用 `__file__` 推导真实 Windows 路径
- 后台子进程 `PATH` 是 `/c/…` 风格 → 归一为 `C:\…` 才能找到 `lark-cli.cmd`
- `lark-cli` 的 `--file` 必须是 **cwd 内的相对路径**，传绝对路径报 `unsafe file path`

## 辅助脚本（`scripts/`，已内置到本 Skill 包）

| 脚本 | 作用 | 状态 |
|------|------|------|
| `normalize.py` | Obsidian → 标准 MD 导出（纯 stdlib） | ✅ 已内置 |
| `sync_to_feishu.py` | 飞书同步（含旧笔记/附件更新回推、压缩件跳过） | ✅ 已内置 |
| `shrink_pptx.py` | 超限 pptx 压缩内部媒体（Pillow + imageio-ffmpeg，缺失降级） | ✅ 已内置 |
| `upload_shrunk_pptx.py` | 压缩件上传到飞书对应 wiki 节点 | ✅ 已内置 |

## 自动化

- `automation-1786459999938`：每日 **23:00**，ACTIVE
- 序列：normalize → 检查连接器 → `sync_to_feishu`（含更新/压缩）→ 报告计数
- `cwd = obsidian-sync`

## 与其他 Skill 的关系

- `Zero-WYM-organize-skill`：负责**新素材录入/本地归档**（用户丢入的素材/资源分类 + 知识点提炼），不负责同步；本 Skill 负责**飞书分享/备份同步的具体管线**，二者互补。
- `Zero-WYM-brain-skill`（操作手册）：行为宪法与调度中心；本 Skill 内化其 6 要素 / 5 维 / 复杂度闸门 / Eval。
