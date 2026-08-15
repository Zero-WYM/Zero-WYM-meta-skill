#!/usr/bin/env python3
"""Obsidian export/ → 飞书知识库（新增 + 旧笔记/附件更新回推）。

- 读取 manifest.json 作为本地文件清单与 sha256
- 维护 feishu_remote_map.json 记录远程 node_token / obj_token / sha256
- 读取 feishu_sync_failures.json 跳过已知超限文件
- 默认执行；加 --dry-run 仅打印计划
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
EXPORT_DIR = SCRIPT_DIR / "export"
MANIFEST_PATH = SCRIPT_DIR / "manifest.json"
REMOTE_MAP_PATH = SCRIPT_DIR / "feishu_remote_map.json"
FAILURES_PATH = SCRIPT_DIR / "feishu_sync_failures.json"

# 飞书 wiki 空间配置
SPACE_ID = "7672790838467906514"
SPACE_NAME = "第二大脑"

# 附件扩展名（与 normalize.py 共享）
ATTACHMENT_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".mp4", ".mov", ".webm", ".mkv", ".avi",
    ".mp3", ".wav", ".ogg", ".m4a", ".flac",
    ".pdf", ".docx", ".pptx", ".xlsx", ".zip", ".epub",
}

LARK_CLI = os.environ.get("LARK_CLI", r"C:\Users\33754\.workbuddy\binaries\node\cli-connector-packages\lark-cli.cmd")
SIZE_20MB = 20 * 1024 * 1024


def load_json(path: Path) -> dict[str, Any]:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_lark(args: list[str], dry_run: bool = False) -> dict[str, Any]:
    """运行 lark-cli 命令并解析 JSON 输出。"""
    cmd = [LARK_CLI] + args
    if dry_run and "--dry-run" not in args:
        cmd.append("--dry-run")
    print(f"[lark] {' '.join(cmd)}")
    if dry_run:
        return {"dry_run": True, "ok": True}
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=SCRIPT_DIR)
    if result.returncode != 0:
        # 尝试解析错误 JSON
        text = result.stdout or result.stderr
        try:
            err = json.loads(text)
        except Exception:
            err = {"raw": text}
        raise RuntimeError(f"lark-cli failed: {err}")
    text = result.stdout.strip()
    if not text:
        return {"ok": True}
    try:
        return json.loads(text)
    except Exception:
        return {"ok": True, "raw": text}


def path_to_title(rel: str) -> str:
    return Path(rel).stem


def path_parts(rel: str) -> list[str]:
    return Path(rel).parts


def list_wiki_nodes(parent_token: str | None = None) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    page_token = ""
    while True:
        args = ["wiki", "+node-list", "--space-id", SPACE_ID, "--page-size", "50"]
        if parent_token:
            args += ["--parent-node-token", parent_token]
        if page_token:
            args += ["--page-token", page_token]
        resp = run_lark(args)
        data = resp.get("data", {})
        nodes.extend(data.get("nodes", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return nodes


def build_remote_tree() -> dict[str, dict[str, Any]]:
    """构建路径 → 节点 映射。路径格式：folder1/folder2/title（不含扩展名）。"""
    tree: dict[str, dict[str, Any]] = {}

    def walk(parent_token: str | None, parent_path: str) -> None:
        nodes = list_wiki_nodes(parent_token)
        for node in nodes:
            title = node["title"]
            node_path = f"{parent_path}/{title}" if parent_token else title
            tree[node_path] = node
            if node.get("has_child"):
                walk(node["node_token"], node_path)

    walk(None, "")
    return tree


def ensure_remote_folder(
    parent_token: str | None,
    title: str,
    dry_run: bool,
    dry_created_paths: set[str],
    current_path: str,
) -> dict[str, Any]:
    """确保远程文件夹存在；不存在则创建 docx 容器节点。"""
    if dry_run and (current_path in dry_created_paths or any(current_path.startswith(p + "/") for p in dry_created_paths)):
        # dry-run 中，该路径或其祖先已被标记为新建，返回占位节点，不再发起真实请求
        return {"node_token": f"DRY-{current_path}", "title": title, "has_child": True, "dry_run": True}

    nodes = list_wiki_nodes(parent_token)
    for node in nodes:
        if node["title"] == title and node.get("has_child"):
            return node
    # 创建容器节点
    args = [
        "wiki", "+node-create",
        "--space-id", SPACE_ID,
        "--title", title,
        "--obj-type", "docx",
    ]
    if parent_token:
        args += ["--parent-node-token", parent_token]
    resp = run_lark(args, dry_run=dry_run)
    if dry_run:
        dry_created_paths.add(current_path)
        return {"node_token": f"DRY-{current_path}", "title": title, "has_child": True, "dry_run": True}
    node = resp.get("data", {})
    node["has_child"] = True
    return node


def get_or_create_parent(
    rel: str,
    remote_tree: dict[str, dict[str, Any]],
    dry_run: bool,
    dry_created_paths: set[str],
) -> str | None:
    """根据本地相对路径返回父节点 token；必要时创建中间文件夹。"""
    parts = path_parts(rel)
    if len(parts) <= 1:
        return None

    current_token: str | None = None
    current_path = ""
    for folder in parts[:-1]:
        current_path = f"{current_path}/{folder}" if current_path else folder
        if current_path in remote_tree:
            current_token = remote_tree[current_path]["node_token"]
        else:
            node = ensure_remote_folder(current_token, folder, dry_run, dry_created_paths, current_path)
            current_token = node["node_token"]
            remote_tree[current_path] = node
    return current_token


def relative_file_arg(local_path: Path) -> str:
    """lark-cli --file 要求 cwd 内的相对路径，返回 export/... 格式。"""
    try:
        rel = local_path.relative_to(SCRIPT_DIR)
    except ValueError:
        rel = local_path
    return rel.as_posix()


def upload_md(rel: str, local_path: Path, parent_token: str | None, dry_run: bool) -> dict[str, str]:
    """导入 markdown 为 docx 并移动到 wiki 父节点。"""
    title = path_to_title(rel)
    args = [
        "drive", "+import",
        "--file", relative_file_arg(local_path),
        "--type", "docx",
        "--name", title,
    ]
    resp = run_lark(args, dry_run=dry_run)
    if dry_run:
        return {"node_token": f"DRY-MD-{rel}", "obj_token": f"DRY-OBJ-{rel}"}
    obj_token = resp.get("data", {}).get("file", {}).get("token") or resp.get("data", {}).get("token")
    if not obj_token:
        raise RuntimeError(f"导入失败，无 obj_token: {resp}")

    # 移动到 wiki
    move_args = [
        "wiki", "+move",
        "--obj-token", obj_token,
        "--obj-type", "docx",
        "--target-space-id", SPACE_ID,
    ]
    if parent_token:
        move_args += ["--target-parent-token", parent_token]
    move_resp = run_lark(move_args, dry_run=dry_run)
    node_token = move_resp.get("data", {}).get("node_token")
    if not node_token:
        # 尝试从 data 直接取
        node_token = move_resp.get("data", {}).get("node_token") or obj_token
    return {"node_token": node_token, "obj_token": obj_token}


def update_md(rel: str, local_path: Path, node_info: dict[str, Any], parent_token: str | None, dry_run: bool) -> dict[str, str]:
    """更新已有 markdown：删除旧 wiki 节点，重新导入并移动。"""
    node_token = node_info["node_token"]
    # 删除旧节点
    run_lark(["wiki", "+node-delete", "--node-token", node_token], dry_run=dry_run)
    return upload_md(rel, local_path, parent_token, dry_run)


def upload_attachment(rel: str, local_path: Path, parent_token: str | None, dry_run: bool, existing_file_token: str | None = None) -> dict[str, str]:
    """上传附件到 wiki；如提供 file_token 则覆盖。"""
    args = ["drive", "+upload", "--file", relative_file_arg(local_path)]
    if existing_file_token:
        args += ["--file-token", existing_file_token]
    if parent_token:
        args += ["--wiki-token", parent_token]
    resp = run_lark(args, dry_run=dry_run)
    if dry_run:
        return {"file_token": f"DRY-FILE-{rel}"}
    file_token = resp.get("data", {}).get("file_token") or existing_file_token
    return {"file_token": file_token}


def bootstrap_remote_map() -> dict[str, Any]:
    """根据当前 manifest 与远程节点路径，初始化 feishu_remote_map.json（不修改远程）。"""
    manifest = load_json(MANIFEST_PATH)
    remote_tree = build_remote_tree()
    remote_map: dict[str, Any] = load_json(REMOTE_MAP_PATH)
    matched = 0
    unmatched = 0

    for rel, info in sorted(manifest.get("files", {}).items()):
        title = path_to_title(rel)
        match_path_parts = path_parts(rel)[:-1] + (title,)
        match_path = "/".join(match_path_parts)
        remote_node = remote_tree.get(match_path)
        if not remote_node:
            unmatched += 1
            continue
        local_sha = info.get("sha256", "")
        ext_lower = Path(rel).suffix.lower()
        if ext_lower == ".md" and remote_node.get("obj_type") == "docx":
            remote_map[rel] = {
                "node_token": remote_node["node_token"],
                "obj_token": remote_node["obj_token"],
                "sha256": local_sha,
                "type": "docx",
            }
            matched += 1
        elif remote_node.get("obj_type") == "file":
            remote_map[rel] = {
                "file_token": remote_node["obj_token"],
                "sha256": local_sha,
                "type": "file",
            }
            matched += 1
        else:
            unmatched += 1

    save_json(REMOTE_MAP_PATH, remote_map)
    return {
        "matched": matched,
        "unmatched": unmatched,
        "total": len(manifest.get("files", {})),
    }


def sync(dry_run: bool = False) -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    remote_map = load_json(REMOTE_MAP_PATH)
    failures = load_json(FAILURES_PATH)
    failure_paths = set(failures.keys())

    remote_tree = build_remote_tree()
    dry_created_paths: set[str] = set()

    stats = {
        "md_created": 0,
        "md_updated": 0,
        "md_unchanged": 0,
        "attachment_created": 0,
        "attachment_updated": 0,
        "attachment_unchanged": 0,
        "skipped_failure": 0,
        "skipped_size": 0,
        "errors": [],
    }

    new_remote_map: dict[str, Any] = {}

    for rel, info in sorted(manifest.get("files", {}).items()):
        local_path = EXPORT_DIR / rel
        if not local_path.exists():
            continue

        if rel in failure_paths:
            stats["skipped_failure"] += 1
            continue

        local_sha = info.get("sha256", "")
        ext_lower = Path(rel).suffix.lower()
        is_md = ext_lower == ".md"

        # 超过 20MB 的附件直接记录失败
        if not is_md and local_path.stat().st_size > SIZE_20MB:
            stats["skipped_size"] += 1
            failures[rel] = {"reason": "size > 20MB", "size": local_path.stat().st_size, "sha256": local_sha}
            continue

        parent_node = get_or_create_parent(rel, remote_tree, dry_run, dry_created_paths)

        # 构建用于匹配的路径 key（无扩展名）
        title = path_to_title(rel)
        match_path_parts = path_parts(rel)[:-1] + (title,)
        match_path = "/".join(match_path_parts)

        remote_node = remote_tree.get(match_path)
        remote_entry = remote_map.get(rel, {})
        remote_sha = remote_entry.get("sha256", "")

        try:
            if is_md:
                if remote_node and remote_node.get("obj_type") == "docx":
                    if remote_sha == local_sha and not dry_run:
                        stats["md_unchanged"] += 1
                        new_remote_map[rel] = remote_entry
                    else:
                        result = update_md(rel, local_path, remote_node, parent_node, dry_run)
                        stats["md_updated"] += 1
                        new_remote_map[rel] = {
                            "node_token": result["node_token"],
                            "obj_token": result["obj_token"],
                            "sha256": local_sha,
                            "type": "docx",
                        }
                else:
                    result = upload_md(rel, local_path, parent_node, dry_run)
                    stats["md_created"] += 1
                    new_remote_map[rel] = {
                        "node_token": result["node_token"],
                        "obj_token": result["obj_token"],
                        "sha256": local_sha,
                        "type": "docx",
                    }
            else:
                # 附件
                if remote_node and remote_node.get("obj_type") == "file":
                    if remote_sha == local_sha and not dry_run:
                        stats["attachment_unchanged"] += 1
                        new_remote_map[rel] = remote_entry
                    else:
                        result = upload_attachment(rel, local_path, parent_node, dry_run, remote_entry.get("file_token"))
                        stats["attachment_updated"] += 1
                        new_remote_map[rel] = {
                            "file_token": result["file_token"],
                            "sha256": local_sha,
                            "type": "file",
                        }
                else:
                    result = upload_attachment(rel, local_path, parent_node, dry_run)
                    stats["attachment_created"] += 1
                    new_remote_map[rel] = {
                        "file_token": result["file_token"],
                        "sha256": local_sha,
                        "type": "file",
                    }
        except Exception as e:
            stats["errors"].append({"path": rel, "error": str(e)})

    if not dry_run:
        save_json(REMOTE_MAP_PATH, new_remote_map)
        save_json(FAILURES_PATH, failures)

    return {
        "space_id": SPACE_ID,
        "space_name": SPACE_NAME,
        "dry_run": dry_run,
        "stats": stats,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="仅打印计划，不执行写入")
    parser.add_argument("--bootstrap", action="store_true", help="仅根据当前 manifest 与远程节点初始化 feishu_remote_map.json")
    args = parser.parse_args()
    if args.bootstrap:
        result = bootstrap_remote_map()
    else:
        result = sync(dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if isinstance(result, dict) and "errors" in result and result["errors"]:
        sys.exit(1)
