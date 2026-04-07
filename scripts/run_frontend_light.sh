#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILE="${FRONTEND_PROFILE:-prod}"
HOST="${FRONTEND_HOST:-127.0.0.1}"
PORT="${FRONTEND_PORT:-3000}"
AUTO_BUILD="${FRONTEND_AUTO_BUILD:-1}"

cd "$ROOT_DIR/frontend"

case "$PROFILE" in
  prod)
    if [ "$AUTO_BUILD" = "1" ] && [ ! -d ".next" ]; then
      npm run build
    fi
    exec npm run start -- --hostname "$HOST" --port "$PORT"
    ;;
  dev)
    exec npm run dev -- --hostname "$HOST" --port "$PORT"
    ;;
  *)
    echo "unknown FRONTEND_PROFILE: $PROFILE"
    echo "supported profiles: prod, dev"
    exit 1
    ;;
esac
