#!/usr/bin/env python3
"""超限 pptx 压缩内部媒体（图片重编码 + 视频转码）。

- 解开 .pptx（本质是 zip），遍历 ppt/media/ 下媒体
- 图片：Pillow 重编码降质（默认 quality=70），体积显著下降
- 视频：imageio-ffmpeg 转码为更高压缩率的 mp4（若可用）
- 重打包为 <原名>_shrunk.pptx，并在包内 customProps/shrunk.json 标记 shrunk_from 原件路径
- 缺失 Pillow / imageio-ffmpeg 时：明确提示并退出（非零），不静默产出损坏文件

用法：
  python shrink_pptx.py input.pptx [--out out.pptx] [--quality 70]
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any

MEDIA_PREFIX = "ppt/media/"


def log(msg: str) -> None:
    print(msg, flush=True)


def has_pil() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except Exception:
        return False


def has_ffmpeg() -> bool:
    try:
        import imageio_ffmpeg  # noqa: F401
        return True
    except Exception:
        return False


def shrink_image(data: bytes, quality: int) -> bytes | None:
    """返回压缩后 bytes；无法处理则返回 None（保持原样）。"""
    if not has_pil():
        return None
    from PIL import Image

    try:
        img = Image.open(io.BytesIO(data))
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        out = io.BytesIO()
        fmt = "JPEG" if img.mode == "RGB" else "PNG"
        if fmt == "JPEG":
            img.save(out, "JPEG", quality=quality, optimize=True)
        else:
            img.save(out, "PNG", optimize=True)
        return out.getvalue()
    except Exception as e:  # noqa: BLE001
        log(f"  [warn] 图片重编码失败，保留原样: {e}")
        return None


def shrink_video(data: bytes, quality: int) -> bytes | None:
    if not has_ffmpeg():
        return None
    import imageio_ffmpeg
    import subprocess

    exe = imageio_ffmpeg.get_ffmpeg_exe()
    tmpdir = Path(os.environ.get("TMPDIR", "/tmp"))
    tmp_in = tmpdir / "_shrink_in.tmp"
    tmp_out = tmpdir / "_shrink_out.mp4"
    try:
        tmp_in.write_bytes(data)
        crf = max(18, 40 - quality)  # quality 越高 crf 越低
        subprocess.run(
            [exe, "-y", "-i", str(tmp_in), "-vcodec", "libx264",
             "-crf", str(crf), "-acodec", "aac", str(tmp_out)],
            check=False, capture_output=True,
        )
        if tmp_out.exists() and tmp_out.stat().st_size > 0:
            return tmp_out.read_bytes()
    except Exception as e:  # noqa: BLE001
        log(f"  [warn] 视频转码失败，保留原样: {e}")
    finally:
        for p in (tmp_in, tmp_out):
            try:
                p.unlink()
            except OSError:
                pass
    return None


def mark_shrunk(zf: zipfile.ZipFile, src_path: str) -> None:
    """在 pptx 内 customProps 写入 shrunk_from 标记（溯源用）。"""
    try:
        custom = {
            "shrunk_from": src_path,
            "shrunk_by": "sync-skill/shrink_pptx.py",
        }
        with zf.open("customProps/shrunk.json", "w") as f:
            f.write(json.dumps(custom, ensure_ascii=False).encode("utf-8"))
    except Exception as e:  # noqa: BLE001
        log(f"  [warn] 写入 shrunk_from 标记失败（不影响压缩结果）: {e}")


def shrink(input_path: Path, out_path: Path, quality: int) -> dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(f"找不到输入文件: {input_path}")
    stats: dict[str, Any] = {"images": 0, "videos": 0, "saved_bytes": 0, "skipped": 0}
    with zipfile.ZipFile(input_path, "r") as zin:
        names = zin.namelist()
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                data = zin.read(name)
                if name.startswith(MEDIA_PREFIX) and "/" not in name[len(MEDIA_PREFIX):]:
                    ext = Path(name).suffix.lower()
                    if ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff"):
                        new = shrink_image(data, quality)
                        if new is not None and len(new) < len(data):
                            data = new
                            stats["images"] += 1
                            stats["saved_bytes"] += len(data) - len(new)
                        elif new is not None:
                            stats["skipped"] += 1
                    elif ext in (".mp4", ".mov", ".webm", ".avi", ".mkv"):
                        new = shrink_video(data, quality)
                        if new is not None and len(new) < len(data):
                            data = new
                            stats["videos"] += 1
                            stats["saved_bytes"] += len(data) - len(new)
                        elif new is not None:
                            stats["skipped"] += 1
                zout.writestr(name, data)
            mark_shrunk(zout, str(input_path))
    orig = input_path.stat().st_size
    new = out_path.stat().st_size
    stats["orig_bytes"] = orig
    stats["new_bytes"] = new
    stats["ratio"] = round(new / orig, 3) if orig else 1.0
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="压缩超限 pptx 内部媒体")
    ap.add_argument("input", help="输入 .pptx 路径")
    ap.add_argument("--out", help="输出路径（默认 <输入>_shrunk.pptx）")
    ap.add_argument("--quality", type=int, default=70, help="图片质量 1-100（默认 70）")
    args = ap.parse_args()

    inp = Path(args.input)
    out = Path(args.out) if args.out else inp.with_name(inp.stem + "_shrunk.pptx")

    if not has_pil() and not has_ffmpeg():
        log("[ERROR] 缺少压缩依赖：Pillow（图片）与 imageio-ffmpeg（视频）均未安装。")
        log("        安装：pip install Pillow imageio-ffmpeg")
        log("        缺失时无法压缩，请手动用压缩软件降质后回传飞书。")
        return 2

    log(f"[info] 输入: {inp} ({inp.stat().st_size} bytes)")
    try:
        stats = shrink(inp, out, args.quality)
    except Exception as e:  # noqa: BLE001
        log(f"[ERROR] 压缩失败: {e}")
        return 1
    log(f"[info] 输出: {out} ({stats['new_bytes']} bytes, 压缩比 {stats['ratio']})")
    log(f"[info] 图片压缩 {stats['images']} 个，视频转码 {stats['videos']} 个，"
        f"跳过 {stats['skipped']} 个，共省 {stats['saved_bytes']} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
