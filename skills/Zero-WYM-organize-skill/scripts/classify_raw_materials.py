#!/usr/bin/env python3
"""
第二大脑 · 原始素材批量分类脚本

功能：按文件名中的包名/时间戳特征，把图片自动分类到
      素材/学习/抖音AI夜校/ 下的三个子目录：
      - 飞书课程截图
      - 抖音知识碎片
      - 实战项目过程

用法：
    # 批量分类（复制归档，源文件不动）
    python classify_raw_materials.py <源目录> <目标根目录>

    # 跑内置固定测试用例（Eval 驱动迭代）
    python classify_raw_materials.py --test

    # 生成「原数据清理清单」（Step 7 用，纯只读，不复制不删）
    # 比对暂存目录与素材根，标出 ✅已落实 / ⚠️仅知识点 / ❌未落实
    python classify_raw_materials.py --manifest <源/暂存目录> <素材根目录> [--check-knowledge <知识点md目录>] [--json]
"""

import sys
import json
import shutil
from pathlib import Path

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp")


def classify_image(filename: str) -> str:
    """根据文件名判断来源类别。"""
    f = filename.lower()
    # 飞书/起点读书 → 课程截图
    if "com.ss.android.lark" in f or "com.dragon.read" in f:
        return "飞书课程截图"
    # 抖音 → 知识碎片
    if "com.ss.android.ugc.aweme" in f:
        return "抖音知识碎片"
    # 腾讯元宝 / 微信 / 13位时间戳 → 实战项目过程
    if "com.tencent.hunyuan" in f or "mmexport" in f:
        return "实战项目过程"
    # 13 位纯数字时间戳（如 1786032689749.jpg）
    stem = Path(filename).stem
    if stem.isdigit() and len(stem) == 13:
        return "实战项目过程"
    # 默认：无法识别时归入实战项目过程（让用户后续手动调整）
    return "实战项目过程"


# ---- Eval：固定测试用例（优化分类规则后重跑对比）----
TEST_CASES = [
    ("Screenshot_2026-08-10_com.ss.android.lark_a.png", "飞书课程截图"),
    ("IMG_x_com.ss.android.ugc.aweme_b.jpg", "抖音知识碎片"),
    ("com.tencent.hunyuan.app.chat_c.png", "实战项目过程"),
    ("mmexport1723389000000.jpg", "实战项目过程"),
    ("1786032689749.jpg", "实战项目过程"),
    ("photo_2026.png", "实战项目过程"),
]


def run_tests() -> int:
    print("=== 分类脚本固定测试用例 ===")
    passed = 0
    for name, expected in TEST_CASES:
        got = classify_image(name)
        ok = got == expected
        passed += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name} -> {got} (期望 {expected})")
    print(f"\n通过 {passed}/{len(TEST_CASES)}")
    return 0 if passed == len(TEST_CASES) else 1


def ensure_readme(target_dir: Path, title: str, desc: str):
    readme = target_dir / "README.md"
    if readme.exists():
        return
    content = f"""# {title}

> {desc}
> 本目录由 `Zero-WYM-organize-skill` Skill 自动维护。

## 说明

子目录下均为图片素材，文件名未改动。Obsidian 中通过文件树或链接浏览。

---

*自动归档时间：见各文件修改时间*
"""
    readme.write_text(content, encoding="utf-8")


def main(src_dir: str, dst_root: str):
    src = Path(src_dir)
    dst = Path(dst_root)
    if not src.exists():
        print(f"源目录不存在: {src}")
        sys.exit(1)

    dst.mkdir(parents=True, exist_ok=True)

    counts = {"飞书课程截图": 0, "抖音知识碎片": 0, "实战项目过程": 0}
    moved = []

    for f in sorted(src.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() not in IMAGE_EXTS:
            continue
        category = classify_image(f.name)
        target_dir = dst / category
        target_dir.mkdir(exist_ok=True)
        target = target_dir / f.name
        # 若目标已存在则跳过，避免覆盖
        if target.exists():
            print(f"跳过（已存在）: {f.name}")
            continue
        shutil.copy2(str(f), str(target))
        counts[category] += 1
        moved.append((f.name, category))

    # 补 README
    ensure_readme(dst / "飞书课程截图", "飞书课程截图", "飞书/起点读书来源的课程截图。")
    ensure_readme(dst / "抖音知识碎片", "抖音知识碎片", "抖音刷到的知识点碎片。")
    ensure_readme(dst / "实战项目过程", "实战项目过程", "腾讯元宝/微信/时间戳来源的实战过程截图。")

    print("\n=== 分类结果 ===")
    for cat, n in counts.items():
        print(f"  {cat}: {n} 张")
    print(f"\n已复制到: {dst}")


# ---- manifest：原数据清理清单（Step 7 安全闸门支撑）----
# 纯只读：比对「暂存目录」与「素材根」，标出每个源文件的落实状态，不复制、不移动、不删除。
# 状态三态：
#   ✅ 已落实   → 素材根下存在同名副本（本 Skill 或别的流程已归档）
#   ⚠️ 仅知识点 → 素材根无同名，但知识点 md 里引用了文件名（保守保留，防误删）
#   ❌ 未落实   → 素材根无同名、知识点也未引用 → 默认保留，不清理
def build_manifest(src_dir: str, material_root: str, check_knowledge_dir: str = None):
    src = Path(src_dir)
    root = Path(material_root)
    if not src.exists():
        print(f"源目录不存在: {src}")
        sys.exit(1)

    items = []
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() not in IMAGE_EXTS:
            continue
        name = f.name
        # 1) 素材根下查同名副本
        hits = list(root.rglob(name)) if root.exists() else []
        if hits:
            try:
                loc = str(hits[0].relative_to(root))
            except ValueError:
                loc = str(hits[0])
            items.append({"name": name, "status": "✅ 已落实", "location": loc})
            continue
        # 2) 可选：知识点 md 引用检查（准确率有限，默认关闭）
        if check_knowledge_dir:
            stem = f.stem
            cdir = Path(check_knowledge_dir)
            if cdir.exists():
                found = False
                for md in cdir.rglob("*.md"):
                    try:
                        text = md.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue
                    if stem in text:
                        found = True
                        break
                if found:
                    items.append({"name": name, "status": "⚠️ 仅知识点",
                                   "location": f"知识点 md 引用了 {stem}"})
                    continue
        # 3) 都没命中
        items.append({"name": name, "status": "❌ 未落实", "location": "—"})
    return items


def render_manifest_markdown(items, src_dir, material_root):
    print("# 原数据清理清单（manifest）\n")
    print(f"源目录: {src_dir}")
    print(f"素材根: {material_root}\n")
    print("| 文件 | 状态 | 第二大脑落点 |")
    print("|------|------|--------------|")
    for it in items:
        print(f"| {it['name']} | {it['status']} | {it['location']} |")
    done = sum(1 for i in items if i["status"] == "✅ 已落实")
    warn = sum(1 for i in items if i["status"] == "⚠️ 仅知识点")
    notdone = sum(1 for i in items if i["status"] == "❌ 未落实")
    print(f"\n**统计**：已落实 {done} / 仅知识点 {warn} / 未落实 {notdone}")
    print("\n> 仅 ❌ 未落实的源文件在 Step 7 中应默认保留，避免误删尚未落地的素材。")


def main_manifest(argv):
    check_knowledge = None
    as_json = False
    positional = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--check-knowledge":
            i += 1
            if i >= len(argv):
                print("错误: --check-knowledge 需要一个目录参数")
                sys.exit(1)
            check_knowledge = argv[i]
        elif a == "--json":
            as_json = True
        else:
            positional.append(a)
        i += 1
    if len(positional) != 2:
        print("用法: python classify_raw_materials.py --manifest <源/暂存目录> <素材根目录> "
              "[--check-knowledge <知识点md目录>] [--json]")
        sys.exit(1)
    src_dir, material_root = positional
    items = build_manifest(src_dir, material_root, check_knowledge)
    if as_json:
        print(json.dumps({"source": src_dir, "material_root": material_root, "items": items},
                         ensure_ascii=False, indent=2))
    else:
        render_manifest_markdown(items, src_dir, material_root)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == "--test":
        sys.exit(run_tests())
    if args[0] == "--manifest":
        sys.exit(main_manifest(args[1:]))
    if len(args) != 2:
        print(__doc__)
        sys.exit(1)
    main(args[0], args[1])
