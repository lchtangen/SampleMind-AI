#!/usr/bin/env bash
# Phase 10 — Desktop Build
# Builds the Tauri desktop app for the current platform.
# On macOS: builds universal binary (arm64 + x86_64) when --target is passed.
# On Linux: builds AppImage.
# On Windows (MSYS2/MINGW): builds NSIS installer.
#
# Usage:
#   ./scripts/build-desktop.sh                                   # native arch
#   ./scripts/build-desktop.sh --target universal-apple-darwin   # macOS universal
#   ./scripts/build-desktop.sh --debug                           # unoptimised debug build

set -euo pipefail

# ── Resolve project root (script may be called from any directory) ────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ── Read version from pyproject.toml (stdlib tomllib, no extra deps) ─────────
VERSION="$(python3 -c "
import sys, tomllib
with open('${PROJECT_ROOT}/pyproject.toml', 'rb') as f:
    d = tomllib.load(f)
print(d['project']['version'])
")"

OS="$(uname -s)"
TARGET=""
DEBUG_FLAG=""

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)
            TARGET="${2:-}"
            shift 2
            ;;
        --debug)
            DEBUG_FLAG="--debug"
            shift
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

echo "==> Building SampleMind v${VERSION} on ${OS}" >&2

# ── Prerequisite checks ───────────────────────────────────────────────────────
command -v pnpm &>/dev/null || {
    echo "ERROR: pnpm not found. Install with: npm install -g pnpm" >&2
    exit 1
}
command -v cargo &>/dev/null || {
    echo "ERROR: cargo not found. Install Rust via: https://rustup.rs" >&2
    exit 1
}

# ── Install frontend dependencies ─────────────────────────────────────────────
cd "${PROJECT_ROOT}/app"
pnpm install --frozen-lockfile

# ── Platform-specific build ───────────────────────────────────────────────────
case "$OS" in
    Darwin)
        if [[ "$TARGET" == "universal-apple-darwin" ]]; then
            echo "==> Building Universal Binary (arm64 + x86_64)..." >&2
            pnpm tauri build --target universal-apple-darwin ${DEBUG_FLAG}
        else
            echo "==> Building native macOS binary..." >&2
            pnpm tauri build ${DEBUG_FLAG}
        fi
        ;;
    Linux)
        echo "==> Building Linux AppImage..." >&2
        pnpm tauri build ${DEBUG_FLAG}
        ;;
    MINGW*|CYGWIN*|MSYS*)
        echo "==> Building Windows NSIS installer..." >&2
        pnpm tauri build ${DEBUG_FLAG}
        ;;
    *)
        echo "ERROR: Unsupported platform: ${OS}" >&2
        exit 1
        ;;
esac

echo "==> Build complete. Artifacts in app/src-tauri/target/release/bundle/" >&2
