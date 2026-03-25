#!/usr/bin/env bash
# Phase 6 / Phase 10 — Desktop Build
# Builds the Tauri desktop app for the current platform.
# On macOS: builds universal binary (arm64 + x86_64).
# On Linux: builds AppImage.
# On Windows (cross-compiled via CI): builds NSIS installer.
#
# Usage: ./scripts/build-desktop.sh [--target universal-apple-darwin]
# TODO: implement in Phase 6 — Tauri Desktop App

set -euo pipefail

echo "ERROR: build-desktop.sh not yet implemented (Phase 6)" >&2
exit 1
