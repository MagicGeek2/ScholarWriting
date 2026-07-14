import os
import subprocess
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_script(script_name, codex_home, *extra_args):
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    return subprocess.run(
        ["bash", str(REPO_ROOT / "scripts" / script_name), "--no-sync", *extra_args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_codex_install_and_uninstall_roundtrip(tmp_path):
    codex_home = tmp_path / "codex-home"

    install = run_script("install-codex.sh", codex_home)

    assert install.returncode == 0, install.stderr
    skill_dir = codex_home / "skills" / "scholar-writing"
    runtime_dir = skill_dir / "runtime"
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "bin" / "scholar-writing").exists()
    assert os.access(skill_dir / "bin" / "scholar-writing", os.X_OK)
    assert (runtime_dir / "pyproject.toml").exists()
    assert (runtime_dir / "scholar_writing" / "resources" / "references" / "STYLE_GUIDE_ZH.md").exists()
    assert (runtime_dir / "scholar_writing" / "resources" / "references" / "paper" / "citation-strategy.md").exists()
    assert (runtime_dir / "scholar_writing" / "cli.py").exists()
    assert (runtime_dir / "scholar_writing" / "prompts" / "writer.md").exists()
    assert not (runtime_dir / ".git").exists()
    assert not (runtime_dir / ".venv").exists()
    assert not (runtime_dir / ".codex").exists()
    assert not (runtime_dir / ".agents").exists()
    assert not (runtime_dir / "SKILL.md").exists()
    assert {path.name for path in runtime_dir.iterdir()} <= {
        "README.md",
        "pyproject.toml",
        "scholar_writing",
        "uv.lock",
    }
    assert sorted(path.relative_to(skill_dir).as_posix() for path in skill_dir.rglob("SKILL.md")) == ["SKILL.md"]
    assert (codex_home / "agents" / "scholar-writer.toml").exists()
    installed_skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    assert "学术写作助手" in installed_skill
    assert "paper 项目" in installed_skill
    assert "project.language" in installed_skill
    assert "用户交互始终使用简体中文" in installed_skill
    assert "缺少 `output_language` 时按 `zh` 处理" in installed_skill
    installed_writer_prompt = (
        runtime_dir / "scholar_writing" / "prompts" / "writer.md"
    ).read_text(encoding="utf-8")
    assert "缺少 `output_language` 时按 `zh` 处理" in installed_writer_prompt
    assert "ScholarWriting 已安装到 Codex" in install.stdout

    uninstall = run_script("uninstall-codex.sh", codex_home)

    assert uninstall.returncode == 0, uninstall.stderr
    assert "ScholarWriting 已从 Codex 中移除" in uninstall.stdout
    assert not skill_dir.exists()
    assert not (codex_home / "agents" / "scholar-writer.toml").exists()


def test_installed_wrapper_sets_runtime_and_runs_help(tmp_path):
    codex_home = tmp_path / "codex-home"
    install = run_script("install-codex.sh", codex_home)
    assert install.returncode == 0, install.stderr

    wrapper = codex_home / "skills" / "scholar-writing" / "bin" / "scholar-writing"
    content = wrapper.read_text(encoding="utf-8")
    assert "UV_CACHE_DIR" in content

    result = subprocess.run(
        [str(wrapper), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "ScholarWriting 确定性工作流 CLI" in result.stdout


def test_install_stops_when_previous_skill_payload_exists(tmp_path):
    codex_home = tmp_path / "codex-home"
    stale_file = codex_home / "skills" / "scholar-writing" / "skills" / "pipeline" / "SKILL.md"
    stale_file.parent.mkdir(parents=True)
    stale_file.write_text("old payload\n", encoding="utf-8")

    install = run_script("install-codex.sh", codex_home)

    assert install.returncode == 10
    assert "检测到已有 ScholarWriting 安装" in install.stderr
    assert "使用 --replace 重新运行" in install.stderr
    assert stale_file.exists()


def test_install_help_is_chinese(tmp_path):
    result = run_script("install-codex.sh", tmp_path / "codex-home", "--help")

    assert result.returncode == 0
    assert "将 ScholarWriting 安装到本机 Codex" in result.stdout
    assert "选项：" in result.stdout


def test_install_replaces_previous_skill_payload_when_explicitly_allowed(tmp_path):
    codex_home = tmp_path / "codex-home"
    stale_file = codex_home / "skills" / "scholar-writing" / "skills" / "pipeline" / "SKILL.md"
    stale_file.parent.mkdir(parents=True)
    stale_file.write_text("old payload\n", encoding="utf-8")

    install = run_script("install-codex.sh", codex_home, "--replace")

    assert install.returncode == 0, install.stderr
    assert not stale_file.exists()


def test_repository_does_not_expose_install_shim_as_root_skill():
    assert not (REPO_ROOT / "SKILL.md").exists()


def test_install_can_finalize_generic_skill_install_location(tmp_path):
    codex_home = tmp_path / "codex-home"
    generic_skill_dir = codex_home / "skills" / "scholar-writing"
    ignore = shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache")
    shutil.copytree(REPO_ROOT, generic_skill_dir, ignore=ignore)

    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    result = subprocess.run(
        ["bash", str(generic_skill_dir / "scripts" / "install-codex.sh"), "--no-sync"],
        cwd=generic_skill_dir,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (generic_skill_dir / "SKILL.md").exists()
    assert (generic_skill_dir / "runtime" / "pyproject.toml").exists()
    assert (generic_skill_dir / "bin" / "scholar-writing").exists()
    assert {path.name for path in (generic_skill_dir / "runtime").iterdir()} <= {
        "README.md",
        "pyproject.toml",
        "scholar_writing",
        "uv.lock",
    }
    assert not (generic_skill_dir / "scripts" / "install-codex.sh").exists()
