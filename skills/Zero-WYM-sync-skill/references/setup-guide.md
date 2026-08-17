# Zero-WYM-sync-skill · 配置与凭据指引（setup-guide）

> 本文件是 `Zero-WYM-sync-skill` SKILL.md 凭据段的补充。所有「官方申请/控制台地址」均标注 **「待你确认」**，请勿臆造——以你实际开通平台的官方页面为准。

## 1. 飞书知识库 / 开放平台凭据

- **用途**：`sync_to_feishu.py` 把 `D:/第二大脑` 同步到飞书知识库（分享 + 旧笔记/附件更新回推）。
- **依赖**：外部 CLI `lark-cli`（飞书上传用，需 `PATH` 可寻址，脚本内已做 `/c/...` → `C:\...` 归一）。
- **配置位置**：⚠️ 待你确认（lark-cli 配置文件或环境变量 `app_id` / `app_secret` / token，以官方为准）。
- **安全**：密钥勿外发、勿提交 git。
- **轮换 / 撤销**：到飞书开放平台控制台重置应用密钥。

## 2. 运行依赖

- **Python**：脚本均为纯标准库（`json` / `re` / `subprocess` / `urllib` 等），无需 `pip install`。
- **超限 pptx 压缩（可选）**：`shrink_pptx.py` 用 **Pillow**（图片重编码）与 **imageio-ffmpeg**（视频转码）；缺失时脚本会明确提示并安全退出，不影响基础同步。
- **外部工具**：`lark-cli.cmd`（飞书上传）；`D:/第二大脑` 仓库（唯一真源，需存在）。
- **已内置脚本**（`scripts/`）：`normalize.py` / `sync_to_feishu.py` / `shrink_pptx.py` / `upload_shrunk_pptx.py`。

## 3. 安全红线

- 真实飞书密钥 **永不**提交、不对外分享。
- 自动化（`automation-1786459999938`，每日 23:00）运行时只读取本地飞书凭据，不外传。
