#!/usr/bin/env bash
set -euo pipefail

sync_runtime=1
replace_existing=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-sync)
      sync_runtime=0
      shift
      ;;
    --replace)
      replace_existing=1
      shift
      ;;
    --help|-h)
      cat <<'EOF'
用法：scripts/install-codex.sh [--no-sync] [--replace]

将 ScholarWriting 安装到本机 Codex。

选项：
  --replace  替换已有的 ScholarWriting Codex 安装。仅在用户确认后使用。

环境变量：
  CODEX_HOME                  默认值：$HOME/.codex
  SCHOLAR_WRITING_INSTALL_DIR 默认值：$CODEX_HOME/skills/scholar-writing
  SCHOLAR_WRITING_AGENTS_DIR  默认值：$CODEX_HOME/agents
EOF
      exit 0
      ;;
    *)
      echo "未知选项：$1" >&2
      exit 2
      ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
codex_home="${CODEX_HOME:-$HOME/.codex}"
install_dir="${SCHOLAR_WRITING_INSTALL_DIR:-$codex_home/skills/scholar-writing}"
agents_dir="${SCHOLAR_WRITING_AGENTS_DIR:-$codex_home/agents}"
runtime_dir="$install_dir/runtime"
stage_dir="$(mktemp -d "${TMPDIR:-/tmp}/scholar-writing-install.XXXXXX")"
trap 'rm -rf "$stage_dir"' EXIT
stage_source="$stage_dir/source"

if [ -z "$install_dir" ] || [ "$install_dir" = "/" ]; then
  echo "拒绝使用不安全的安装目录：$install_dir" >&2
  exit 1
fi

if [ -e "$install_dir" ] && [ "$replace_existing" -ne 1 ] && [ "$(cd "$install_dir" && pwd)" != "$repo_root" ]; then
  echo "检测到已有 ScholarWriting 安装：$install_dir" >&2
  echo "替换前请停止并询问用户。确认后使用 --replace 重新运行。" >&2
  exit 10
fi

mkdir -p "$stage_source"

copy_tree() {
  local source_path="$1"
  local target_path="$2"
  mkdir -p "$(dirname "$target_path")"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude '__pycache__' \
      --exclude '.pytest_cache' \
      --exclude '.DS_Store' \
      "$source_path/" "$target_path/"
  else
    cp -R "$source_path" "$target_path"
    find "$target_path" -name '__pycache__' -type d -prune -exec rm -rf {} +
    find "$target_path" -name '.pytest_cache' -type d -prune -exec rm -rf {} +
    find "$target_path" -name '.DS_Store' -type f -delete
  fi
}

copy_file() {
  local source_path="$1"
  local target_path="$2"
  mkdir -p "$(dirname "$target_path")"
  cp "$source_path" "$target_path"
}

# Build a minimal Codex runtime from the shared package and Codex agent definitions.
# Repository-only development files are intentionally excluded from the installation.
copy_file "$repo_root/pyproject.toml" "$stage_source/pyproject.toml"
copy_file "$repo_root/README.md" "$stage_source/README.md"
if [ -f "$repo_root/uv.lock" ]; then
  copy_file "$repo_root/uv.lock" "$stage_source/uv.lock"
fi
copy_tree "$repo_root/scholar_writing" "$stage_source/scholar_writing"
copy_tree "$repo_root/.codex/agents" "$stage_source/.codex/agents"

rm -rf "$install_dir"
mkdir -p "$install_dir" "$agents_dir" "$install_dir/bin"
mkdir -p "$runtime_dir"

if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.codex' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.DS_Store' \
    "$stage_source/" "$runtime_dir/"
else
  tar -C "$stage_source" \
    --exclude './.codex' \
    --exclude './__pycache__' \
    --exclude './.pytest_cache' \
    -cf - . | tar -C "$runtime_dir" -xf -
fi

cat > "$install_dir/SKILL.md" <<'EOF'
---
name: scholar-writing
description: 学术写作助手，面向国自然申报书、论文、初稿审阅和“写作-审阅-修订”循环优化。
---

# 学术写作助手（Codex 安装版）

本 skill 的机器 ID 是 `scholar-writing`。面向中文用户时，优先称为“学术写作助手”。

当用户要求进行学术写作、国自然/NSFC 申报书写作、论文起草、初稿审阅或迭代优化时，使用本 skill。

## 已安装内容

安装目录中包含与本文件并列的运行资源：

```text
runtime/
bin/scholar-writing
```

执行 controller 命令时使用 `bin/scholar-writing`。这个包装命令会设置 `SCHOLAR_WRITING_RUNTIME`，让 controller 在当前工作目录仍为用户写作项目的情况下找到 schemas、references、prompts 和 templates。

## 用户工作流

用户通常应在自己的写作项目目录中工作，不需要进入 ScholarWriting 源码仓库。

推荐项目结构：

```text
my-proposal/
├── materials/
├── planning/
├── sections/
├── reviews/
└── revisions/
```

如果用户还没有项目骨架，先创建：

```bash
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing init my-proposal --type nsfc --mode auto
```

然后执行：

```bash
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing next my-proposal --format json
${CODEX_HOME:-$HOME/.codex}/skills/scholar-writing/bin/scholar-writing taskpack my-proposal --format json
```

按返回的 action 和 taskpack 推进。`taskpack.reference_inputs` 是安装版运行资源中 `scholar_writing/resources/references/` 提供的质量规则；paper 项目会额外选择论文 lifecycle、章节写作、review gate、venue/visual、英文润色和 citation strategy references。

`project.language` 只控制最终学术产物的语言和参考规则选择。任务包中的对应字段是 `output_language`：`zh` 产出中文学术内容，`en` 产出英文学术内容；任务包缺少 `output_language` 时按 `zh` 处理。用户交互始终使用简体中文，不随这个设置改变。

## 写作角色

当前 Codex 环境中如果能发现以下写作角色，优先使用：

- `scholar-architect`
- `scholar-writer`
- `scholar-reviewer`
- `scholar-revision`

必须遵守 taskpack 的写入边界。涉及 `critical` 问题、核心论点变化、大范围重构、关键事实变更或跨章节广泛影响时，先向用户确认。
EOF

cat > "$install_dir/bin/scholar-writing" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runtime_dir="$(cd "$script_dir/../runtime" && pwd)"
export SCHOLAR_WRITING_RUNTIME="$runtime_dir"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$runtime_dir/.uv-cache}"
exec uv run --project "$runtime_dir" scholar-writing "$@"
EOF
chmod +x "$install_dir/bin/scholar-writing"

cp "$stage_source/.codex/agents/"*.toml "$agents_dir/"

cat > "$install_dir/install-manifest.txt" <<EOF
skill_dir=$install_dir
runtime_dir=$runtime_dir
agents_dir=$agents_dir
installed_agents=scholar-architect.toml scholar-writer.toml scholar-reviewer.toml scholar-revision.toml
EOF

if [ "$sync_runtime" -eq 1 ]; then
  if ! command -v uv >/dev/null 2>&1; then
    echo "预同步 runtime 需要 uv。请安装 uv，或使用 --no-sync 重新运行。" >&2
    exit 1
  fi
  uv sync --project "$runtime_dir"
fi

echo "ScholarWriting 已安装到 Codex。"
echo "Skill：$install_dir"
echo "Agents：$agents_dir"
echo "请重启 Codex，以刷新已安装的 Skill 和 Agents。"
