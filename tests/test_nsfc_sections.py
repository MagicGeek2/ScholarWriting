from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SECTION_FILES = {
    "摘要": "sections/01_摘要.md",
    "立项依据": "sections/02_立项依据.md",
    "研究内容": "sections/03_研究内容.md",
    "研究方案": "sections/04_研究方案.md",
    "可行性分析": "sections/05_可行性分析.md",
    "创新点": "sections/06_创新点.md",
    "研究基础": "sections/07_研究基础.md",
}


def test_nsfc_base_template_declares_canonical_section_files():
    data = yaml.safe_load((REPO_ROOT / "scholar_writing" / "resources" / "templates" / "nsfc" / "base.yaml").read_text(encoding="utf-8"))
    template_files = {section["name"]: section["file"] for section in data["sections"]}

    assert template_files == {
        name: path.removeprefix("sections/")
        for name, path in EXPECTED_SECTION_FILES.items()
    }


def test_nsfc_templates_use_the_shared_writer_role():
    template_dir = REPO_ROOT / "scholar_writing" / "resources" / "templates" / "nsfc"
    for template_path in template_dir.glob("*.yaml"):
        data = yaml.safe_load(template_path.read_text(encoding="utf-8"))
        writers = [section.get("writer") for section in data.get("sections", [])]
        assert all(writer in {None, "writer"} for writer in writers)
