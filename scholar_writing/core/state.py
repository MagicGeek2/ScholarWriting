from pathlib import Path

import yaml


STATE_FILE = "scores.yaml"


def create_initial_state(section_names=None):
    """Create an initial machine-readable state with a human summary."""
    sections = {}
    for name in section_names or []:
        sections[name] = {
            "status": "pending",
            "current_round": 0,
            "inner_scores": [],
            "outer_scores": [],
        }

    return {
        "phase": "initialized",
        "global_round": 0,
        "summary": "项目已初始化，等待检测输入并计算下一步动作。",
        "last_action": None,
        "next_action": None,
        "blocked_reason": None,
        "sections": sections,
    }


def state_path(project_dir):
    """Return the project scores.yaml path."""
    return Path(project_dir) / STATE_FILE


def read_state(project_dir):
    """Read scores.yaml from a project directory."""
    with open(state_path(project_dir), "r", encoding="utf-8") as f:
        state = yaml.safe_load(f) or {}
    if not isinstance(state, dict):
        raise ValueError("scores.yaml 的顶层必须是对象。")
    if "revision" in state and not isinstance(state["revision"], dict):
        raise ValueError("scores.yaml 中的 revision 必须是对象。")
    return state


def write_state(project_dir, state):
    """Write scores.yaml to a project directory."""
    path = state_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, allow_unicode=True, sort_keys=False)
    return path
