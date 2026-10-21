#!/usr/bin/env bash
# Local development server.
#   ./scripts/dev.sh
set -euo pipefail
cd "$(dirname "$0")/.."
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
exec python3 -m "${UVI:-uvi}corn" app.main:app --host "$HOST" --port "$PORT" --reload
