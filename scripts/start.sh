#!/usr/bin/env bash
# start.sh — Quick-start SampleMind AI services
# Usage:
#   bash scripts/start.sh           # Start Flask web UI (default)
#   bash scripts/start.sh web       # Start Flask web UI on port 5000
#   bash scripts/start.sh desktop   # Start Tauri desktop app (dev mode)
#   bash scripts/start.sh both      # Start Flask + Tauri together

set -euo pipefail

MODE="${1:-web}"
PORT="${2:-5000}"

case "$MODE" in
    web)
        echo "Starting SampleMind web UI at http://localhost:$PORT ..."
        uv run samplemind serve --port "$PORT"
        ;;
    desktop)
        echo "Starting SampleMind desktop app (Tauri dev mode)..."
        echo "Note: Flask backend will start on port 5174 automatically."
        cd app && pnpm tauri dev
        ;;
    both)
        echo "Starting Flask backend (port 5000) + Tauri desktop app..."
        uv run samplemind serve --port 5000 &
        FLASK_PID=$!
        echo "Flask started (PID $FLASK_PID)"
        sleep 1
        cd app && pnpm tauri dev
        kill "$FLASK_PID" 2>/dev/null || true
        ;;
    *)
        echo "Usage: $0 [web|desktop|both] [port]"
        echo ""
        echo "  web         Start Flask web UI (default port 5000)"
        echo "  desktop     Start Tauri desktop app in dev mode"
        echo "  both        Start Flask backend + Tauri desktop app"
        exit 1
        ;;
esac
