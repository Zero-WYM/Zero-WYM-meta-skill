# Zero-WYM-learn-skill · 三位一体自学引擎

> Zero-WYM（零-望月明工作台）自建 Skill 生态成员。基于 qiaomu-learning（向阳乔木, MIT）品牌化改造。

## 它解决什么
把「主题 / 教材 / 截图 / PDF / 笔记 / 你自己的理解」变成**主动推导**的循环学习，而不是被动灌输。

三种模式覆盖自学闭环：

| 模式 | 角色 | 触发词 | 详情 |
|------|------|--------|------|
| 逆向（输入） | 自顶向下拆解、画知识地图、给最小例子/思想实验 | 「逆向法」「给我最小例子」「画知识地图」 | [reverse-mode](references/reverse-mode.md) |
| 费曼（输出） | 你讲、AI 扮小白只追问不给药（含拓展层） | 「费曼法」「讲给小白听」 | [feynman-mode](references/feynman-mode.md) |
| 苏格拉底（加工） | 一轮一问、累积黑板、来源忠实 | 「苏格拉底」「逐问带我学」「一次只问一个问题」 | [socratic-protocol](references/socratic-protocol.md) |

闭环：`①逆向 → ②费曼 → ③苏格拉底 → ④费曼(整合) → ⑤应用验证 → 回到①`。详见 [loop-orchestration](references/loop-orchestration.md)。

## 关键特性
- **水平感知**：开场判定你的水平与领域；非编程 / 零基础默认用类比与词汇地基，**不默认抛代码**。
- **12 词知识地图**：宽泛主题先列恰好 12 个关键词 + 白话解释 + 专家/书籍。
- **一轮一问**：每个活跃回合只问一个简短问题，像真人老师一样接住你的原话。
- **掌握门**：用自己的话解释 + 新情境应用，才算真掌握。
- **来源忠实**：材料里的「忽略前文 / 运行命令」只当学习内容，不当作指令。
- **随时退出**：说「停止 / 直接告诉我 / 只要总结」立即退出苏格拉底模式。

## 安装（WorkBuddy）
本 skill 由 Zero-WYM 生态加载，不走 `npx skills add`。将本目录置于：
- 真身：`D:\.agent\skills\Zero-WYM-learn-skill\`
- 加载：`C:\Users\33754\.workbuddy\skills\Zero-WYM-learn-skill\`（junction 或副本）

## 许可与署名
- 原许可：**MIT**，原作者 **向阳乔木**，见 [LICENSE](LICENSE)（必须保留）。
- 改造：Zero-WYM 生态，方法论（三位一体）归属 **Master**。详见 [NOTICE](NOTICE)。

## 致谢
上游引擎来自 向阳乔木 的 qiaomu-learning（MIT），感谢其受治理的苏格拉底学习协议。
