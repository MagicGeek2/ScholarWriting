# 扩展开发指南

ScholarWriting 采用模块化设计，支持扩展新的项目类型、写作规则、审阅维度和评审标准。

## 添加新的项目模板

以添加"青年基金"模板为例：

### 1. 创建模板文件

```bash
# 可以继承已有的 base 模板
touch scholar_writing/resources/templates/nsfc/青年基金.yaml
```

```yaml
# scholar_writing/resources/templates/nsfc/青年基金.yaml
type: nsfc
extends: nsfc/base            # 继承基础 NSFC 模板

# 覆盖特定配置
length_management:
  total_pages: 15             # 青年基金页数限制较少
  section_ratios:
    立项依据: 0.30
    研究内容: 0.20
    研究方案: 0.30
    可行性分析: 0.10
    创新点: 0.05
    研究基础: 0.05
```

`extends` 字段指定父模板，子模板只需定义差异部分。

### 2. 创建/调整 Checklist

如果评审标准与基础模板不同，在 `checklists/` 下创建对应文件。Checklist 不支持继承，需要完整定义。

```yaml
# checklists/02_立项依据.yaml
section: 立项依据
target_length: "2-4页"        # 青年基金篇幅较短
reviewers: [R1, R2, R3]

checklist:
  logic:
    - id: L1
      criterion: "研究现状综述有清晰的逻辑递进"
      weight: high
    - id: L2
      criterion: "科学问题从研究空白中自然推导而出"
      weight: critical
  # ...
```

### 3. 使用新模板

```yaml
# 项目 config.yaml
project:
  type: nsfc
  template: 青年基金
```

## 添加新的文档类型

以添加"AI 顶会论文"支持为例：

### 1. 创建模板目录

```bash
mkdir -p scholar_writing/resources/templates/paper
mkdir -p scholar_writing/resources/templates/paper/checklists
```

### 2. 定义基础模板

```yaml
# templates/paper/base.yaml
type: paper

sections:
  - name: Abstract
    file: 01_abstract.md
    checklist: checklists/abstract.yaml
    writer: writer
  - name: Introduction
    file: 02_introduction.md
    checklist: checklists/introduction.yaml
    writer: writer
  # ...

dependency_graph:
  Introduction:
    depends_on: []
    priority: 1
  Related Work:
    depends_on: [Introduction]
    priority: 2
  Method:
    depends_on: [Introduction]
    priority: 2
  # ...

review_strategy:
  section_level:
    always: [R1, R2, R3]
  global_level:
    always: [R4, R5, R7]
```

### 3. 添加章节写作规则

把 Introduction 的结构、输入和输出要求写入 `scholar_writing/resources/references/paper/` 下的章节规则，并在 `scholar_writing/resources/config/reference_registry.yaml` 中登记选择条件。通用 `writer` 角色会通过 taskpack 的 `reference_inputs` 读取这些规则。

## 添加新的审阅维度

以添加“创新性审阅”（R9）为例。

### 1. 添加审阅规则

在 `scholar_writing/resources/references/` 中新增创新性规则，明确自由分析、Checklist 评分和输出字段。

### 2. 注册到模板

在模板的 `review_strategy` 中添加：

```yaml
review_strategy:
  global_level:
    always: [R4, R5, R7, R9]     # 添加 R9
```

### 3. 更新评分权重和规则映射

在 `config.yaml` 中调整：

```yaml
score_weights:
  global:
    consistency: 0.25
    narrative: 0.30
    feasibility: 0.15
    format: 0.10
    novelty: 0.20                # 新增维度
```

## 自定义 Checklist

### 编写规范

1. **正面指令表述**：说"应当包含 X" 而非 "不要遗漏 X"
2. **唯一 ID**：每条标准分配唯一标识（如 `L1`、`D2`）
3. **权重级别**：`critical`（不通过直接标红）/ `high` / `medium`
4. **可选 few_shot**：复杂标准可附带范文片段

### 示例

```yaml
checklist:
  your_dimension:
    - id: YD1
      criterion: "核心论点有明确的数据或文献支撑"
      weight: critical
      few_shot: |
        好的示例：通过在 X 数据集上的实验（准确率 92.3%），
        验证了该方法的有效性 [1,2]。
    - id: YD2
      criterion: "技术方案描述足够具体，第三方可复现"
      weight: high
```

## 添加辅助脚本

如果需要新的确定性检查，在 `scripts/` 下创建 Python 脚本：

```python
#!/usr/bin/env python3
"""
新检查脚本的功能描述。

输入参数：项目目录路径
输出：检查结果（JSON 格式，便于 controller 解析）
"""
import argparse
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('project_dir')
    args = parser.parse_args()
    
    results = check_something(args.project_dir)
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
```

脚本应使用 Python 标准库 + PyYAML，避免引入额外依赖。
