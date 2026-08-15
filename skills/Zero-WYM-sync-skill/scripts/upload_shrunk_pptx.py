#!/usr/bin/env python3
"""把 shrink_pptx.py 产出的压缩件上传到飞书对应 wiki 节点。

- 逻辑与 sync_to_feishu.py 的 md 路径一致：lark-cli import → wiki move
- 通过 feishu_remote_map.json 找到原件对应的 wiki 节点，把压缩件覆盖/移动到该节点
- 原件（shrunk_from）默认不再重推

用法：
  python upload_shrunk_pptx.py <shrunk.pptx> --node <wiki_node_id>
  python upload_shrunk_pptx.py <shrunk.pptx>   # 自动从 shrunk_from 推算原件并查 map
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
MAP_PATH = SCRIPT_DIR / "feishu_remote_map.json"


def find_lark_cli() -> str | None:
    return shutil.which("lark-cli") or shutil.which("lark-cli.cmd")


def load_map() -> dict[str, Any]:
    if MAP_PATH.exists():
        with MAP_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def resolve_node(shrunk: Path, node_arg: str | None) -> str | None:
    if node_arg:
        return node_arg
    try:
        with zipfile.ZipFile(shrunk) as z:
            if "customProps/shrunk.json" in z.namelist():
                meta = json.loads(z.read("customProps/shrunk.json"))
                orig = meta.get("shrunk_from")
                if orig:
                    m = load_map()
                    entry = m.get("files", {}).get(orig) or m.get(orig)
                    if entry and entry.get("wiki_node_id"):
                        return entry["wiki_node_id"]
    except Exception as e:  # noqa: BLE001
        print(f"[warn] 无法从 shrunk_from 推算节点: {e}")
    return None


def upload(shrunk: Path, node_id: str) -> int:
    cli = find_lark_cli()
    if not cli:
        print("[ERROR] 未找到 lark-cli（飞书上传 CLI）。请确认已安装并在 PATH。")
        return 2
    r1 = subprocess.run([cli, "drive", "+import", str(shrunk)],
                        capture_output=True, text=True)
    if r1.returncode != 0:
        print(f"[ERROR] lark-cli import 失败:\n{r1.stderr}")
        return 1
    r2 = subprocess.run([cli, "wiki", "+move", "--node", node_id, str(shrunk)],
                        capture_output=True, text=True)
    if r2.returncode != 0:
        print(f"[ERROR] lark-cli wiki move 失败:\n{r2.stderr}")
        return 1
    print(f"[ok] 已上传压缩件 {shrunk.name} 到 wiki 节点 {node_id}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="上传压缩 pptx 到飞书 wiki 节点")
    ap.add_argument("shrunk", help="shrink_pptx.py 产出的 *_shrunk.pptx")
    ap.add_argument("--node", help="目标 wiki 节点 id（缺省则从 shrunk_from 反查）")
    args = ap.parse_args()
    shrunk = Path(args.shrunk)
    if not shrunk.exists():
        print(f"[ERROR] 找不到压缩件: {shrunk}")
        return 1
    node = resolve_node(shrunk, args.node)
    if not node:
        print("[ERROR] 无法确定目标 wiki 节点：请显式传 --node，或确保 feishu_remote_map.json 含原件映射。")
        return 1
    return upload(shrunk, node)


if __name__ == "__main__":
    sys.exit(main())
