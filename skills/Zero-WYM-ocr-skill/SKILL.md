---
name: Zero-WYM-ocr-skill
keywords: [ocr, 识图]
description: '用本地 easyocr 离线读取图片/截图中的文字（中文+英文+代码混合识别）。当当前会话的模型无法直接读取图片文件（Read 图片返回 does not support images / Content filtered）、或需要批量离线提取截图文字时使用。调用用户级 venv 中的 easyocr。其他 skill（如 Zero-WYM-organize-skill）在 OCR 环节可调用本 skill。 / Local offline OCR via EasyOCR for reading text from images and screenshots (mixed Chinese + English + code recognition). Use when the current model cannot read image files directly (Read returns does not support images / Content filtered), or when batch offline text extraction from screenshots is needed. Invokes EasyOCR installed in the user-level venv. Other skills (e.g. Zero-WYM-organize-skill) may call this skill during their OCR step.'
version: 1.1.0
agent_created: true
---

# OCR 图片读取器

## 何时触发
- 当前模型无法直接读取图片（Read 图片返回 "does not support images" / "Content filtered"）
- 需要对一批截图/图片做离线文字提取
- 其他 skill（如 `Zero-WYM-organize-skill`）在 Step 1「OCR / 内容提取」判断需要识别图片文字时，加载本 skill 调用本地 easyocr

## 环境与依赖
- 隔离 Python 虚拟环境（已含 easyocr）：`C:\Users\33754\.workbuddy\binaries\python\envs\default`
- 该 venv 的 Python 解释器：`C:\Users\33754\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
- easyocr 模型：首次运行 `easyocr.Reader(['ch_sim','en'])` 会自动下载识别模型到 `C:\Users\33754\.EasyOCR\`（约 50–100MB，下载一次后离线可用）
- 该环境为**用户级共享**，任何 WorkBuddy 会话/窗口均可复用，无需重复安装

## 用法

读取单张图片（输出图片中的全部文字）：
```
C:\Users\33754\.workbuddy\binaries\python\envs\default\Scripts\python.exe "C:\Users\33754\.workbuddy\skills\Zero-WYM-ocr-skill\ocr.py" "图片绝对路径"
```

批量读取整个目录（逐个文件输出 文件名 + 文字）：
```
C:\Users\33754\.workbuddy\binaries\python\envs\default\Scripts\python.exe "C:\Users\33754\.workbuddy\skills\Zero-WYM-ocr-skill\ocr.py" "目录绝对路径"
```

## 调用约定（给其他 skill 用）
1. 先判断：本会话能否用 Read 直接读图？能则直接读，不必走 OCR。
2. 不能读（被过滤）→ 加载本 skill，用上面的命令对每张图跑 OCR，把 stdout 文字作为"读到的内容"继续后续流程。
3. OCR 输出即图片文字，按识别顺序拼接；用于核对截图命名、提炼知识点、判定归属。

## 注意事项
- **读图通道（重要坑）**：本沙箱内 opencv 5.0.0 的 `cv2.imread` 读取 PNG 会稳定失败（报 `can't open/read file`，即便文件存在、路径为正斜杠）。`ocr.py` 已改为统一用 `PIL.Image.open` 解码、转 `numpy` 数组后直接传给 `easyocr.Reader.readtext(arr)`，彻底绕开该问题，**兼容中文路径与混合斜杠**。调用方直接传文件路径即可，无需关心内部实现。
- 路径含空格需用英文双引号包裹。
- 首次 OCR 会下载模型（需联网一次）；之后离线。
- 识别质量受图片清晰度/排版影响；模糊或复杂表格建议结合 PPT 课件文本交叉核对。
- 本 skill 只产出文字，**不删除、不移动、不修改任何图片文件**。
