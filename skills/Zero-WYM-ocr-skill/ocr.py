#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ocr.py — 本地 easyocr 图片文字提取
用法:
  单图:  python ocr.py "<图片路径>"
  目录:  python ocr.py "<目录路径>"
依赖:    C:/Users/33754/.workbuddy/binaries/python/envs/default 中的 easyocr
"""
import sys
import os
from pathlib import Path

IMG_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}


def get_reader():
    try:
        import easyocr
    except ImportError:
        sys.stderr.write(
            "ERROR: easyocr 未安装在隔离 venv。请先运行:\n"
            "  C:\\Users\\33754\\.workbuddy\\binaries\\python\\envs\\default\\Scripts\\pip install easyocr\n"
        )
        sys.exit(2)
    # gpu=False 走 CPU，避免依赖 CUDA；如需可改 True
    return easyocr.Reader(['ch_sim', 'en'], gpu=False)


def ocr_one(path: str, reader) -> str:
    # 关键: 本 sandbox 的 opencv 5.0.0 对 cv2.imread 读 PNG 会失败
    # (can't open/read file)，但 PIL 可正常解码。故统一用 PIL 打开
    # 并转 numpy 数组直传给 easyocr，绕开文件路径解码问题，
    # 同时兼容中文路径 / 混合斜杠。
    from PIL import Image
    import numpy as np
    img = Image.open(path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    arr = np.array(img)
    lines = reader.readtext(arr, detail=0, paragraph=True)
    return "\n".join(str(x) for x in lines)


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python ocr.py <image_or_dir>\n")
        sys.exit(1)
    target = sys.argv[1]
    if not os.path.exists(target):
        sys.stderr.write(f"ERROR: 路径不存在: {target}\n")
        sys.exit(1)

    reader = get_reader()
    if os.path.isdir(target):
        for f in sorted(Path(target).iterdir()):
            if f.suffix.lower() in IMG_EXTS:
                print(f"\n===== {f.name} =====")
                try:
                    print(ocr_one(str(f), reader))
                except Exception as e:
                    print(f"[OCR 失败: {e}]")
    else:
        print(ocr_one(target, reader))


if __name__ == "__main__":
    main()
