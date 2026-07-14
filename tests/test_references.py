from pathlib import Path

import pytest

from scholar_writing.core.paths import find_repo_root
from scholar_writing.core.references import load_reference_registry, select_references
from scholar_writing.core.schema import validate_data


def paths_for(reference_inputs):
    paths = []
    for group in reference_inputs.values():
        paths.extend(item["path"] for item in group)
    return paths


def test_reference_registry_validates_and_paths_exist():
    repo_root = find_repo_root(Path(__file__))
    registry = load_reference_registry(repo_root)

    assert validate_data("reference_registry", registry, repo_root) == []
    for item in registry["references"].values():
        path = Path(item["path"])
        assert not path.is_absolute()
        assert (repo_root / path).exists()
    for section_path in registry["section_patterns"]["nsfc"].values():
        path = Path(section_path)
        assert not path.is_absolute()
        assert (repo_root / path).exists()


def test_select_references_for_nsfc_architect():
    selected = select_references(
        project_type="nsfc",
        action="run_architect",
        agent_role="architect",
    )
    paths = paths_for(selected)

    assert "scholar_writing/resources/references/NSFC_GUIDE.md" in paths
    assert "scholar_writing/resources/references/NSFC_STRUCTURE_ZH.md" in paths
    assert all(not Path(path).is_absolute() for path in paths)


def test_select_references_for_nsfc_writer_section():
    selected = select_references(
        project_type="nsfc",
        action="run_writer",
        agent_role="writer",
        target_section="02_立项依据",
    )
    paths = paths_for(selected)

    assert "scholar_writing/resources/references/STYLE_GUIDE_ZH.md" in paths
    assert "scholar_writing/resources/references/SENTENCE_PATTERNS_ZH.md" in paths
    assert "scholar_writing/resources/references/patterns/00_通用.md" in paths
    assert "scholar_writing/resources/references/patterns/02_立项依据.md" in paths
    assert "scholar_writing/resources/references/NSFC_STRUCTURE_ZH.md" in paths


def test_select_references_for_deai_review():
    selected = select_references(
        project_type="nsfc",
        action="run_reviewers",
        agent_role="reviewer",
        review_dimensions=["de_ai"],
    )
    paths = paths_for(selected)

    assert "scholar_writing/resources/references/DEAI_PATTERNS_ZH.md" in paths
    assert "scholar_writing/resources/references/STYLE_GUIDE_ZH.md" in paths


def test_missing_reference_file_raises_clear_error(tmp_path):
    registry = {
        "version": 1,
        "references": {
            "missing": {
                "path": "scholar_writing/resources/references/MISSING.md",
                "purpose": "missing test",
                "applies_to": {
                    "project_types": ["nsfc"],
                    "agent_roles": ["writer"],
                    "actions": ["run_writer"],
                },
            }
        },
        "section_patterns": {},
    }

    with pytest.raises(FileNotFoundError, match="参考文件不存在"):
        select_references(
            project_type="nsfc",
            action="run_writer",
            agent_role="writer",
            registry=registry,
            repo_root=tmp_path,
        )

def test_select_references_for_paper_architect():
    selected = select_references(
        project_type="paper",
        action="run_architect",
        agent_role="architect",
        language="zh",
    )
    paths = paths_for(selected)

    assert "scholar_writing/resources/references/paper/paper-lifecycle-and-outline.md" in paths
    assert "scholar_writing/resources/references/paper/citation-strategy.md" in paths
    assert all(not Path(path).is_absolute() for path in paths)


def test_paper_reference_files_exist_and_preserve_boundaries():
    repo_root = find_repo_root(Path(__file__))
    paper_dir = repo_root / "scholar_writing" / "resources" / "references" / "paper"
    expected = {
        "paper-lifecycle-and-outline.md",
        "paper-section-writing.md",
        "paper-style-routing.md",
        "paper-review-gates.md",
        "peer-review-rubric.md",
        "venue-and-visual-contract.md",
        "english-paper-polishing.md",
        "citation-strategy.md",
    }

    assert {path.name for path in paper_dir.glob("*.md")} >= expected
    assert "不能把愿望写成结果" in (paper_dir / "paper-lifecycle-and-outline.md").read_text(encoding="utf-8")
    assert "不代表任何会议或期刊的官方模板" in (paper_dir / "venue-and-visual-contract.md").read_text(encoding="utf-8")
    assert "不能替代 Zotero/CSL" in (paper_dir / "citation-strategy.md").read_text(encoding="utf-8")


def test_paper_review_references_route_human_labels_by_output_language():
    repo_root = find_repo_root(Path(__file__))
    paper_dir = repo_root / "scholar_writing" / "resources" / "references" / "paper"
    rubric = (paper_dir / "peer-review-rubric.md").read_text(encoding="utf-8")
    gates = (paper_dir / "paper-review-gates.md").read_text(encoding="utf-8")

    for content in [rubric, gates]:
        assert "output_language" in content
        assert "critical" in content
        assert "major" in content
        assert "minor" in content
    assert "概要 / 优点 / 主要问题 / 次要问题 / 可执行修订计划" in rubric
    assert "Summary / Strengths / Major concerns / Minor concerns / Actionable revision plan" in rubric
    assert "严重 / 主要 / 次要" in gates
