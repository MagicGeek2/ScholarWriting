#!/usr/bin/env bash
set -euo pipefail

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-sync)
      shift
      ;;
    --help|-h)
      cat <<'EOF'
用法：scripts/uninstall-codex.sh

从本机 Codex 中移除 ScholarWriting。

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

codex_home="${CODEX_HOME:-$HOME/.codex}"
install_dir="${SCHOLAR_WRITING_INSTALL_DIR:-$codex_home/skills/scholar-writing}"
agents_dir="${SCHOLAR_WRITING_AGENTS_DIR:-$codex_home/agents}"

rm -rf "$install_dir"
rm -f \
  "$agents_dir/scholar-architect.toml" \
  "$agents_dir/scholar-writer.toml" \
  "$agents_dir/scholar-reviewer.toml" \
  "$agents_dir/scholar-revision.toml"

echo "ScholarWriting 已从 Codex 中移除。"
