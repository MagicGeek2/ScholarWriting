"""用于 ScholarWriting 辅助脚本的简体中文 argparse 界面。"""

import argparse
import re
import sys


class ChineseArgumentParser(argparse.ArgumentParser):
    """让 argparse 的帮助和参数错误保持简体中文。"""

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
    """设置 argparse 内置分组名和帮助动作。"""
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    for action in parser._actions:
        if action.dest == "help":
            action.help = "显示此帮助信息并退出"
    return parser
