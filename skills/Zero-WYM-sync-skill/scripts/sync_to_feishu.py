#!/usr/bin/env python3
"""Obsidian export/ → 飞书知识库（新增 + 旧笔记/附件更新回推）。

- 读取 manifest.json 作为本地文件清单与 sha256
- 维护 feishu_remote_map.json 记录远程 node_token / obj_token / sha256
- 绑定双写（v1.2）：同时落 vault .workbuddy/bindings.json 与源 .md frontmatter（feishu_binding），三源任一边丢失可恢复
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
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
# 导出目录：默认 SCRIPT_DIR/export；若设 OBSIDIAN_SYNC_EXPORT_DIR 则与 normalize.py 共用该路径（两侧一致）
EXPORT_DIR = Path(os.environ.get("OBSIDIAN_SYNC_EXPORT_DIR", str(SCRIPT_DIR / "export")))
MANIFEST_PATH = EXPORT_DIR / "manifest.json"
REMOTE_MAP_PATH = SCRIPT_DIR / "feishu_remote_map.json"
FAILURES_PATH = SCRIPT_DIR / "feishu_sync_failures.json"
PENDING_DELETES_PATH = SCRIPT_DIR / "feishu_pending_deletes.json"

# 绑定双写（对齐 Obsidian-飞书同步架构方案.md 决策4）：三源镜像
#   ① feishu_remote_map.json（沿用，scripts 内）
#   ② D:/第二大脑/.workbuddy/bindings.json（vault 内，跨设备随库走）
#   ③ 源 .md frontmatter 的 feishu_binding
VAULT_DIR = Path(r"D:/第二大脑")
VAULT_BINDINGS_PATH = VAULT_DIR / ".workbuddy" / "bindings.json"

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


# ---------- 绑定双写（三源镜像，对齐 .md 决策4） ----------

def load_vault_bindings() -> dict[str, Any]:
    return load_json(VAULT_BINDINGS_PATH)


def save_vault_bindings(data: dict[str, Any]) -> None:
    VAULT_BINDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_json(VAULT_BINDINGS_PATH, data)


def vault_md_path(rel: str) -> Path:
    """源 .md 路径：manifest 的 rel 对应 VAULT_DIR 下同源文件。"""
    return VAULT_DIR / rel


def read_frontmatter_binding(vault_md: Path) -> dict[str, Any] | None:
    """读取 .md frontmatter 的 feishu_binding 字段（单源恢复）。"""
    if not vault_md.exists():
        return None
    try:
        text = vault_md.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None  # 非 UTF-8 源文件：跳过 frontmatter 双写恢复，避免崩溃
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not m:
        return None
    for line in m.group(1).splitlines():
        if line.startswith("feishu_binding:"):
            raw = line.split(":", 1)[1].strip()
            try:
                return json.loads(raw)
            except Exception:
                return None
    return None


def write_frontmatter_binding(vault_md: Path, binding: dict[str, Any]) -> None:
    """在 .md frontmatter 写入/更新 feishu_binding（缺失则补 --- 块）。"""
    if not vault_md.exists():
        return
    binding_line = f"feishu_binding: {json.dumps(binding, ensure_ascii=False)}"
    try:
        text = vault_md.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return  # 非 UTF-8 源文件：不改写，避免损坏；该文件仍正常同步（内容取自 export 副本）
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if m:
        kept = [ln for ln in m.group(1).splitlines() if not ln.startswith("feishu_binding:")]
        kept.append(binding_line)
        new_text = "---\n" + "\n".join(kept) + "\n---\n" + text[m.end():]
    else:
        new_text = f"---\n{binding_line}\n---\n" + text
    vault_md.write_text(new_text, encoding="utf-8")


def resolve_binding(rel: str, remote_map: dict, vault_bindings: dict, vault_md: Path) -> tuple[dict | None, str | None]:
    """三源恢复顺序：remote_map → vault_bindings → .md frontmatter。返回 (entry, source)。"""
    entry = remote_map.get(rel)
    if entry and entry.get("node_token"):
        return entry, "remote_map"
    entry = vault_bindings.get(rel)
    if entry and entry.get("node_token"):
        return entry, "vault_bindings"
    entry = read_frontmatter_binding(vault_md)
    if entry and entry.get("node_token"):
        return entry, "frontmatter"
    return None, None


def record_binding(rel: str, node_token: str, doc_token: str, typ: str, local_sha: str,
                   vault_bindings: dict[str, Any], dry_run: bool = False, write_frontmatter: bool = True) -> dict[str, Any]:
    """内存态写入统一绑定（vault_bindings）；real 模式下落盘 vault bindings.json 并（docx）写 .md frontmatter。
    返回统一绑定 dict 供 new_remote_map 复用。"""
    binding = {
        "node_token": node_token,
        "doc_token": doc_token,
        "space_id": SPACE_ID,
        "type": typ,
        "sha256": local_sha,
        "last_sync_time": datetime.now().astimezone().isoformat(),
    }
    vault_bindings[rel] = binding
    if not dry_run and typ == "docx" and write_frontmatter:
        write_frontmatter_binding(vault_md_path(rel), binding)
    return binding


def run_lark(args: list[str], dry_run: bool = False, timeout: int = 180) -> dict[str, Any]:
    """运行 lark-cli 命令并解析 JSON 输出。timeout 防止单条调用挂起拖死整个 sync（死锁根因修复）。"""
    cmd = [LARK_CLI] + args
    if dry_run and "--dry-run" not in args:
        cmd.append("--dry-run")
    print(f"[lark] {' '.join(cmd)}")
    if dry_run:
        return {"dry_run": True, "ok": True}
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", cwd=SCRIPT_DIR, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"lark-cli timed out after {timeout}s: {' '.join(cmd)}")
    print(f"[run] rc={result.returncode} op={' '.join(args[:2])}")
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


def remote_node_for(rel: str, remote_tree: dict[str, Any]) -> dict[str, Any] | None:
    """按 manifest rel 在远程树查找节点。

    md(docx) 节点 title 为 stem；附件(file) 节点 title 含扩展名（如 xxx.jpg），
    所以同时尝试 stem 与 含扩展名 两种 key，避免附件被误判为"新建"而重复上传。
    """
    parts = path_parts(rel)
    stem_key = "/".join(parts[:-1] + (Path(rel).stem,))
    ext_key = "/".join(parts[:-1] + (Path(rel).name,))
    return remote_tree.get(stem_key) or remote_tree.get(ext_key)


def path_parts(rel: str) -> list[str]:
    return Path(rel).parts


def list_wiki_nodes(parent_token: str | None = None, dry_run: bool = False) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    page_token = ""
    while True:
        args = ["wiki", "+node-list", "--space-id", SPACE_ID, "--page-size", "50"]
        if parent_token:
            args += ["--parent-node-token", parent_token]
        if page_token:
            args += ["--page-token", page_token]
        resp = run_lark(args, dry_run=dry_run)
        data = resp.get("data", {})
        nodes.extend(data.get("nodes", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token", "")
        if not page_token:
            break
    return nodes


def build_remote_tree(dry_run: bool = False) -> dict[str, dict[str, Any]]:
    """构建路径 → 节点 映射。路径格式：folder1/folder2/title（不含扩展名）。"""
    tree: dict[str, dict[str, Any]] = {}

    def walk(parent_token: str | None, parent_path: str) -> None:
        nodes = list_wiki_nodes(parent_token, dry_run=dry_run)
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
    """lark-cli --file 要求 cwd 内的相对路径，返回相对 SCRIPT_DIR 的 posix 路径。
    文件必须在 SCRIPT_DIR 内；跨盘/不同根时直接报错，绝不退回绝对路径（否则 lark-cli 拒收并挂起死锁）。"""
    try:
        rel = local_path.relative_to(SCRIPT_DIR)
    except ValueError:
        rel = Path(os.path.relpath(str(local_path), str(SCRIPT_DIR)))
        if rel.is_absolute():
            raise RuntimeError(
                f"--file 必须是 SCRIPT_DIR 内的相对路径，但 {local_path} 不在 {SCRIPT_DIR} 内"
            )
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
    """根据当前 manifest 与远程节点路径，初始化 feishu_remote_map.json + vault bindings.json（三源双写）。
    注意：bootstrap 仅播种 remote_map 与 vault bindings.json，不写 .md frontmatter（避免一次性改动大量源文件）；
    frontmatter 在日常 sync 运行时按需增量写入。"""
    manifest = load_json(MANIFEST_PATH)
    remote_tree = build_remote_tree()
    remote_map: dict[str, Any] = load_json(REMOTE_MAP_PATH)
    vault_bindings: dict[str, Any] = load_vault_bindings()
    matched = 0
    unmatched = 0

    for rel, info in sorted(manifest.get("files", {}).items()):
        remote_node = remote_node_for(rel, remote_tree)
        if not remote_node:
            unmatched += 1
            continue
        local_sha = info.get("sha256", "")
        ext_lower = Path(rel).suffix.lower()
        if ext_lower == ".md" and remote_node.get("obj_type") == "docx":
            remote_map[rel] = record_binding(rel, remote_node["node_token"], remote_node["obj_token"], "docx", local_sha, vault_bindings, write_frontmatter=False)
            matched += 1
        elif remote_node.get("obj_type") == "file":
            remote_map[rel] = record_binding(rel, remote_node["node_token"], remote_node["obj_token"], "file", local_sha, vault_bindings, write_frontmatter=False)
            matched += 1
        else:
            unmatched += 1

    save_json(REMOTE_MAP_PATH, remote_map)
    save_vault_bindings(vault_bindings)
    return {
        "matched": matched,
        "unmatched": unmatched,
        "total": len(manifest.get("files", {})),
        "vault_bindings_seeded": len(vault_bindings),
    }


def sync(dry_run: bool = False) -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    remote_map = load_json(REMOTE_MAP_PATH)
    vault_bindings: dict[str, Any] = load_vault_bindings()
    failures = load_json(FAILURES_PATH)
    failure_paths = set(failures.keys())

    remote_tree = build_remote_tree(dry_run=dry_run)
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
    manifest_match_paths: set[str] = set()

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

        # 匹配 key：md 节点 title 为 stem（无扩展名），附件节点 title 含扩展名；
        # 同时以 stem_key / ext_key 两种 key 标记"已匹配"，避免附件被误判孤儿而重复上传（bug①）
        parts = path_parts(rel)
        stem_key = "/".join(parts[:-1] + (Path(rel).stem,))
        ext_key = "/".join(parts[:-1] + (Path(rel).name,))
        manifest_match_paths.add(stem_key)
        manifest_match_paths.add(ext_key)

        remote_node = remote_node_for(rel, remote_tree)
        # 三源恢复：remote_map 缺失时回退 vault_bindings / .md frontmatter，避免「绑定丢失→重复建文档」
        remote_entry, _src = resolve_binding(rel, remote_map, vault_bindings, vault_md_path(rel))
        if remote_entry is None:
            remote_entry = {}
        remote_sha = remote_entry.get("sha256", "")

        try:
            if is_md:
                if remote_node and remote_node.get("obj_type") == "docx":
                    if remote_sha == local_sha:
                        # sha 未变：幂等跳过，绝不重建（dry-run 与真实一致，P1③）
                        stats["md_unchanged"] += 1
                        new_remote_map[rel] = remote_entry
                    else:
                        result = update_md(rel, local_path, remote_node, parent_node, dry_run)
                        stats["md_updated"] += 1
                        new_remote_map[rel] = record_binding(rel, result["node_token"], result["obj_token"], "docx", local_sha, vault_bindings, dry_run=dry_run)
                else:
                    result = upload_md(rel, local_path, parent_node, dry_run)
                    stats["md_created"] += 1
                    new_remote_map[rel] = record_binding(rel, result["node_token"], result["obj_token"], "docx", local_sha, vault_bindings, dry_run=dry_run)
            else:
                # 附件
                if remote_node and remote_node.get("obj_type") == "file":
                    if remote_sha == local_sha:
                        # sha 未变：幂等跳过（P1③）
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

    # P1② 删除分支：收集"飞书有、本地 manifest 无"的孤儿节点（仅 docx/file，不碰文件夹）
    pending_deletes = []
    for rpath, node in remote_tree.items():
        # 仅收 file 级孤儿（附件）：文件夹容器与文档都是 docx 类型，
        # 若纳入会误删整棵目录树（bug②）。真实删除需单独 YES 授权，此处只列清单不执行。
        if node.get("obj_type") == "file" and rpath not in manifest_match_paths:
            pending_deletes.append({
                "path": rpath,
                "node_token": node.get("node_token"),
                "obj_type": node.get("obj_type"),
                "title": node.get("title"),
            })
    stats["pending_deletes"] = pending_deletes

    if not dry_run:
        save_json(REMOTE_MAP_PATH, new_remote_map)
        save_json(FAILURES_PATH, failures)
        save_vault_bindings(vault_bindings)
        # P1②：真实运行才写待删清单（dry-run 仅 stats 预览，零副作用）
        save_json(PENDING_DELETES_PATH, {
            "pending": pending_deletes,
            "generated_at": datetime.now().astimezone().isoformat(),
        })

    return {
        "space_id": SPACE_ID,
        "space_name": SPACE_NAME,
        "dry_run": dry_run,
        "stats": stats,
    }


def apply_deletes(dry_run: bool = False) -> dict[str, Any]:
    """P1②：执行 pending_deletes.json 中的待删节点。

    dry_run=True 仅预览；False 真实删除，且需交互输入 YES 二次确认。
    删除是不可逆的外部动作——调用方（CLI）应确保用户已审阅清单。
    """
    data = load_json(PENDING_DELETES_PATH)
    pending = data.get("pending", [])
    if not pending:
        return {"total": 0, "deleted": 0, "errors": [], "dry_run": dry_run, "note": "无可删除项"}
    print(f"[apply-deletes] 将处理 {len(pending)} 个待删节点：")
    for p in pending:
        print(f"  - {p.get('path')}  ({p.get('obj_type')})  node={p.get('node_token')}")
    if not dry_run:
        confirm = input("确认删除以上节点？输入 YES 继续：").strip()
        if confirm != "YES":
            print("已取消删除。")
            return {"total": len(pending), "deleted": 0, "errors": [], "dry_run": False, "cancelled": True}
    deleted = []
    errors = []
    for p in pending:
        node_token = p.get("node_token")
        if not node_token:
            continue
        try:
            run_lark(["wiki", "+node-delete", "--node-token", node_token], dry_run=dry_run)
            if not dry_run:
                deleted.append(node_token)
        except Exception as e:
            errors.append({"node_token": node_token, "error": str(e)})
    if not dry_run and deleted:
        save_json(PENDING_DELETES_PATH, {
            "pending": [],
            "applied_at": datetime.now().astimezone().isoformat(),
            "deleted": deleted,
        })
    return {"total": len(pending), "deleted": len(deleted), "errors": errors, "dry_run": dry_run}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="仅打印计划，不执行写入")
    parser.add_argument("--bootstrap", action="store_true", help="仅根据当前 manifest 与远程节点初始化 feishu_remote_map.json")
    parser.add_argument("--apply-deletes", action="store_true", help="执行 pending_deletes.json 中的待删节点（默认 dry-run 预览；真实删除需交互确认）")
    args = parser.parse_args()
    if args.bootstrap:
        result = bootstrap_remote_map()
    elif args.apply_deletes:
        result = apply_deletes(dry_run=args.dry_run)
    else:
        result = sync(dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if isinstance(result, dict) and "errors" in result and result["errors"]:
        sys.exit(1)
