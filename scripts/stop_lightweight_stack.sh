#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/runs/lightweight"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

stop_pid() {
  local name="$1"
  local pid="$2"
  local origin="$3"

  if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
    return
  fi

  kill "$pid" 2>/dev/null || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "$name: stopped ($origin pid $pid)"
      return
    fi
    sleep 1
  done

  kill -9 "$pid" 2>/dev/null || true
  echo "$name: force-stopped ($origin pid $pid)"
}

stop_process() {
  local name="$1"
  local pid_file="$2"

  if [ ! -f "$pid_file" ]; then
    echo "$name: not running"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if [ -z "$pid" ]; then
    rm -f "$pid_file"
    echo "$name: stale pid file removed"
    return
  fi

  stop_pid "$name" "$pid" "pid-file"
  rm -f "$pid_file"
}

stop_port_listeners() {
  local name="$1"
  local port="$2"

  local pids
  pids="$(lsof -ti tcp:"$port" -sTCP:LISTEN || true)"
  if [ -z "$pids" ]; then
    echo "$name: no listener on :$port"
    return
  fi

  for pid in $pids; do
    stop_pid "$name" "$pid" "port:$port"
  done
}

stop_process "frontend" "$FRONTEND_PID_FILE"
stop_process "backend" "$BACKEND_PID_FILE"
stop_port_listeners "frontend" "$FRONTEND_PORT"
stop_port_listeners "backend" "$BACKEND_PORT"

if lsof -ti tcp:"$FRONTEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "warning: frontend port :$FRONTEND_PORT is still occupied"
fi
if lsof -ti tcp:"$BACKEND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "warning: backend port :$BACKEND_PORT is still occupied"
fi
