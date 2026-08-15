# 触发评测方法 · 三桶用例 + 词袋启发式

> 移植自 `qiaomu-meta-skill` 的思路并独立重写。重点是**诚实**：这是代理指标，不是真实路由力。

## 为什么是"三桶"

单看"该触发"不够——一个描述写得烂的 Skill 也可能碰巧命中；真正区分优劣的是**它会不会误伤近邻**。因此分三桶：

| 桶 | 标签 | 含义 | 期望 |
|---|---|---|---|
| 该触发 | `should_trigger` | 用户意图明确指向本 Skill | 评测器判"触发" |
| 不该触发 | `should_not_trigger` | 意图指向**别的能力**（市场安装/skillhub/第二大脑） | 评测器判"不触发" |
| 近邻 | `near_miss` | 语义相邻但**不是**本 Skill（对比两个 skill / 读源码 / 卸载） | 评测器判"不触发" |

`pass_rate = (该触发的命中数 + 不该触发/近邻的未误触数) / 总用例数`。满分需 100%。

## 词袋命中原理（零依赖实现）

`trigger_eval.py` 的做法：
1. 读 `SKILL.md` 的 `description` 与正文关键词，构造**正向词袋**。
2. 对每个用例文本做分词（按中文/英文混合、去停用词）。
3. 计算**重叠度**：用例词与正向词袋的 Jaccard / 覆盖率。
4. 阈值判定：覆盖度 ≥ 阈值 → 判"触发"；否则"不触发"。
5. 对照用例真实标签，统计 pass/fail。

## 诚实边界（必读，写报告时附带）

- 这是**关键词覆盖**的启发式代理指标，**不等于模型真的会路由到本 Skill**。真实路由由 WorkBuddy 的匹配器决定，词袋无法预测。
- 因此 `qiaomu` 原 README 写的"23/23 触发评测通过"**不能作为真实触发力证据**——它只证明 description 覆盖了用例文本。
- 本包的 `trigger_eval.py` 输出里**强制打印免责声明**，报告里也照写，不假装它等于真实路由力。
- 要提升真实触发力，靠的是 `description` 自然嵌入用户原话 + references 里写明近邻边界，而非刷高这个词袋分数。

## 用例文件格式（evals/trigger_cases.json）

```json
{
  "skill": "Zero-WYM-meta-skill",
  "cases": [
    { "bucket": "should_trigger", "text": "帮我做个 skill 专门整理抖音截图" },
    { "bucket": "should_not_trigger", "text": "从市场安装一下 obsidian skill" },
    { "bucket": "near_miss", "text": "对比一下 skill-crafting 和这个工厂哪个好" }
  ]
}
```
