# Paper Review Gates

## Gate 类型

### Section gate

- 本节使命是否清楚。
- 核心 claim 是否有证据或引用。
- 与前后章节是否衔接。
- 是否存在未定义术语、符号或指标。

### Methodology gate

- 任务、数据、baseline、指标和统计口径是否可复现。
- 方法选择是否有理由。
- 结果是否真正支持结论。

### Coherence gate

- 贡献、方法、实验、图表和讨论是否讲同一条主线。
- Abstract、Introduction 和 Conclusion 是否互相一致。

### Abstract gate

- 是否包含问题、方法、结果和意义。
- 是否出现未在正文支撑的 claim。

## 审查输出

- 人类报告按 `taskpack.output_language` 显示级别；字段缺失时按 `zh`。中文使用“严重 / 主要 / 次要”，英文使用 “Critical / Major / Minor”。
- 严重问题涉及核心事实、引用、实验结果、方法有效性或伦理风险，需要用户确认后再修订。
- 主要问题必须在进入下一轮前收口。
- 次要问题可作为语言、格式和局部表达修订。
- 机器事件的 `severity` 枚举继续使用 `critical`、`major`、`minor`。
