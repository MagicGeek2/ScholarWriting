from pathlib import Path
import re

import yaml
from jsonschema import Draft7Validator

from .paths import schema_path


SCHEMA_TYPE_NAMES_ZH = {
    "array": "列表",
    "boolean": "布尔值",
    "integer": "整数",
    "null": "空值",
    "number": "数字",
    "object": "对象",
    "string": "字符串",
}


def format_schema_type(expected):
    """Render one or more JSON Schema type names in Simplified Chinese."""
    values = expected if isinstance(expected, list) else [expected]
    return "、".join(SCHEMA_TYPE_NAMES_ZH.get(value, str(value)) for value in values)


def format_schema_context(error):
    """Render and deduplicate nested branch errors."""
    details = []
    for child in error.context:
        path = ".".join(str(part) for part in child.relative_path)
        message = format_schema_error(child)
        detail = f"{path}: {message}" if path else message
        if detail not in details:
            details.append(detail)
    return "；".join(details)


def format_schema_error(error):
    """Render jsonschema validation details in Simplified Chinese."""
    if error.validator == "required":
        match = re.fullmatch(r"'(.+)' is a required property", error.message)
        if match:
            return f"缺少必填属性：{match.group(1)!r}"
        missing = [
            repr(name)
            for name in error.validator_value
            if not isinstance(error.instance, dict) or name not in error.instance
        ]
        return f"缺少必填属性：{', '.join(missing)}"
    if error.validator == "enum":
        allowed = ", ".join(repr(value) for value in error.validator_value)
        return f"值 {error.instance!r} 不在允许范围内：{allowed}"
    if error.validator == "type":
        return f"值的类型不符合要求，应为：{format_schema_type(error.validator_value)}"
    if error.validator == "minimum":
        return f"数值不能小于 {error.validator_value}"
    if error.validator == "maximum":
        return f"数值不能大于 {error.validator_value}"
    if error.validator == "minLength":
        return f"字符串长度不能少于 {error.validator_value}"
    if error.validator == "maxLength":
        return f"字符串长度不能超过 {error.validator_value}"
    if error.validator == "minItems":
        return f"列表项目数不能少于 {error.validator_value}"
    if error.validator == "maxItems":
        return f"列表项目数不能超过 {error.validator_value}"
    if error.validator == "minProperties":
        return f"对象至少需要 {error.validator_value} 个属性"
    if error.validator == "uniqueItems":
        return "列表项目不能重复"
    if error.validator == "pattern":
        return f"字符串不符合格式规则：{error.validator_value}"
    if error.validator == "additionalProperties":
        allowed = set(error.schema.get("properties", {}))
        extras = [repr(name) for name in error.instance if name not in allowed]
        detail = f"：{', '.join(extras)}" if extras else ""
        return f"存在未允许的额外属性{detail}"
    if error.validator in {"oneOf", "anyOf"}:
        requirement = (
            "值必须且只能符合一种允许结构"
            if error.validator == "oneOf"
            else "值至少需要符合一种允许结构"
        )
        details = format_schema_context(error)
        return f"{requirement}；具体问题：{details}" if details else requirement
    return f"未满足 Schema 规则：{error.validator}"


def load_schema(data_type, repo_root=None):
    """Load a YAML JSON Schema by data type."""
    path = schema_path(data_type, repo_root)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_data(data_type, data, repo_root=None):
    """Validate data and return a compact list of error strings."""
    schema = load_schema(data_type, repo_root)
    validator = Draft7Validator(schema)
    errors = []
    for error in validator.iter_errors(data):
        path = ".".join(str(p) for p in error.absolute_path)
        message = format_schema_error(error)
        if path:
            errors.append(f"{path}: {message}")
        else:
            errors.append(message)
    return sorted(errors)


def load_yaml(path):
    """Load a YAML file as a dict."""
    with open(Path(path), "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}
