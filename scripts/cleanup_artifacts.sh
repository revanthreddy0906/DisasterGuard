#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-cache-only}"

remove_path() {
  local target="$1"
  if [ -e "$target" ]; then
    rm -rf "$target"
    echo "removed: $target"
  fi
}

echo "cleanup mode: $MODE"
echo "project root: $ROOT_DIR"

case "$MODE" in
  cache-only)
    remove_path "$ROOT_DIR/frontend/.next"
    remove_path "$ROOT_DIR/frontend/.next_old"
    remove_path "$ROOT_DIR/frontend/node_modules/.cache"
    find "$ROOT_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +
    ;;
  --all-generated)
    remove_path "$ROOT_DIR/frontend/.next"
    remove_path "$ROOT_DIR/frontend/.next_old"
    remove_path "$ROOT_DIR/frontend/node_modules"
    remove_path "$ROOT_DIR/runs"
    find "$ROOT_DIR" -type d -name "__pycache__" -prune -exec rm -rf {} +
    find "$ROOT_DIR/checkpoints" -maxdepth 1 -type f \
      \( -name "evaluation_*.json" -o -name "evaluation_report.txt" -o -name "training_*.json" \) \
      -delete
    ;;
  *)
    echo "unknown mode: $MODE"
    echo "usage:"
    echo "  bash scripts/cleanup_artifacts.sh"
    echo "  bash scripts/cleanup_artifacts.sh --all-generated"
    exit 1
    ;;
esac

echo "cleanup complete"
