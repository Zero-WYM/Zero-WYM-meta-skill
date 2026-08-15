#!/usr/bin/env python3
"""Obsidian → 标准 Markdown 导出器。

- wikilink / embed → 标准相对链接
- callout → 引用块
- frontmatter 保留
- manifest.json 驱动增量
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

# 工作目录：脚本所在目录
SCRIPT_DIR = Path(__file__).resolve().parent
# 仓库真源：可用环境变量覆盖（默认用户的第二大脑）；避免硬编码、便于迁移
VAULT_DIR = Path(os.environ.get("OBSIDIAN_VAULT_DIR", "D:/第二大脑"))
# 导出目录默认放在包体【外】（用户缓存区），可用环境变量覆盖，避免污染 Skill 包
EXPORT_DIR = Path(os.environ.get(
    "OBSIDIAN_SYNC_EXPORT_DIR",
    str(Path.home() / ".cache" / "obsidian-kb-sync" / "export"),
))
# manifest 与导出产物同目录，统一在包体外，避免污染包体
MANIFEST_PATH = EXPORT_DIR / "manifest.json"

# 附件扩展名（与 sync_to_feishu.py 共享）
ATTACHMENT_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".mp4", ".mov", ".webm", ".mkv", ".avi",
    ".mp3", ".wav", ".ogg", ".m4a", ".flac",
    ".pdf", ".docx", ".pptx", ".xlsx", ".zip", ".epub",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_str(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def convert_wikilinks(text: str) -> str:
    """将 [[...]] / ![[...]] 转为标准相对链接。"""
    # ![[image.png|alt]] → ![](image.png)
    text = re.sub(
        r"!\[\[([^|\]]+)(?:\|[^\]]+)?\]\]",
        lambda m: f"![]({m.group(1).strip()})",
        text,
    )
    # [[note|display]] → [display](note.md)
    text = re.sub(
        r"\[\[([^|\]]+)\|([^\]]+)\]\]",
        lambda m: f"[{m.group(2).strip()}]({m.group(1).strip()}.md)",
        text,
    )
    # [[note]] → [note](note.md)
    text = re.sub(
        r"\[\[([^\]]+)\]\]",
        lambda m: f"[{m.group(1).strip()}]({m.group(1).strip()}.md)",
        text,
    )
    return text


def convert_callouts(text: str) -> str:
    """将 Obsidian callout 转为 Markdown 引用块。"""
    lines = text.splitlines()
    out: list[str] = []
    in_callout = False
    for line in lines:
        m = re.match(r"^(>+)\s*\[!\s*(\w+)\]([^\n]*)$", line)
        if m:
            prefix = m.group(1)
            callout_type = m.group(2).strip().lower()
            title = m.group(3).strip().lstrip("-").strip()
            if title:
                out.append(f"{prefix} **{callout_type.upper()}**: {title}")
            else:
                out.append(f"{prefix} **{callout_type.upper()}**:")
            in_callout = True
            continue
        if in_callout and line.startswith(">"):
            out.append(line)
            continue
        in_callout = False
        out.append(line)
    return "\n".join(out)


def normalize_md(text: str) -> str:
    text = convert_wikilinks(text)
    text = convert_callouts(text)
    return text


def is_attachment(path: Path) -> bool:
    return path.suffix.lower() in ATTACHMENT_EXTS


def relative_to_vault(path: Path, vault_dir: Path) -> str:
    try:
        rel = path.relative_to(vault_dir)
    except ValueError:
        rel = path
    return rel.as_posix()


def load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"version": 1, "files": {}, "last_run": None}


def save_manifest(manifest: dict[str, Any]) -> None:
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def should_skip(path: Path) -> bool:
    """跳过 Obsidian 配置、workbuddy 元数据、临时文件。"""
    parts = set(path.parts)
    if ".obsidian" in parts or ".workbuddy" in parts:
        return True
    if path.suffix in {".tmp", ".bak", ".swp", ".DS_Store"}:
        return True
    if path.name.startswith("~") or path.name.endswith("~"):
        return True
    return False


def normalize() -> dict[str, Any]:
    if not VAULT_DIR.exists():
        raise FileNotFoundError(f"Vault 不存在: {VAULT_DIR}")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    previous_files = set(manifest.get("files", {}).keys())
    current_files: dict[str, dict[str, Any]] = {}
    stats = {"md_copied": 0, "md_unchanged": 0, "attachment_copied": 0, "attachment_unchanged": 0, "skipped": 0}

    for src_path in sorted(VAULT_DIR.rglob("*")):
        if src_path.is_dir():
            continue
        if should_skip(src_path):
            stats["skipped"] += 1
            continue

        rel = relative_to_vault(src_path, VAULT_DIR)
        ext_lower = src_path.suffix.lower()

        if ext_lower == ".md":
            text = src_path.read_text(encoding="utf-8")
            normalized = normalize_md(text)
            content_hash = sha256_str(normalized)
            dst_path = EXPORT_DIR / rel
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            prev = manifest.get("files", {}).get(rel)
            if prev and prev.get("sha256") == content_hash and dst_path.exists():
                stats["md_unchanged"] += 1
            else:
                dst_path.write_text(normalized, encoding="utf-8")
                stats["md_copied"] += 1

            current_files[rel] = {
                "type": "md",
                "sha256": content_hash,
                "mtime": src_path.stat().st_mtime,
            }
        elif is_attachment(src_path):
            file_hash = sha256_file(src_path)
            dst_path = EXPORT_DIR / rel
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            prev = manifest.get("files", {}).get(rel)
            if prev and prev.get("sha256") == file_hash and dst_path.exists():
                stats["attachment_unchanged"] += 1
            else:
                shutil.copy2(src_path, dst_path)
                stats["attachment_copied"] += 1

            current_files[rel] = {
                "type": "attachment",
                "sha256": file_hash,
                "mtime": src_path.stat().st_mtime,
                "size": src_path.stat().st_size,
            }
        else:
            # 其他文件不导出（如 .canvas 等）
            stats["skipped"] += 1

    # 清理已不存在的文件
    removed = previous_files - set(current_files.keys())
    for rel in removed:
        dst = EXPORT_DIR / rel
        if dst.exists():
            dst.unlink()

    manifest["files"] = current_files
    manifest["last_run"] = __import__("datetime").datetime.now().isoformat()
    save_manifest(manifest)

    summary = {
        "vault": str(VAULT_DIR),
        "export": str(EXPORT_DIR),
        "total_files": len(current_files),
        "md_total": stats["md_copied"] + stats["md_unchanged"],
        "attachment_total": stats["attachment_copied"] + stats["attachment_unchanged"],
        "md_changed": stats["md_copied"],
        "attachment_changed": stats["attachment_copied"],
        "removed": len(removed),
        "skipped": stats["skipped"],
    }
    return summary


if __name__ == "__main__":
    import datetime
    result = normalize()
    print(json.dumps(result, ensure_ascii=False, indent=2))
