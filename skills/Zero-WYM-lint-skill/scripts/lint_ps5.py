#!/usr/bin/env python3
# Zero-WYM-lint-skill 草稿版检查器（DRAFT）
# 扫描 .ps1 文本，标出 PowerShell 7+ 专有语法。
# 完整实现待用户审阅后补全（当前仅正则扫描，非 AST 解析；可能有误报）。
import re
import sys

BANNED = [
    (r"\?\?=", "??=  null 合并赋值"),
    (r"\?\?", "??  null 合并"),
    (r"\?\s*\[", "?[  null 条件索引"),
    (r"\?\s*\.", "?.  null 条件成员"),
    (r"&&=\s*", "&&= 链赋值"),
    (r"\|\|=\s*", "||= 链赋值"),
    (r"(?<![&\|])\s*&&\s*(?![&])", "&&  成功链 (PS7+)"),
    (r"(?<![&\|])\s*\|\|\s*(?![|])", "||  失败链 (PS7+)"),
]


def lint(text):
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        for pat, label in BANNED:
            if re.search(pat, line):
                hits.append((i, label, line.strip()))
    return hits


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("DRAFT: usage: lint_ps5.py <file.ps1>")
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        hits = lint(f.read())
    if not hits:
        print("OK: 未检测到 PS7+ 专有语法。")
    else:
        for ln, label, snippet in hits:
            print(f"L{ln}: {label} -> {snippet}")
        sys.exit(1)
