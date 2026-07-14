# Peer Review Rubric

## 使用边界

本 rubric 用于模拟投稿前同行评审，不代表真实审稿意见。PDF 或文本读取不完整时，必须标注不确定性。

## 四维审查

| 维度 | 要看什么 | 常见 Major 问题 |
|---|---|---|
| Originality | 问题是否重要，贡献是否相对现有工作清楚 | 贡献和相关工作差异不明 |
| Methodology | 方法、实验、数据、baseline 和指标是否合理 | 没有对照、样本不足、统计口径不清 |
| Results | 结果是否支持 claim，有无消融和误差分析 | 结论超出证据 |
| Writing | 结构、叙事、图表、术语和可读性 | 摘要或引言承诺正文未支撑 |

## 输出模板

人类可读标题按 `taskpack.output_language` 选择；字段缺失时按 `zh`：

- `zh`：概要 / 优点 / 主要问题 / 次要问题 / 可执行修订计划。
- `en`：Summary / Strengths / Major concerns / Minor concerns / Actionable revision plan。

内容要求不随语言改变：概要用一句话概括论文试图解决的问题和方法；优点只写材料能支撑的内容；主要问题按证据链排序；次要问题聚焦表达、格式和局部清晰度；修订计划给出投稿前修改顺序。机器事件的 `severity` 枚举继续使用 `critical`、`major`、`minor`。

## 禁止

- 替用户补实验数值、p 值、作者或引用。
- 把模拟审稿写成真实审稿结论。
- 忽略方法和结果之间的证据链。
