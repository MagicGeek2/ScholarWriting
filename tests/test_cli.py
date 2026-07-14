import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import scholar_writing.cli as cli
from scholar_writing.core.state import create_initial_state, write_state


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "scholar_writing.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_cli_help():
    result = run_cli("--help")

    assert result.returncode == 0
    assert result.stdout.startswith("用法：")
    assert "ScholarWriting 确定性工作流 CLI" in result.stdout
    assert "创建标准的 ScholarWriting 项目骨架" in result.stdout
    assert "位置参数:" in result.stdout
    assert "选项:" in result.stdout
    assert "显示此帮助信息并退出" in result.stdout
    assert "show this help message" not in result.stdout


def test_cli_argument_errors_are_chinese():
    invalid_command = run_cli("not-a-command")
    missing_project = run_cli("init")
    invalid_type = run_cli("init", "/tmp/scholar-invalid", "--type", "invalid")

    assert invalid_command.returncode == 2
    assert "参数 command" in invalid_command.stderr
    assert "无效选择" in invalid_command.stderr
    assert "invalid choice" not in invalid_command.stderr

    assert missing_project.returncode == 2
    assert "以下参数为必填项：project_dir" in missing_project.stderr
    assert "the following arguments are required" not in missing_project.stderr

    assert invalid_type.returncode == 2
    assert "参数 --type" in invalid_type.stderr
    assert "无效选择" in invalid_type.stderr
    assert "invalid choice" not in invalid_type.stderr


def test_cli_status_reads_scores_yaml(tmp_path):
    write_state(tmp_path, create_initial_state(["摘要"]))

    result = run_cli("status", str(tmp_path), "--format", "json")
    data = json.loads(result.stdout)

    assert result.returncode == 0
    assert data["phase"] == "initialized"
    assert "摘要" in data["sections"]


def test_cli_next_outputs_action(tmp_path):
    (tmp_path / "materials").mkdir()
    (tmp_path / "materials" / "manifest.yaml").write_text("materials: []\n", encoding="utf-8")
    write_state(tmp_path, create_initial_state(["摘要"]))

    result = run_cli("next", str(tmp_path), "--format", "json")
    data = json.loads(result.stdout)

    assert result.returncode == 0
    assert data["action"] == "run_architect"


def test_cli_init_creates_project_config_and_state(tmp_path):
    project_dir = tmp_path / "project"

    result = run_cli("init", str(project_dir), "--type", "nsfc", "--mode", "auto", "--name", "测试项目")

    assert result.returncode == 0, result.stderr
    assert (project_dir / "config.yaml").exists()
    assert (project_dir / "scores.yaml").exists()
    assert (project_dir / "materials").is_dir()
    assert (project_dir / "planning").is_dir()
    assert (project_dir / "sections").is_dir()
    config = yaml.safe_load((project_dir / "config.yaml").read_text(encoding="utf-8"))
    assert config["project"]["name"] == "测试项目"
    assert config["project"]["input_mode"] == "auto"


def test_cli_validate_project_reports_valid_results(tmp_path):
    result = run_cli("init", str(tmp_path), "--type", "nsfc", "--mode", "auto")
    assert result.returncode == 0, result.stderr

    result = run_cli("validate", str(tmp_path), "--format", "json")
    data = json.loads(result.stdout)

    assert result.returncode == 0
    assert data["valid"] is True
    assert {item["type"] for item in data["results"]} >= {"config", "scores"}


def test_cli_taskpack_outputs_architect_pack(tmp_path):
    (tmp_path / "materials").mkdir()
    (tmp_path / "materials" / "manifest.yaml").write_text("materials: []\n", encoding="utf-8")
    write_state(tmp_path, create_initial_state(["摘要"]))

    result = run_cli("taskpack", str(tmp_path), "--format", "json")
    data = json.loads(result.stdout)

    assert result.returncode == 0
    assert data["agent_role"] == "architect"
    assert data["action"] == "run_architect"
    assert data["outputs"]["outline_path"] == "planning/outline.md"


def test_cli_taskpack_reports_unsupported_project_language_in_chinese(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "project:\n  language: fr\n",
        encoding="utf-8",
    )

    result = run_cli("taskpack", str(tmp_path), "--format", "json")

    assert result.returncode == 2
    assert "project.language" in result.stderr
    assert "仅允许 zh 或 en" in result.stderr
    assert "请修改 config.yaml" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_taskpack_reports_invalid_config_structure_in_chinese(tmp_path):
    (tmp_path / "config.yaml").write_text("project: invalid\n", encoding="utf-8")

    result = run_cli("taskpack", str(tmp_path), "--format", "json")

    assert result.returncode == 2
    assert "config.yaml" in result.stderr
    assert "project" in result.stderr
    assert "对象" in result.stderr
    assert "Traceback" not in result.stderr
    assert "AttributeError" not in result.stderr
    assert "has no attribute" not in result.stderr


def test_cli_advance_reports_missing_event_file_in_chinese(tmp_path):
    missing_event = tmp_path / "missing-event.yaml"

    result = run_cli("advance", str(tmp_path), "--event-file", str(missing_event))

    assert result.returncode == 2
    assert f"文件不存在：{missing_event}" in result.stderr
    assert "Traceback" not in result.stderr
    assert "No such file or directory" not in result.stderr


def test_cli_advance_reports_malformed_yaml_in_chinese(tmp_path):
    event_file = tmp_path / "bad-event.yaml"
    event_file.write_text("kind: [\n", encoding="utf-8")

    result = run_cli("advance", str(tmp_path), "--event-file", str(event_file))

    assert result.returncode == 2
    assert "YAML 内容无效" in result.stderr
    assert "行" in result.stderr
    assert "列" in result.stderr
    assert "Traceback" not in result.stderr
    assert "ParserError" not in result.stderr
    assert "while parsing" not in result.stderr


def test_cli_next_reports_invalid_scores_structure_in_chinese(tmp_path):
    (tmp_path / "scores.yaml").write_text("invalid\n", encoding="utf-8")

    result = run_cli("next", str(tmp_path), "--format", "json")

    assert result.returncode == 2
    assert "scores.yaml" in result.stderr
    assert "对象" in result.stderr
    assert "Traceback" not in result.stderr
    assert "AttributeError" not in result.stderr


def test_cli_next_reports_invalid_revision_structure_in_chinese(tmp_path):
    (tmp_path / "scores.yaml").write_text(
        """phase: section_revision
global_round: 0
sections: {}
revision: invalid
""",
        encoding="utf-8",
    )

    result = run_cli("next", str(tmp_path), "--format", "json")

    assert result.returncode == 2
    assert "scores.yaml" in result.stderr
    assert "revision" in result.stderr
    assert "对象" in result.stderr
    assert "Traceback" not in result.stderr
    assert "AttributeError" not in result.stderr


def test_cli_advance_reports_invalid_event_structure_in_chinese(tmp_path):
    event_file = tmp_path / "event.yaml"
    event_file.write_text("- invalid\n", encoding="utf-8")

    result = run_cli("advance", str(tmp_path), "--event-file", str(event_file))

    assert result.returncode == 2
    assert "事件 YAML" in result.stderr
    assert "对象" in result.stderr
    assert "Traceback" not in result.stderr
    assert "AttributeError" not in result.stderr


@pytest.mark.parametrize(
    ("event_content", "expected_path"),
    [
        ("kind: review_result\ndata: invalid\n", "data"),
        (
            """kind: review_result
data:
  section: 摘要
  round: 1
  scores:
    logic: 85
  issues:
    - invalid
""",
            "data.issues.0",
        ),
    ],
)
def test_cli_advance_reports_invalid_review_result_shape_in_chinese(
    tmp_path,
    event_content,
    expected_path,
):
    event_file = tmp_path / "review-result.yaml"
    event_file.write_text(event_content, encoding="utf-8")

    result = run_cli("advance", str(tmp_path), "--event-file", str(event_file))

    assert result.returncode == 2
    assert "review_result 事件无效" in result.stderr
    assert expected_path in result.stderr
    assert "对象" in result.stderr
    assert "Traceback" not in result.stderr
    assert "AttributeError" not in result.stderr
    assert "has no attribute" not in result.stderr


def test_cli_main_does_not_swallow_unexpected_errors(monkeypatch, tmp_path):
    def raise_unexpected_error(args):
        raise RuntimeError("unexpected internal failure")

    monkeypatch.setattr(cli, "command_status", raise_unexpected_error)

    with pytest.raises(RuntimeError, match="unexpected internal failure"):
        cli.main(["status", str(tmp_path)])


def test_cli_advance_records_next_action(tmp_path):
    (tmp_path / "sections").mkdir()
    (tmp_path / "sections" / "01_摘要.md").write_text("# 摘要\n", encoding="utf-8")
    write_state(tmp_path, create_initial_state(["摘要"]))

    result = run_cli("advance", str(tmp_path), "--format", "json")
    data = json.loads(result.stdout)
    state = yaml.safe_load((tmp_path / "scores.yaml").read_text(encoding="utf-8"))

    assert result.returncode == 0
    assert data["next_action"]["action"] == "run_reviewers"
    assert state["next_action"]["action"] == "run_reviewers"
    assert state["last_action"] == "advance_state"


def test_cli_advance_event_file_records_review_result(tmp_path):
    (tmp_path / "sections").mkdir()
    (tmp_path / "sections" / "01_摘要.md").write_text("# 摘要\n", encoding="utf-8")
    write_state(tmp_path, create_initial_state(["摘要"]))
    event_file = tmp_path / "review-result.yaml"
    event_file.write_text(
        """
kind: review_result
data:
  section: 摘要
  round: 1
  scores:
    logic: 70
    de_ai: 72
    completeness: 74
  issues:
    - severity: major
      message: 论证链不足
""",
        encoding="utf-8",
    )

    result = run_cli("advance", str(tmp_path), "--event-file", str(event_file), "--format", "json")
    data = json.loads(result.stdout)
    state = yaml.safe_load((tmp_path / "scores.yaml").read_text(encoding="utf-8"))

    assert result.returncode == 0, result.stderr
    assert data["next_action"]["action"] == "run_revision"
    assert state["phase"] == "section_revision"
    assert state["sections"]["摘要"]["current_score"] < 80


def test_cli_advance_event_file_can_complete_section(tmp_path):
    (tmp_path / "sections").mkdir()
    (tmp_path / "sections" / "01_摘要.md").write_text("# 摘要\n", encoding="utf-8")
    write_state(tmp_path, create_initial_state(["摘要"]))
    event_file = tmp_path / "review-pass.yaml"
    event_file.write_text(
        """
kind: review_result
data:
  section: 摘要
  round: 2
  scores:
    logic: 86
    de_ai: 82
    completeness: 88
  issues: []
""",
        encoding="utf-8",
    )

    result = run_cli("advance", str(tmp_path), "--event-file", str(event_file), "--format", "json")
    data = json.loads(result.stdout)
    state = yaml.safe_load((tmp_path / "scores.yaml").read_text(encoding="utf-8"))

    assert result.returncode == 0, result.stderr
    assert data["next_action"]["action"] == "stop_complete"
    assert state["phase"] == "complete"
    assert state["sections"]["摘要"]["status"] == "approved"


def test_cli_simulated_review_revision_review_loop(tmp_path):
    (tmp_path / "sections").mkdir()
    (tmp_path / "sections" / "01_摘要.md").write_text("# 摘要\n", encoding="utf-8")
    write_state(tmp_path, create_initial_state(["摘要"]))

    low_review = REPO_ROOT / "tests" / "fixtures" / "review-low.yaml"
    pass_review = REPO_ROOT / "tests" / "fixtures" / "review-pass.yaml"

    result = run_cli("advance", str(tmp_path), "--event-file", str(low_review), "--format", "json")
    data = json.loads(result.stdout)
    assert result.returncode == 0, result.stderr
    assert data["next_action"]["action"] == "run_revision"

    result = run_cli("advance", str(tmp_path), "--event-file", str(pass_review), "--format", "json")
    data = json.loads(result.stdout)
    state = yaml.safe_load((tmp_path / "scores.yaml").read_text(encoding="utf-8"))

    assert result.returncode == 0, result.stderr
    assert data["next_action"]["action"] == "stop_complete"
    assert state["sections"]["摘要"]["status"] == "approved"
    assert len(state["sections"]["摘要"]["inner_scores"]) == 2


def test_cli_next_for_example_input_modes():
    cases = {
        "examples/from-materials": "run_architect",
        "examples/from-outline": "run_writer",
        "examples/from-draft": "run_reviewers",
    }

    for project_dir, expected_action in cases.items():
        result = run_cli("next", project_dir, "--format", "json")
        data = json.loads(result.stdout)

        assert result.returncode == 0, result.stderr
        assert data["action"] == expected_action
