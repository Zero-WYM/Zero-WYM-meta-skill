#!/usr/bin/env python3
"""Zero-WYM-meta-skill · 安装（零依赖，安全优先）

流程：读源 SKILL.md 的 name -> 目标 = target/name
- 目标已存在：先改名备份（不删除）
- 复制源到目标（copytree）
- 验证目标 SKILL.md 存在
- 失败则回滚到备份
绝不静默覆盖、绝不删除用户文件。
退出码 0 = 安装成功，1 = 失败（已回滚）。
"""
import argparse
import os
import sys
import re
import time
import shutil


def parse_name(skill_dir):
    md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(md):
        return None
    t = open(md, encoding="utf-8").read()
    m = re.search(r"name:\s*\"?([^\"\n]+)\"?", t)
    return m.group(1).strip().strip('"') if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", required=True)
    ap.add_argument("--target",
                    default=os.path.join(os.path.expanduser("~"), ".workbuddy", "skills"))
    ap.add_argument("--name")
    a = ap.parse_args()

    name = a.name or parse_name(a.skill_dir)
    if not name:
        print("无法确定 Skill 名称（SKILL.md 缺少 name）")
        sys.exit(1)

    src = os.path.abspath(a.skill_dir)
    target_root = os.path.abspath(a.target)
    dest = os.path.join(target_root, name)

    if not os.path.isdir(src):
        print("源目录不存在:", src)
        sys.exit(1)
    if not os.path.isdir(target_root):
        os.makedirs(target_root, exist_ok=True)

    backup = None
    if os.path.exists(dest):
        backup = dest + ".bak." + time.strftime("%Y%m%d-%H%M%S")
        shutil.move(dest, backup)
        print("已备份原目录 ->", backup)

    try:
        shutil.copytree(src, dest)
        assert os.path.isfile(os.path.join(dest, "SKILL.md")), "SKILL.md 缺失"
        print("已安装 ->", dest)
        print("安装成功")
        sys.exit(0)
    except Exception as e:  # noqa
        print("安装失败，回滚:", e)
        if backup and os.path.exists(backup):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.move(backup, dest)
            print("已回滚到备份")
        sys.exit(1)


if __name__ == "__main__":
    main()
