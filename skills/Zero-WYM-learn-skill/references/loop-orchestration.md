# Loop Orchestration（循环编排）

本 skill 不是单向苏格拉底对话，而是「逆向→费曼→苏格拉底→费曼→应用验证」的五步循环编排器。源自 Master 方法论的闭环设计。

## loop-state（会话内维护）
```
loop-state:
  step: ①逆向 | ②费曼 | ③苏格拉底 | ④费曼(整合) | ⑤应用验证
  concept: <当前概念>
  mode: 逆向 | 费曼 | 苏格拉底
  blind_spots: [<盲区描述>]
```
- 沿用 socratic-protocol 的「学习证据账本」（unseen/exposed/recalled/applied/confused + own_words/transfer）；
- 盲区记入 `blind_spots`，每条含「事实偏差 / 过度泛化 / 误解」类型与 learner 原话摘要。

## 五步推进
```
①逆向(输入)   → 最小例子/思想实验/知识地图
②费曼(输出)   → learner 讲，小白只追问，暴露盲区
③苏格拉底(加工)→ 一轮一问深挖边界，记 blind_spots
④费曼(整合)   → learner 用自己话整合，验证掌握门
⑤应用验证     → learner 自行实现/应用后回来复盘
   ↓
回到① 攻克下一概念（螺旋上升）
```
- ②暴露的盲区 → ③深挖 → ④更准 → ⑤验证；
- 模式可临时前折（如 learner 点名要深挖某点，可②→③提前）；
- 每个概念只有 `own_words=true 且 transfer=true` 才算掌握（沿用苏格拉底掌握门）。

## 进度记忆
- **会话内**：loop-state 全程维护，每 3–5 轮/暂停/切换主题时压缩总结；
- **跨会话（可选）**：可导出「追问日志.md」到第二大脑（2_学习板块），不默认接 context-skill（避免过度工程）；
- 用户说「停止/暂停」时停止发问，给恢复锚点；恢复从最后证据重算下一问。

## 退出
显式退出 / 直接答案 / 安全关键响应可不带问题，直接按意图响应。
