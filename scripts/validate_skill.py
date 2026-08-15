#!/usr/bin/env python3
"""Zero-WYM-meta-skill · 包结构校验（零依赖）

校验项：
- SKILL.md 存在
- frontmatter 合法（自写解析器，支持 description 折叠块）
- name / description 非空
- 体积预算 SKILL.md <= 14KB（上下文预算）
- 无嵌套 SKILL.md（防止子目录示例被 Agent 误当独立技能加载）
退出码 0 = 全部通过，1 = 存在失败。
"""
import argparse
import os
import sys
import re

MAX_BYTES = 14 * 1024


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None, "缺少 frontmatter（文件未以 --- 开头）"
    end = text.find("\n---", 3)
    if end == -1:
        return None, "frontmatter 未闭合"
    block = text[3:end].strip("\n")
    fm = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if val in (">-", "|", "|-"):
                val_lines = []
                i += 1
                while i < len(lines) and (lines[i].startswith(" ") or lines[i].strip() == ""):
                    if lines[i].strip():
                        val_lines.append(lines[i].strip())
                    i += 1
                fm[key] = " ".join(val_lines)
                continue
            fm[key] = val
        i += 1
    return fm, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=".")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    sd = a.skill_dir
    skill_md = os.path.join(sd, "SKILL.md")
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    if not os.path.isfile(skill_md):
        add("SKILL.md 存在", False, "未找到 " + skill_md)
        report(checks, a.json, False)
        sys.exit(1)

    size = os.path.getsize(skill_md)
    add("SKILL.md 体积 <=14KB", size <= MAX_BYTES,
        "%d 字节 (%.1fKB)" % (size, size / 1024.0))

    text = open(skill_md, encoding="utf-8").read()
    fm, err = parse_frontmatter(text)
    if err:
        add("frontmatter 合法", False, err)
    else:
        add("frontmatter 合法", True, "解析成功")
        name = fm.get("name", "").strip('"').strip()
        desc = fm.get("description", "").strip('"').strip()
        add("name 非空", bool(name), "name=%r" % name)
        add("description 非空", bool(desc), "len=%d" % len(desc))

    # 嵌套 SKILL.md 检测
    nested = []
    abs_main = os.path.abspath(skill_md)
    for root, _, files in os.walk(sd):
        for f in files:
            if f == "SKILL.md":
                fp = os.path.abspath(os.path.join(root, f))
                if fp != abs_main:
                    nested.append(os.path.relpath(fp, sd))
    add("无嵌套 SKILL.md", len(nested) == 0,
        "嵌套:" + (", ".join(nested) if nested else "无"))

    ok = all(c["pass"] for c in checks)
    report(checks, a.json, ok)
    sys.exit(0 if ok else 1)


def report(checks, json_mode, ok):
    if json_mode:
        print(json.dumps({"checks": checks, "all_pass": ok},
                         ensure_ascii=False, indent=2))
    else:
        print("=== 包结构校验 ===")
        for c in checks:
            print("[%s] %s: %s" % ("PASS" if c["pass"] else "FAIL",
                                   c["check"], c["detail"]))
        if ok is not None:
            print("结果:", "全部通过" if ok else "存在失败")


if __name__ == "__main__":
    main()
