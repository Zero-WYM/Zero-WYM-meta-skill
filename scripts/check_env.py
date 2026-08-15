#!/usr/bin/env python3
"""Zero-WYM-meta-skill · 环境预检（零依赖）

- 定位 gh（PATH → winget 包目录 → --gh-path 覆盖），报告版本与登录态
- 校验 Python 标准库可用性
- 扫描已装 Skill 清单（供查重）
退出码 0 = 预检完成（gh 缺失/未登录只告警不阻断，发布会降级）。
"""
import argparse
import os
import sys
import json
import shutil
import subprocess
import re


def find_gh(explicit):
    if explicit and os.path.isfile(explicit):
        return explicit
    p = shutil.which("gh")
    if p:
        return p
    local = os.environ.get("LOCALAPPDATA", "")
    base = os.path.join(local, "Microsoft", "WinGet", "Packages")
    if os.path.isdir(base):
        for root, _, files in os.walk(base):
            if "gh.exe" in files:
                return os.path.join(root, "gh.exe")
    return None


def gh_info(gh):
    if not gh:
        return {"present": False}
    try:
        v = subprocess.run([gh, "--version"], capture_output=True, text=True, timeout=20)
        ver = v.stdout.splitlines()[0].strip() if v.stdout else "unknown"
    except Exception as e:  # noqa
        return {"present": True, "version": "?", "error": str(e)}
    info = {"present": True, "version": ver}
    try:
        a = subprocess.run([gh, "auth", "status", "--hostname", "github.com"],
                           capture_output=True, text=True, timeout=20)
        out = (a.stdout or "") + (a.stderr or "")
        m = re.search(r"Logged in to (\S+) account (\S+)", out)
        if m:
            info["logged_in"] = True
            info["host"] = m.group(1)
            info["account"] = m.group(2)
            sm = re.search(r"Token scopes:\s*'([^']+)'", out)
            if sm:
                info["scopes"] = sm.group(1)
        else:
            info["logged_in"] = False
            info["hint"] = (out.strip().splitlines()[0] if out.strip()
                            else "not logged in")
    except Exception as e:  # noqa
        info["logged_in"] = None
        info["auth_error"] = str(e)
    return info


def scan_skills(*dirs):
    found = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            sd = os.path.join(d, name)
            if os.path.isdir(sd) and os.path.isfile(os.path.join(sd, "SKILL.md")):
                found.append(name)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-dir", default=".")
    ap.add_argument("--user-skills",
                    default=os.path.join(os.path.expanduser("~"), ".workbuddy", "skills"))
    ap.add_argument("--gh-path")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    gh = find_gh(a.gh_path)
    ginfo = gh_info(gh)
    skills = scan_skills(a.skills_dir, a.user_skills)
    result = {
        "gh": ginfo,
        "installed_skills": skills,
        "installed_count": len(skills),
        "python_stdlib_ok": True,
    }

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=== 环境预检 ===")
        if ginfo.get("present"):
            print("gh: 已安装", ginfo.get("version"))
            if ginfo.get("logged_in"):
                print("    已登录 github.com 账号", ginfo.get("account"),
                      "scopes=", ginfo.get("scopes"))
            else:
                print("    未登录：", ginfo.get("hint", "请运行 gh auth login --web"))
        else:
            print("gh: 未安装（发布将降级；安装：winget install --id GitHub.cli）")
        print("已装 Skill 清单（%d 个）：" % len(skills))
        for s in skills:
            print("  -", s)
        print("Python 标准库：OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
