from pathlib import Path

import pytest
import yaml

from scholar_writing.core.config import load_project_config
from scholar_writing.core.paths import find_repo_root
from scholar_writing.core.state import read_state
from scholar_writing.core.taskpack import build_taskpack
from scholar_writing.core.schema import validate_data


def flatten_paths(taskpack):
    paths = []
    for group in taskpack["reference_inputs"].values():
        paths.extend(item["path"] for item in group)
    return paths


def build_example_taskpack(example_name):
    repo_root = find_repo_root(Path(__file__))
    project_dir = repo_root / "examples" / example_name
    config = load_project_config(project_dir, repo_root)
    state = read_state(project_dir)
    return build_taskpack(project_dir, config, state)


def test_from_materials_taskpack_contains_architect_references():
    taskpack = build_example_taskpack("from-materials")
    paths = flatten_paths(taskpack)

    assert taskpack["action"] == "run_architect"
    assert "scholar_writing/resources/references/NSFC_GUIDE.md" in paths
    assert "scholar_writing/resources/references/NSFC_STRUCTURE_ZH.md" in paths


def test_from_outline_taskpack_contains_writer_references():
    taskpack = build_example_taskpack("from-outline")
    paths = flatten_paths(taskpack)

    assert taskpack["action"] == "run_writer"
    assert "scholar_writing/resources/references/STYLE_GUIDE_ZH.md" in paths
    assert "scholar_writing/resources/references/SENTENCE_PATTERNS_ZH.md" in paths
    assert "scholar_writing/resources/references/NSFC_STRUCTURE_ZH.md" in paths


def test_from_draft_taskpack_contains_reviewer_references():
    taskpack = build_example_taskpack("from-draft")
    paths = flatten_paths(taskpack)

    assert taskpack["action"] == "run_reviewers"
    assert "scholar_writing/resources/references/STYLE_GUIDE_ZH.md" in paths
    assert "scholar_writing/resources/references/DEAI_PATTERNS_ZH.md" in paths
    assert "scholar_writing/resources/references/NSFC_STRUCTURE_ZH.md" in paths


def test_taskpack_reference_inputs_validate_against_schema():
    repo_root = find_repo_root(Path(__file__))
    taskpack = build_example_taskpack("from-outline")

    assert validate_data("taskpack", taskpack, repo_root) == []
    for path in flatten_paths(taskpack):
        assert not Path(path).is_absolute()


def test_cli_taskpack_outputs_reference_inputs():
    repo_root = find_repo_root(Path(__file__))
    taskpack = build_example_taskpack("from-outline")
    serialized = yaml.safe_dump(taskpack, allow_unicode=True)

    assert "reference_inputs:" in serialized
    assert "STYLE_GUIDE_ZH.md" in serialized

def write_paper_project(project_dir, *, phase="initialized", language="zh"):
    (project_dir / "materials").mkdir(parents=True, exist_ok=True)
    (project_dir / "materials" / "manifest.yaml").write_text("materials: []\n", encoding="utf-8")
    (project_dir / "config.yaml").write_text(
        yaml.safe_dump({
            "project": {
                "name": "paper smoke",
                "type": "paper",
                "input_mode": "auto",
                "language": language,
            }
        }, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (project_dir / "scores.yaml").write_text(
        yaml.safe_dump({
            "phase": phase,
            "global_round": 0,
            "summary": "paper reference smoke",
            "last_action": None,
            "next_action": None,
            "blocked_reason": None,
            "sections": {
                "Introduction": {
                    "status": "pending",
                    "current_round": 0,
                }
            },
        }, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def build_temp_taskpack(project_dir):
    repo_root = find_repo_root(Path(__file__))
    config = load_project_config(project_dir, repo_root)
    state = read_state(project_dir)
    return build_taskpack(project_dir, config, state)


def test_paper_architect_taskpack_contains_paper_references(tmp_path):
    write_paper_project(tmp_path)
    taskpack = build_temp_taskpack(tmp_path)
    paths = flatten_paths(taskpack)

    assert taskpack["action"] == "run_architect"
    assert "scholar_writing/resources/references/paper/paper-lifecycle-and-outline.md" in paths
    assert "scholar_writing/resources/references/paper/citation-strategy.md" in paths


def test_paper_revision_taskpack_contains_review_and_citation_references(tmp_path):
    write_paper_project(tmp_path, phase="section_revision")
    state = yaml.safe_load((tmp_path / "scores.yaml").read_text(encoding="utf-8"))
    state["revision"] = {
        "requires_user_confirmation": False,
        "section": "Introduction",
        "issues": [{"severity": "major", "message": "evidence gap"}],
    }
    (tmp_path / "scores.yaml").write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    taskpack = build_temp_taskpack(tmp_path)
    paths = flatten_paths(taskpack)

    assert taskpack["action"] == "run_revision"
    assert taskpack["review"]["dimensions"] == ["logic", "de_ai", "completeness", "format"]
    assert "scholar_writing/resources/references/paper/paper-review-gates.md" in paths
    assert "scholar_writing/resources/references/paper/citation-strategy.md" in paths


def test_project_language_controls_output_and_reference_selection_only(tmp_path):
    taskpacks = {}
    for language in ["zh", "en"]:
        project_dir = tmp_path / language
        write_paper_project(project_dir, language=language)
        (project_dir / "planning").mkdir()
        (project_dir / "planning" / "outline.md").write_text("# Outline\n", encoding="utf-8")
        taskpacks[language] = build_temp_taskpack(project_dir)

    zh_pack = taskpacks["zh"]
    en_pack = taskpacks["en"]
    zh_paths = flatten_paths(zh_pack)
    en_paths = flatten_paths(en_pack)

    assert zh_pack["action"] == en_pack["action"] == "run_writer"
    assert zh_pack["output_language"] == "zh"
    assert en_pack["output_language"] == "en"
    assert zh_pack["reason"] == en_pack["reason"] == "检测到 planning/outline.md，可进入章节写作。"
    assert "scholar_writing/resources/references/STYLE_GUIDE_ZH.md" in zh_paths
    assert "scholar_writing/resources/references/STYLE_GUIDE_ZH.md" not in en_paths
    assert "scholar_writing/resources/references/paper/english-paper-polishing.md" not in zh_paths
    assert "scholar_writing/resources/references/paper/english-paper-polishing.md" in en_paths


def test_taskpack_rejects_unsupported_project_language(tmp_path):
    write_paper_project(tmp_path, language="fr")

    with pytest.raises(ValueError, match=r"project\.language.*zh.*en.*config\.yaml"):
        build_temp_taskpack(tmp_path)
