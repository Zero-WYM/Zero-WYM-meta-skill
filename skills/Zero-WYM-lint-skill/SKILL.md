---
name: Zero-WYM-lint-skill
keywords: [lint, 语法检查]
description: >-
  PowerShell 5.1 语法兼容性静态检查器。当用户要交付、保存或交给自己/他人运行的
  PowerShell 脚本（.ps1）时，扫描其中是否存在 PowerShell 7+ 专有语法
  （如 ?? ??= && || ?. ?[ &&= ||= 等），并给出 5.1 安全替代写法。
  用户 Windows 默认环境为 PowerShell 5.1，含 7+ 语法的脚本复制粘贴即抛 ParserError。
  此 skill 应在「生成/改写任意 .ps1 脚本」后、交付前自动触发。
agent_created: true
version: 1.0.0
status: draft
---

# PowerShell 5.1 Lint（草稿 · 待审阅）

> ⚠️ 本 skill 由自动化任务（痛点驱动推荐）反向生成，目前为**草稿骨架**，实现待用户审阅后补全。
> 记忆证据：`~/.workbuddy/MEMORY.md` 跨项目红线 ——
> 「Windows 默认 PowerShell 5.1（Windows 11 自带）。给 .ps1 脚本时禁止用 PS 7+ 专有语法：
> `??` `??=` `&&` `||` `?.` `?[` `&&=` `||=` 等一律禁用，否则用户复制粘贴跑就会 ParserError。」

## Overview

这是一个**编码标准 / 指南型** skill：在交付 PowerShell 脚本前做 5.1 兼容性静态检查，
把会触发 PS 5.1 `ParserError` 的 7+ 专有语法全部标红并给出可运行替代。

## When to Use

- 任何「生成 / 改写 / 保存 .ps1 脚本」的任务完成后，交付给用户前。
- 用户说「写个脚本给我」「存成 .ps1」「这个命令在 5.1 跑不了」时。
- 作为 `Zero-WYM-brain-skill` 红线的一部分：PS 脚本交付前必经 lint。

## Banned Syntax Table（PS 7+ → 5.1 安全替代）

| 7+ 语法 | 含义 | 5.1 安全替代 |
|---------|------|--------------|
| `$a ?? $b` | Null 合并 | `if ($null -eq $a) { $b } else { $a }` |
| `$a ??= $b` | Null 合并赋值 | `if ($null -eq $a) { $a = $b }` |
| `A && B` | 成功链 | `A; if ($?) { B }` |
| `A \|\| B` | 失败链 | `A; if (-not $?) { B }` |
| `$a?.Prop` | 空条件成员 | `if ($null -ne $a) { $a.Prop }` |
| `$a?['k']` | 空条件索引 | `if ($null -ne $a) { $a['k'] }` |
| `&&=` `\|\|=` | 链赋值 | `if ($?) { $x = $x -and $y }` 等展开 |
| `${env:...}` / `::new()` 等 | 部分 7+ 构造 | 用 5.1 等价写法 |

## Workflow

1. 读取待交付的 `.ps1` 内容（或用户粘贴的脚本块）。
2. 用 `scripts/lint_ps5.py` 逐行正则扫描上表语法，输出「行号 + 命中语法 + 替代建议」。
3. 将报告回给用户；若用户要求，直接产出 5.1 兼容改写版。
4. 给出统一调用形式：`powershell -ExecutionPolicy Bypass -File <绝对路径>`（不切目录、零参数、绝对路径）。

## Resources

### scripts/
- `lint_ps5.py` —— 正则静态检查器（草稿版，仅做语法扫描，未做 AST 解析）。

> 实现待补：当前为匹配 `Banned Syntax Table` 的正则扫描；后续可升级为 `System.Management.Automation.Language` AST 解析以降误报。

### references/
- （可选）`ps5_compat.md` —— 完整的 PS 5.1 vs 7 差异清单，审阅后补。

### assets/
- 无。

---

**审阅提示**：用户确认痛点（脚本在 PS 5.1 报错）后，再补 `lint_ps5.py` 完整实现与 `references/ps5_compat.md`。
