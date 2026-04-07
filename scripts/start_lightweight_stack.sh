#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/runs/lightweight"
LOG_DIR="$RUN_DIR/logs"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

port_in_use() {
  local port="$1"
  lsof -ti tcp:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

cleanup_stale_pid() {
  local pid_file="$1"
  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file")"
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$pid_file"
    fi
  fi
}

is_running() {
  local pid_file="$1"
  [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null
}

cleanup_stale_pid "$BACKEND_PID_FILE"
cleanup_stale_pid "$FRONTEND_PID_FILE"

if is_running "$BACKEND_PID_FILE" || is_running "$FRONTEND_PID_FILE"; then
  echo "lightweight stack appears to be running already"
  echo "use: bash scripts/stop_lightweight_stack.sh"
  exit 1
fi

mkdir -p "$LOG_DIR"

START_LOCAL_BACKEND="${START_LOCAL_BACKEND:-1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_ORIGIN="${BACKEND_ORIGIN:-http://127.0.0.1:$BACKEND_PORT}"

if [ "$START_LOCAL_BACKEND" = "1" ] && port_in_use "$BACKEND_PORT"; then
  echo "backend port :$BACKEND_PORT is already in use"
  echo "run: bash scripts/stop_lightweight_stack.sh"
  exit 1
fi

if port_in_use "$FRONTEND_PORT"; then
  echo "frontend port :$FRONTEND_PORT is already in use"
  echo "run: bash scripts/stop_lightweight_stack.sh"
  exit 1
fi

if [ "$START_LOCAL_BACKEND" = "1" ]; then
  (
    cd "$ROOT_DIR"
    BACKEND_PORT="$BACKEND_PORT" bash "$ROOT_DIR/scripts/run_backend_light.sh"
  ) >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  echo "$BACKEND_PID" > "$BACKEND_PID_FILE"

  sleep 2
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "backend failed to start; check $BACKEND_LOG"
    exit 1
  fi
else
  rm -f "$BACKEND_PID_FILE"
  echo "skipping local backend; using BACKEND_ORIGIN=$BACKEND_ORIGIN"
fi

(
  cd "$ROOT_DIR"
  FRONTEND_PORT="$FRONTEND_PORT" BACKEND_ORIGIN="$BACKEND_ORIGIN" bash "$ROOT_DIR/scripts/run_frontend_light.sh"
) >"$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"

sleep 2
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "frontend failed to start"
  if [ "$START_LOCAL_BACKEND" = "1" ]; then
    bash "$ROOT_DIR/scripts/stop_lightweight_stack.sh"
  fi
  exit 1
fi

echo "lightweight stack started"
if [ "$START_LOCAL_BACKEND" = "1" ]; then
  echo "backend:  http://127.0.0.1:$BACKEND_PORT (pid $BACKEND_PID)"
else
  echo "backend:  remote ($BACKEND_ORIGIN)"
fi
echo "frontend: http://127.0.0.1:$FRONTEND_PORT (pid $FRONTEND_PID)"
echo "logs:     $LOG_DIR"
echo "stop:     bash scripts/stop_lightweight_stack.sh"
