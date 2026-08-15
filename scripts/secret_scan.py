#!/usr/bin/env python3
"""Zero-WYM-meta-skill · 密钥泄露扫描（零依赖）

递归扫描 skill 目录（跳过 .git/node_modules/__pycache__），用正则匹配常见
凭据形态。为安全，命中值只打印类型与前缀截断，绝不回显完整密钥。
退出码 0 = 零命中，1 = 有命中。
"""
import argparse
import os
import sys
import json
import re

PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_token", re.compile(r"gh[pousr]_[0-9A-Za-z]{36,}")),
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("slack_token", re.compile(r"xox[baprs]-[0-9A-Za-z\-]{10,}")),
    ("generic_credential", re.compile(
        r"(?i)(?:api[_-]?key|secret|token|password|passwd|access[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?")),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill-dir", default=".")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    hits = []
    for root, dirs, files in os.walk(a.skill_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            fp = os.path.join(root, f)
            try:
                with open(fp, encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        for name, pat in PATTERNS:
                            m = pat.search(line)
                            if m:
                                snippet = m.group(0)[:12] + "..."
                                hits.append({
                                    "file": os.path.relpath(fp, a.skill_dir),
                                    "line": i,
                                    "type": name,
                                    "match_prefix": snippet,
                                })
                                break
            except Exception:  # noqa
                pass

    ok = len(hits) == 0
    if a.json:
        print(json.dumps({"secret_free": ok, "hits": hits},
                         ensure_ascii=False, indent=2))
    else:
        print("=== 密钥扫描 ===")
        if ok:
            print("零命中：无 api_key/token/私钥/凭据泄露")
        else:
            for h in hits:
                print("[HIT] %s:%d %s -> %s"
                      % (h["file"], h["line"], h["type"], h["match_prefix"]))
            print("共 %d 处命中" % len(hits))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
