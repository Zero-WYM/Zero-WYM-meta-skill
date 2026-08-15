# Eval 驱动与测试样例

本 Skill 的迭代不靠「感觉更好」，而靠可重复验证。分类脚本内置固定测试用例：

```bash
python scripts/classify_raw_materials.py --test
```

固定用例（任一文件命中即应归入对应类）：

| 文件名特征 | 期望分类 |
|---|---|
| `Screenshot_..._com.ss.android.lark_a.png` | 飞书课程截图 |
| `IMG_x_com.ss.android.ugc.aweme_b.jpg` | 抖音知识碎片 |
| `com.tencent.hunyuan.app.chat_c.png` | 实战项目过程 |
| `mmexport1723389000000.jpg` | 实战项目过程 |
| `1786032689749.jpg`（13 位纯数字） | 实战项目过程 |
| `photo_2026.png`（无特征） | 实战项目过程（默认兜底） |

每次优化分类规则后，重跑 `--test`，对比前后通过数，用结果说话。
