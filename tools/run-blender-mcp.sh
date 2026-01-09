#!/usr/bin/env bash
set -euo pipefail

# Simple dev script to run the Python MCP server located under third_party/blender-mcp
# Usage: ./tools/run-blender-mcp.sh

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
THIRD_PARTY="$ROOT_DIR/third_party/blender-mcp"

MCP_HOST="${MCP_HOST:-127.0.0.1}"
MCP_PORT="${MCP_PORT:-9876}"
# Check for newer python versions if default is too old or just prefer them
if command -v python3.11 &>/dev/null; then
  PYTHON="${PYTHON:-python3.11}"
elif command -v python3.10 &>/dev/null; then
  PYTHON="${PYTHON:-python3.10}"
else
  PYTHON="${PYTHON:-python3}"
fi

if [ ! -d "$THIRD_PARTY" ]; then
  echo "third_party/blender-mcp not found. Add it as a git submodule or copy the blender-mcp sources into $THIRD_PARTY"
  echo "Example: git submodule add https://github.com/murdadrum/blender-mcp third_party/blender-mcp"
  exit 1
fi

cd "$THIRD_PARTY"

echo "Starting MCP server from $THIRD_PARTY (host=$MCP_HOST port=$MCP_PORT)"

# Create venv if not present
if [ ! -d .venv ]; then
  $PYTHON -m venv .venv
  source .venv/bin/activate
  if [ -f requirements.txt ]; then
    pip install -r requirements.txt
  fi
else
  source .venv/bin/activate
fi

# Run the MCP server entrypoint. Upstream may provide `main.py` or `server.py` — adjust if needed.
if [ -f main.py ]; then
  $PYTHON main.py --host "$MCP_HOST" --port "$MCP_PORT"
elif [ -f server.py ]; then
  $PYTHON server.py --host "$MCP_HOST" --port "$MCP_PORT"
else
  echo "No known entrypoint (main.py/server.py). Start the MCP server manually inside $THIRD_PARTY."
  exit 1
fi
