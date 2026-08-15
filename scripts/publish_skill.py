#!/usr/bin/env python3
"""Zero-WYM-meta-skill · 发布链路（零依赖，安全优先）

前置：gh 已装且 gh auth login 已登录（未满足则自动降级）。
链路：密钥扫描 -> 特性分支 -> commit -> push -> PR（不直推主分支）-> Release。

硬规则：
- 默认 --dry-run：只打印将执行的命令，不写入远端。去掉 --dry-run 才真实执行。
- 密钥扫描不过 = 阻断。
- 禁止直推主分支，所有内容走 PR。
- 发布是**对外不可逆写操作**，真实执行需用户显式去掉 --dry-run 并确认。

本脚本在本包自检时仅以 --dry-run 运行；实际 push/PR/Release 未在本会话执行，
交付报告中标注"未实测/需你确认后运行"。
"""
import argparse
import os
import sys
import re
import json
import shutil
import subprocess

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[0-9A-Za-z]{36,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,}"),
    re.compile(r"(?i)(?:api[_-]?key|secret|token|password|passwd|access[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?"),
]
SKIP_DIRS = {".git", "node_modules", "__pycache__"}


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


def scan_secrets(skill_dir):
    hits = []
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            fp = os.path.join(root, f)
            try:
                with open(fp, encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        for pat in SECRET_PATTERNS:
                            if pat.search(line):
                                hits.append("%s:%d" % (os.path.relpath(fp, skill_dir), i))
                                break
            except Exception:  # noqa
                pass
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=".")
    ap.add_argument("--repo", required=True, help="Owner/Repo")
    ap.add_argument("--version", default="v0.1.0")
    ap.add_argument("--gh-path")
    ap.add_argument("--branch")
    ap.add_argument("--dry-run", action="store_true", default=True,
                    help="只打印命令，不写入远端（默认开启）")
    ap.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    a = ap.parse_args()

    gh = find_gh(a.gh_path)
    if not gh:
        print("gh 未安装/未找到。发布降级为本地打包：")
        print("  1) 安装: winget install --id GitHub.cli")
        print("  2) 登录: gh auth login --web")
        print("  3) 登录后重新运行（去掉 --dry-run）")
        sys.exit(2)

    r = subprocess.run([gh, "auth", "status", "--hostname", "github.com"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("gh 未登录。请运行 gh auth login --web 后重试。")
        sys.exit(2)

    # 密钥扫描（必须零命中）
    hits = scan_secrets(a.skill_dir)
    if hits:
        print("密钥扫描未通过，阻断发布。命中：")
        for h in hits:
            print("  -", h)
        sys.exit(1)
    print("密钥扫描：零命中 OK")

    skill_name = os.path.basename(os.path.abspath(a.skill_dir))
    branch = a.branch or ("feature/publish-" + skill_name)
    steps = [
        "git init  (若 %s 尚不是仓库)" % a.skill_dir,
        "git add -A",
        "git commit -m 'publish %s'" % a.version,
        "git checkout -b %s" % branch,
        "git remote add origin https://github.com/%s.git  (若不存在)" % a.repo,
        "git push -u origin %s" % branch,
        "gh pr create --base main --head %s --title 'Publish %s' --body '...'"
        % (branch, skill_name),
        "# 合并 PR 后：",
        "gh release create %s --repo %s --title %s --notes '...'"
        % (a.version, a.repo, a.version),
    ]

    print("=== 发布链路（gh 已登录）===")
    if a.dry_run:
        print("[DRY-RUN] 以下为将执行的命令，未实际写入远端：")
        for s in steps:
            print("  ", s)
        print("去掉 --dry-run 并显式确认后，才会真正 push/PR/Release。")
        sys.exit(0)

    # ---- 真实执行（仅在用户显式 --no-dry-run 时到达）----
    print("WARNING: 真实发布将写入你的 GitHub（对外不可逆）。")
    cwd = os.path.abspath(a.skill_dir)
    # git init（若需要）
    if not os.path.isdir(os.path.join(cwd, ".git")):
        subprocess.run(["git", "init"], cwd=cwd, check=True)
    subprocess.run(["git", "add", "-A"], cwd=cwd, check=True)
    subprocess.run(["git", "commit", "-m", "publish %s" % a.version], cwd=cwd)
    # 分支
    cur = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                         cwd=cwd, capture_output=True, text=True).stdout.strip()
    if cur != branch:
        subprocess.run(["git", "checkout", "-b", branch], cwd=cwd, check=True)
    # remote
    rem = subprocess.run(["git", "remote"], cwd=cwd, capture_output=True, text=True).stdout
    if "origin" not in rem:
        subprocess.run(["git", "remote", "add", "origin",
                        "https://github.com/%s.git" % a.repo], cwd=cwd, check=True)
    subprocess.run(["git", "push", "-u", "origin", branch], cwd=cwd, check=True)
    subprocess.run(["gh", "pr", "create", "--base", "main", "--head", branch,
                   "--title", "Publish %s" % skill_name, "--body",
                   "Auto-published by Zero-WYM-meta-skill."], check=True)
    print("PR 已创建。合并后运行：")
    print("  gh release create %s --repo %s --title %s --notes '...'"
          % (a.version, a.repo, a.version))
    sys.exit(0)


if __name__ == "__main__":
    main()
