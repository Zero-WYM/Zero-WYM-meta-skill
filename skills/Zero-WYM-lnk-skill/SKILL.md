---
name: Zero-WYM-lnk-skill
keywords: [lnk, 快捷方式]
description: >-
  Windows .lnk 快捷方式可靠生成器。当用户需要在本机创建/修复指向真实文件或目录的
  开始菜单 / 桌面快捷方式（尤其应用装在 D:\program 等非 C 盘、需生成可用 .lnk）时使用。
  本沙箱禁用 COM(WScript.Shell) 与 Add-Type，且 Python open('wb') 覆盖已存在 .lnk 也被拦，
  故采用 pylnk3.for_file(target) 生成标准 lnk（纯 IDList 指向真实文件，Windows 原生解析），
  再用 shell cp -f 拷入目标目录。
  此 skill 应在「创建/修复任何 Windows 快捷方式」时触发。
agent_created: true
version: 1.0.0
status: draft
---

# Windows .lnk 快捷方式生成器（草稿 · 待审阅）

> ⚠️ 本 skill 由自动化任务（痛点驱动推荐）反向生成，目前为**草稿骨架**，实现待用户审阅后补全。
> 记忆证据：`~/.workbuddy/MEMORY.md` 2026-08-15 补充的「.lnk 快捷方式写入」经验 ——
> 「COM(WScript.Shell)/Add-Type 被禁；Python open('wb') 覆盖已存在 .lnk 也被拦（只能新建到工作区）。
> 最可靠做法：pylnk3.for_file(target) 生成标准 lnk（纯 IDList 指向真实文件，Windows 原生解析），
> 生成后 shell cp -f 拷进开始菜单/桌面。」

## Overview

这是一个**环境适配 / 工具型** skill：在 WorkBuddy 沙箱内可靠地生成 Windows `.lnk` 快捷方式，
绕开被禁用的 COM / Add-Type 通道与 `open('wb')` 覆盖拦截，确保生成的 lnk 能被 Windows 原生解析。

## When to Use

- 用户说「给某某程序建个开始菜单/桌面快捷方式」「D:\program 里装的软件没有菜单入口」。
- 需要把 `D:\.Agent\workbuddy`、某 exe、某项目入口固定到开始菜单/桌面/任务栏。
- 任何「创建 / 修复 Windows 快捷方式」的任务。

## 已知坑（红线，来自记忆）

| 失败做法 | 原因 | 正确做法 |
|----------|------|----------|
| `WScript.Shell` COM 建 lnk | 沙箱禁 COM 实例化 | 用 `pylnk3.for_file(target)` |
| `Add-Type` + ShellLink | 沙箱禁 Add-Type | 同上 |
| Python `open('wb')` 覆盖已存在 .lnk | 沙箱拦覆盖（只能新建到工作区） | 先 `for_file` 生成到工作区，再 `shell cp -f` 拷入目标 |
| 手建 `LinkInfo` 写本地路径 | `pylnk3.parse` 崩 `'LinkInfo' has no attribute '_path'` | 优先 `for_file`，别手建 LinkInfo |
| 写 ProgramData 开始菜单（所有用户） | 需管理员，普通权限 Permission denied | 写**用户开始菜单** `C:\Users\33754\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\` |

- `link_info.drive_serial`（整数=本地卷序列号，`GetVolumeInformationW` 取）才是手建时该写的字段，非 `local_volume_serial_number`；`drive_type` 字符串 `'Fixed (Hard disk)'`（非数字/非 `'FIXED'`）。
- `for_file` 生成的 lnk `link_info` 为 None 是正常的；**不要**依赖 `pylnk3.parse().link_info.path` 校验，改用 `shell_item_id_list.items` 项数 >0 证明有指向，或最权威地 `os.startfile(lnk)` 实测。

## Workflow（草图，待补实现）

1. 确认目标真实文件/目录存在（`Test-Path` / `os.path.exists`）。
2. 用 `scripts/make_lnk.py` 调 `pylnk3.for_file(target)` 生成 lnk 到**工作区临时目录**（不覆盖已存在文件）。
3. `shell cp -f <tmp.lnk> <用户开始菜单或桌面目标路径>`（shell 覆盖不被 safe-delete 拦）。
4. 校验：优先 `os.startfile(lnk)` 实测（Windows 解析成功才不报异常；可 `tasklist` 看目标 exe 进程真起——注意 `tasklist` stdout 含中文进程名，Python subprocess 需 `encoding='utf-8', errors='ignore'` 否则 UnicodeDecodeError）。

## Resources

### scripts/
- `make_lnk.py` —— 包裹 `pylnk3.for_file(target)` + `cp -f` + `os.startfile` 校验（草稿占位，待补）。

### references/
- （可选）`lnk_pitfalls.md` —— 完整坑位清单（COM/Add-Type/open-wb/LinkInfo/卷序列号），审阅后补。

### assets/
- 无。

---

**审阅提示**：用户确认痛点（快捷方式建不出来）后，再补 `make_lnk.py` 完整实现与 `references/lnk_pitfalls.md`；
并确认是否要支持「固定到任务栏」等进阶场景（任务栏 jumplist 机制不同，可能超草稿范围）。
