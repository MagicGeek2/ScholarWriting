from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10 compatibility
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_codex_repo_skill_exists_with_required_metadata():
    skill_path = REPO_ROOT / ".agents" / "skills" / "scholar-writing" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")

    assert skill_path.exists()
    assert "name: scholar-writing" in content
    assert "description:" in content
    assert "学术写作助手" in content
    assert "uv run scholar-writing next" in content
    assert "scores.yaml" in content
    assert "reference_inputs" in content
    assert "project.type: paper" in content
    assert "质量规则" in content
    assert "开发者调试" in content
    assert "平台中性" in content
    assert ".codex/agents" in content
    assert "examples/from-draft" in content
    assert "缺少 `output_language` 时按 `zh` 处理" in content


def test_codex_custom_agents_exist_with_required_fields():
    agents_dir = REPO_ROOT / ".codex" / "agents"
    expected = {
        "scholar-architect.toml": ["架构师", "规划师"],
        "scholar-writer.toml": ["写作者"],
        "scholar-reviewer.toml": ["审阅者"],
        "scholar-revision.toml": ["修订者"],
    }

    assert {path.name for path in agents_dir.glob("*.toml")} == set(expected)

    for file_name, nickname_candidates in expected.items():
        content = (agents_dir / file_name).read_text(encoding="utf-8")
        parsed = tomllib.loads(content)
        assert "name =" in content
        assert "description =" in content
        assert "developer_instructions =" in content
        assert "reference_inputs" in content
        assert parsed["nickname_candidates"] == nickname_candidates

        if file_name != "scholar-architect.toml":
            assert "缺少 `output_language` 时按 `zh` 处理" in parsed["developer_instructions"]


def test_developer_debugging_docs_cover_repo_local_workflow():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    codex_doc = (REPO_ROOT / "docs" / "codex-getting-started.md").read_text(encoding="utf-8")

    assert "源码仓库内调试" in readme
    assert "学术写作助手" in readme
    assert "repo-local skill" in readme
    assert "平台通用 repo-local skill" in readme
    assert "学术写作助手" in codex_doc
    assert "临时 Codex Home" in codex_doc
    assert "CODEX_HOME=" in codex_doc


def test_platform_prompts_require_reference_inputs():
    prompts_dir = REPO_ROOT / "scholar_writing" / "prompts"
    for file_name in ["architect.md", "writer.md", "reviewer.md", "revision.md"]:
        content = (prompts_dir / file_name).read_text(encoding="utf-8")
        assert "reference_inputs" in content
        assert "规则" in content
        if file_name != "architect.md":
            assert "缺少 `output_language` 时按 `zh` 处理" in content


def test_reviewer_instructions_define_language_specific_display_labels():
    prompt = (REPO_ROOT / "scholar_writing" / "prompts" / "reviewer.md").read_text(encoding="utf-8")
    agent = tomllib.loads(
        (REPO_ROOT / ".codex" / "agents" / "scholar-reviewer.toml").read_text(encoding="utf-8")
    )["developer_instructions"]

    for content in [prompt, agent]:
        assert "| ID | 评审标准 | 得分 | 评分依据 |" in content
        assert "## 问题清单" in content
        assert "[严重]" in content
        assert "[主要]" in content
        assert "[次要]" in content
        assert "severity" in content
        assert "critical" in content
        assert "major" in content
        assert "minor" in content
