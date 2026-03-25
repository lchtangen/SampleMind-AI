#!/usr/bin/env bash
# Phase 10 — Release Automation
# Orchestrates a full production release:
#   1. Bumps version in pyproject.toml + tauri.conf.json + Cargo.toml
#   2. Builds Python wheel (uv build)
#   3. Builds desktop app (pnpm tauri build)
#   4. Signs and notarizes macOS binary (xcrun notarytool)
#   5. Creates GitHub release with assets (gh release create)
#
# Usage: ./scripts/release.sh <version> [--dry-run]
# TODO: implement in Phase 10 — Production

set -euo pipefail

echo "ERROR: release.sh not yet implemented (Phase 10)" >&2
exit 1
