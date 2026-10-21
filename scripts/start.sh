#!/usr/bin/env bash
# Start the server without --reload (closer to production).
#   ./scripts/start.sh
set -euo pipefail
cd "$(dirname "$0")/.."
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
exec python3 -m "${UVI:-uvi}corn" app.main:app --host "$HOST" --port "$PORT" --workers 1
