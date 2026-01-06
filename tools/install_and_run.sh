#!/usr/bin/env bash
set -euo pipefail

# Simple installer / runner for Chiron3D (macOS-friendly)
# Usage: ./tools/install_and_run.sh [--install-addon]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="/tmp/chiron_logs"
mkdir -p "$LOG_DIR"

echo "Starting Chiron from: $ROOT_DIR"

echo "-- Backend: server --"
pushd "$ROOT_DIR/server" >/dev/null
echo "Installing server dependencies (this may take a minute)..."
npm install --no-audit --no-fund || true
echo "Starting Node backend with mock MCP enabled..."
USE_MOCK_MCP=true MCP_PORT=9876 node index.js > "$LOG_DIR/server.log" 2>&1 &
SERVER_PID=$!
echo "Backend PID: $SERVER_PID (logs: $LOG_DIR/server.log)"
popd >/dev/null

if [ -d "$ROOT_DIR/demo" ]; then
  echo "-- Frontend: demo --"
  pushd "$ROOT_DIR/demo" >/dev/null
  npm install --no-audit --no-fund || true
  npm run dev > "$LOG_DIR/demo.log" 2>&1 &
  DEMO_PID=$!
  echo "Demo PID: $DEMO_PID (logs: $LOG_DIR/demo.log)"
  popd >/dev/null
fi

if [ -d "$ROOT_DIR/web" ]; then
  echo "-- Frontend: web (optional) --"
  echo "If you prefer the web UI, run it separately: cd $ROOT_DIR/web && npm install && npm run dev"
fi

INSTALL_ADDON=0
if [ "${1:-}" = "--install-addon" ]; then
  INSTALL_ADDON=1
fi

if [ "$INSTALL_ADDON" = "1" ]; then
  echo "-- Installing Blender add-on to user addons folder --"
  BLENDER_ADDONS_DIR="$HOME/Library/Application Support/Blender/5.0/scripts/addons/chiron"
  mkdir -p "$BLENDER_ADDONS_DIR"
  rsync -a --delete "$ROOT_DIR/chiron/" "$BLENDER_ADDONS_DIR/"
  echo "Addon copied to: $BLENDER_ADDONS_DIR"
fi

echo
echo "Chiron launched. Logs:"
echo "  Backend: $LOG_DIR/server.log"
[ -f "$LOG_DIR/demo.log" ] && echo "  Demo:    $LOG_DIR/demo.log"
echo
echo "To stop services:"
echo "  pkill -f 'node index.js' || true"
echo "  pkill -f 'vite' || true"
echo
echo "Tip: open the backend logs with: tail -f $LOG_DIR/server.log"

exit 0
