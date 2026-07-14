import argparse
import json
import re
from pathlib import Path
import sys

import yaml

from .core.config import load_project_config
from .core.paths import find_repo_root, framework_root
from .core.project import init_project
from .core.schema import validate_data
from .core.state import create_initial_state, read_state, state_path
from .core.taskpack import build_taskpack
from .core.workflow import advance_state, next_action as compute_next_action


EXPECTED_CLI_EXCEPTIONS = (
    FileNotFoundError,
    IsADirectoryError,
    NotADirectoryError,
    PermissionError,
    UnicodeError,
    yaml.YAMLError,
    ValueError,
)


class ChineseArgumentParser(argparse.ArgumentParser):
    """Keep argparse's human-facing help and errors in Simplified Chinese."""

    def format_usage(self):
        return super().format_usage().replace("usage:", "用法：", 1)

    def format_help(self):
        return super().format_help().replace("usage:", "用法：", 1)

    def error(self, message):
        replacements = (
            ("the following arguments are required: ", "以下参数为必填项："),
            ("unrecognized arguments: ", "无法识别的参数："),
            ("expected one argument", "需要一个参数"),
            ("invalid choice: ", "无效选择："),
            ("invalid int value: ", "无效的整数："),
            ("invalid float value: ", "无效的浮点数："),
            ("argument ", "参数 "),
        )
        for source, target in replacements:
            message = message.replace(source, target)
        message = re.sub(r"\(choose from (.*)\)$", r"（可选值：\1）", message)
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: 参数错误：{message}\n")


def localize_parser(parser):
    """Localize argparse's built-in group and help labels."""
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    for action in parser._actions:
        if action.dest == "help":
            action.help = "显示此帮助信息并退出"
    return parser


def format_cli_error(error):
    """Render expected user, file, YAML, and configuration errors in Chinese."""
    path = getattr(error, "filename", None)
    if isinstance(error, FileNotFoundError):
        if path:
            return f"文件不存在：{path}"
        detail = str(error)
        if re.search(r"[\u4e00-\u9fff]", detail):
            return detail
        return "找不到所需文件；请检查输入路径。"
    if isinstance(error, IsADirectoryError):
        return f"需要文件，但收到目录：{path}" if path else "需要文件，但收到目录。"
    if isinstance(error, NotADirectoryError):
        return f"路径中的某一部分不是目录：{path}" if path else "输入路径包含非目录项。"
    if isinstance(error, PermissionError):
        return f"无权访问文件或目录：{path}" if path else "无权访问指定文件或目录。"
    if isinstance(error, UnicodeError):
        return "文件编码无效；请确认输入文件使用 UTF-8。"
    if isinstance(error, yaml.YAMLError):
        mark = getattr(error, "problem_mark", None)
        if mark is not None:
            return f"YAML 内容无效：第 {mark.line + 1} 行，第 {mark.column + 1} 列。"
        return "YAML 内容无效；请检查文件格式。"
    detail = str(error)
    if re.search(r"[\u4e00-\u9fff]", detail):
        return detail
    return "配置或输入值无效；请检查命令参数与项目配置。"


def emit(data, output_format):
    """Print data in the requested output format."""
    if output_format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(yaml.safe_dump(data, allow_unicode=True, sort_keys=False))


def load_state_or_initial(project_dir):
    """Read scores.yaml when present, otherwise return an initial state."""
    if state_path(project_dir).exists():
        return read_state(project_dir)
    return create_initial_state()


def command_status(args):
    state = load_state_or_initial(args.project_dir)
    emit(state, args.format)
    return 0


def command_next(args):
    repo_root = find_repo_root(Path(__file__))
    project_dir = Path(args.project_dir)
    config = load_project_config(project_dir, repo_root)
    state = load_state_or_initial(project_dir)
    emit(compute_next_action(project_dir, config, state), args.format)
    return 0


def command_init(args):
    repo_root = find_repo_root(Path(__file__))
    result = init_project(args.project_dir, repo_root, project_type=args.type, mode=args.mode, name=args.name)
    emit(result, args.format)
    return 0


def command_validate(args):
    repo_root = find_repo_root(Path(__file__))
    scripts_dir = framework_root(repo_root) / "scripts"
    sys.path.insert(0, str(scripts_dir))
    import validate as legacy_validate

    results = legacy_validate.validate_all(args.project_dir)
    data = {
        "valid": all(r.valid for r in results),
        "results": [r.to_dict() for r in results],
    }
    emit(data, args.format)
    return 0 if data["valid"] else 1


def command_taskpack(args):
    repo_root = find_repo_root(Path(__file__))
    project_dir = Path(args.project_dir)
    config = load_project_config(project_dir, repo_root)
    state = load_state_or_initial(project_dir)
    emit(build_taskpack(project_dir, config, state), args.format)
    return 0


def command_advance(args):
    repo_root = find_repo_root(Path(__file__))
    project_dir = Path(args.project_dir)
    config = load_project_config(project_dir, repo_root)
    state = load_state_or_initial(project_dir)
    if args.event_file:
        event = yaml.safe_load(Path(args.event_file).read_text(encoding="utf-8")) or {}
        if not isinstance(event, dict):
            raise ValueError("事件 YAML 的顶层必须是对象。")
        if event.get("kind") == "review_result":
            errors = validate_data("review_result", event, repo_root)
            if errors:
                raise ValueError(f"review_result 事件无效：{'；'.join(errors)}")
        state = advance_state(state, config, event=event)
        action = state.get("next_action", compute_next_action(project_dir, config, state))
    else:
        action = compute_next_action(project_dir, config, state)
        state["last_action"] = "advance_state"
        state["next_action"] = action
    if action["action"] == "ask_user":
        state["phase"] = "blocked"
        state["blocked_reason"] = action.get("reason")
    from .core.state import write_state
    write_state(project_dir, state)
    emit({"project_dir": str(project_dir), "next_action": action}, args.format)
    return 0


def build_parser():
    parser = localize_parser(ChineseArgumentParser(description="ScholarWriting 确定性工作流 CLI"))
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=ChineseArgumentParser,
    )

    init = localize_parser(subparsers.add_parser("init", help="创建标准的 ScholarWriting 项目骨架"))
    init.add_argument("project_dir", help="项目目录")
    init.add_argument("--type", choices=["nsfc", "paper"], default="nsfc")
    init.add_argument("--mode", choices=["auto", "from_materials", "from_outline", "from_draft"], default="auto")
    init.add_argument("--name", default=None)
    init.add_argument("--format", choices=["json", "yaml"], default="yaml")
    init.set_defaults(func=command_init)

    validate = localize_parser(subparsers.add_parser("validate", help="校验 ScholarWriting 项目"))
    validate.add_argument("project_dir", help="项目目录")
    validate.add_argument("--format", choices=["json", "yaml"], default="yaml")
    validate.set_defaults(func=command_validate)

    status = localize_parser(subparsers.add_parser("status", help="读取并输出项目 scores.yaml"))
    status.add_argument("project_dir", help="项目目录")
    status.add_argument("--format", choices=["json", "yaml"], default="yaml")
    status.set_defaults(func=command_status)

    next_cmd = localize_parser(subparsers.add_parser("next", help="计算下一步工作流动作"))
    next_cmd.add_argument("project_dir", help="项目目录")
    next_cmd.add_argument("--format", choices=["json", "yaml"], default="yaml")
    next_cmd.set_defaults(func=command_next)

    taskpack = localize_parser(subparsers.add_parser("taskpack", help="生成当前 Agent 任务包"))
    taskpack.add_argument("project_dir", help="项目目录")
    taskpack.add_argument("--format", choices=["json", "yaml"], default="yaml")
    taskpack.set_defaults(func=command_taskpack)

    advance = localize_parser(subparsers.add_parser("advance", help="把当前下一步动作写入 scores.yaml"))
    advance.add_argument("project_dir", help="项目目录")
    advance.add_argument("--event-file", default=None, help="YAML 事件文件，例如 review_result payload")
    advance.add_argument("--format", choices=["json", "yaml"], default="yaml")
    advance.set_defaults(func=command_advance)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except EXPECTED_CLI_EXCEPTIONS as error:
        print(f"ScholarWriting 错误：{format_cli_error(error)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
