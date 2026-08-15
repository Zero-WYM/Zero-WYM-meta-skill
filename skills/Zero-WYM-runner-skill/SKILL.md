---
name: Zero-WYM-runner-skill
keywords: [runner, 沙箱执行]
description: >-
  WorkBuddy 沙箱内 PowerShell 可靠执行器。当用户需要在本沙箱执行 PowerShell（查询/文件操作/系统管理）
  且遭遇「.ps1 文件被静态拦截整脚本不执行」「Add-Content 写不进文件」「Get-ChildItem 只枚举到目录层」
  「结果回收失败」时使用：改用内联 PowerShell 命令（PowerShell 工具 command 字段直接写）、用 Out-File -Encoding
  UTF8 替代 Add-Content、用 Test-Path 精确否定代替 Get-ChildItem 计数、用 Out-File 落盘 + Read 读回作为唯一稳的结果回收。
agent_created: true
version: 1.0.0
status: draft
---

# PowerShell 沙箱可靠执行器（草稿 · 待审阅）

> ⚠️ 本 skill 由自动化任务（痛点驱动推荐）反向生成，目前为**草稿骨架**，实现待用户审阅后补全。
> 记忆证据：`~/.workbuddy/MEMORY.md` 2026-08-15 补充的「PowerShell 沙箱通道坑」 ——
> ① .ps1 文件方式（即便只读查询、写已存在子目录）可能被沙箱静态拦截整脚本不执行 → 改用内联 PowerShell 命令；
> ② Add-Content 在沙箱写不进文件（后续行全部丢失）→ 改用 Out-File -Encoding UTF8（覆盖写）；
> ③ Get-ChildItem 对 D:\program 根可能只枚举到目录层（假象「44 目录 0 文件」）→ 用 Test-Path 精确否定更可靠；
> ④ Out-File 落盘 + Read 读回是沙箱内唯一稳的 PowerShell 结果回收模式。

## Overview

这是一个**环境适配 / 执行模式** skill：把「在 WorkBuddy 沙箱里跑 PowerShell」的已验证可靠姿势固化下来，
避免每次都踩 .ps1 静态拦截、Add-Content 静默失败、Get-ChildItem 视图受限、结果回收丢失等坑。

## When to Use

- 任何要在沙箱内执行 PowerShell 的场景（尤其文件查询、磁盘枚举、系统管理）。
- 用户报告「脚本没反应」「写不进文件」「ls 说没文件但其实有」。
- 与 `Zero-WYM-lint-skill`（PS 5.1 语法兼容）互补：本 skill 管「执行通道」，Zero-WYM-lint-skill 管「语法」。

## 已知坑与正确姿势（红线，来自记忆）

| 失败做法 | 现象 | 正确做法 |
|----------|------|----------|
| 用 `.ps1` 文件执行（即便只读） | 沙箱静态拦截整脚本不执行 | 用 **内联 PowerShell 命令**（PowerShell 工具 `command` 字段直接写单行/分段） |
| `Add-Content` 写文件 | 沙箱写不进（后续行全丢） | `Out-File -Encoding UTF8`（覆盖写）替代 |
| `Get-ChildItem D:\program` 判断有无残留 | 可能只枚举目录层（假象「0 文件」） | 用 `Test-Path` 精确否定更可靠 |
| 依赖 `Add-Type` / COM 实例化 | 沙箱禁用 | 禁用；纯内联命令 + 标准 cmdlet |
| PowerShell 写 `D:\` 根 | 被拒 | 写到已存在子目录 |
| 结果回收靠 stdout | 可能截断/丢失 | `Out-File` 落盘 → `Read` 读回（唯一稳） |

## Workflow（草图，待补实现）

1. 判断任务是否必须 PowerShell（文件/系统类）；是则走内联命令，绝不落 .ps1。
2. 写命令时用 `Out-File -Encoding UTF8` 把结果落到已存在子目录的 txt；避免 `Add-Content`、避免 `Add-Type`/COM。
3. 枚举/判断存在性用 `Test-Path` 而非 `Get-ChildItem` 计数（尤其 `D:\program` 根）。
4. 用 `Read` 工具读回落盘文件获取结果；不要在 stdout 里靠肉眼回收。

## Resources

### scripts/
- （可选）`run_ps_inline.py` —— 封装「内联 PS → Out-File 落盘 → 读回」的可靠执行包装（草稿占位，待补）。

### references/
- （可选）`sandbox_pitfalls.md` —— 完整坑位与实测案例（审阅后补）。

### assets/
- 无。

---

**审阅提示**：用户确认痛点（PS 在沙箱里静默失败）后，再补 `run_ps_inline.py` 与 `references/sandbox_pitfalls.md`；
并确认是否要与 `Zero-WYM-lint-skill` 合并为单一 PS 工具 skill（二者维度不同：语法 vs 执行通道，建议保持独立但互相引用）。
