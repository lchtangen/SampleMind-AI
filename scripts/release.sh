#!/usr/bin/env bash
# Phase 10 — Release Automation
# Orchestrates a full production release:
#   1. Validates semver argument
#   2. Bumps version in pyproject.toml, app/src-tauri/tauri.conf.json, app/src-tauri/Cargo.toml
#   3. Builds Python wheel (uv build)
#   4. Builds desktop app (./scripts/build-desktop.sh)
#   5. Signs and notarizes macOS binary (xcrun notarytool) — macOS only
#   6. Creates GitHub release draft with built assets (gh release create)
#
# Usage:
#   ./scripts/release.sh 1.2.3            # full release
#   ./scripts/release.sh 1.2.3 --dry-run  # print steps without executing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OS="$(uname -s)"

# ── Parse arguments ───────────────────────────────────────────────────────────
VERSION="${1:-}"
DRY_RUN=false

for arg in "${@:2}"; do
    if [[ "$arg" == "--dry-run" ]]; then
        DRY_RUN=true
    fi
done

# ── Validate semver ───────────────────────────────────────────────────────────
if [[ -z "$VERSION" ]]; then
    echo "Usage: $0 <version> [--dry-run]" >&2
    echo "  version: semver string, e.g. 1.2.3" >&2
    exit 1
fi

if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    echo "ERROR: Version '${VERSION}' is not valid semver (expected X.Y.Z)" >&2
    exit 1
fi

echo "==> Release SampleMind v${VERSION}${DRY_RUN:+ (DRY RUN)}" >&2

# ── Helper: run or print ──────────────────────────────────────────────────────
run() {
    if $DRY_RUN; then
        echo "  [DRY RUN] $*" >&2
    else
        "$@"
    fi
}

# ── Step 1: Bump version in pyproject.toml ────────────────────────────────────
echo "==> Step 1: Bumping pyproject.toml version to ${VERSION}" >&2
run python3 -c "
import re, pathlib
p = pathlib.Path('${PROJECT_ROOT}/pyproject.toml')
content = p.read_text()
updated = re.sub(r'^version = \"[^\"]+\"', 'version = \"${VERSION}\"', content, count=1, flags=re.MULTILINE)
p.write_text(updated)
print('  pyproject.toml updated')
"

# ── Step 2: Bump version in tauri.conf.json ───────────────────────────────────
echo "==> Step 2: Bumping tauri.conf.json version to ${VERSION}" >&2
TAURI_CONF="${PROJECT_ROOT}/app/src-tauri/tauri.conf.json"
if [[ -f "$TAURI_CONF" ]]; then
    run python3 -c "
import json, pathlib
p = pathlib.Path('${TAURI_CONF}')
conf = json.loads(p.read_text())
conf['version'] = '${VERSION}'
p.write_text(json.dumps(conf, indent=2) + '\n')
print('  tauri.conf.json updated')
"
else
    echo "  WARNING: ${TAURI_CONF} not found — skipping" >&2
fi

# ── Step 3: Bump version in Cargo.toml ───────────────────────────────────────
echo "==> Step 3: Bumping Cargo.toml version to ${VERSION}" >&2
CARGO_TOML="${PROJECT_ROOT}/app/src-tauri/Cargo.toml"
if [[ -f "$CARGO_TOML" ]]; then
    run python3 -c "
import re, pathlib
p = pathlib.Path('${CARGO_TOML}')
content = p.read_text()
# Only bump the first [package] version (not dependency versions)
updated = re.sub(r'^version = \"[^\"]+\"', 'version = \"${VERSION}\"', content, count=1, flags=re.MULTILINE)
p.write_text(updated)
print('  Cargo.toml updated')
"
else
    echo "  WARNING: ${CARGO_TOML} not found — skipping" >&2
fi

# ── Step 4: Build Python wheel ────────────────────────────────────────────────
echo "==> Step 4: Building Python wheel" >&2
run uv build --wheel --out-dir "${PROJECT_ROOT}/dist"

# ── Step 5: Build desktop app ─────────────────────────────────────────────────
echo "==> Step 5: Building desktop app" >&2
if [[ "$OS" == "Darwin" ]]; then
    run "${SCRIPT_DIR}/build-desktop.sh" --target universal-apple-darwin
else
    run "${SCRIPT_DIR}/build-desktop.sh"
fi

# ── Step 6: macOS notarization (requires Apple Developer credentials) ─────────
if [[ "$OS" == "Darwin" ]]; then
    echo "==> Step 6: macOS notarization" >&2

    BUNDLE_DIR="${PROJECT_ROOT}/app/src-tauri/target/universal-apple-darwin/release/bundle/dmg"
    DMG_FILE="$(find "${BUNDLE_DIR}" -name "*.dmg" 2>/dev/null | head -1 || true)"

    if [[ -z "$DMG_FILE" ]]; then
        echo "  WARNING: No .dmg found at ${BUNDLE_DIR} — skipping notarization" >&2
    elif [[ -z "${APPLE_ID:-}" || -z "${APPLE_TEAM_ID:-}" || -z "${APPLE_PASSWORD:-}" ]]; then
        echo "  WARNING: APPLE_ID / APPLE_TEAM_ID / APPLE_PASSWORD not set — skipping notarization" >&2
        echo "  Set these env vars to enable automatic notarization." >&2
    else
        run xcrun notarytool submit \
            "${DMG_FILE}" \
            --apple-id "${APPLE_ID}" \
            --team-id "${APPLE_TEAM_ID}" \
            --password "${APPLE_PASSWORD}" \
            --wait
        run xcrun stapler staple "${DMG_FILE}"
        echo "  Notarization complete: ${DMG_FILE}" >&2
    fi
else
    echo "==> Step 6: Notarization skipped (macOS only)" >&2
fi

# ── Step 7: Create GitHub release draft ───────────────────────────────────────
echo "==> Step 7: Creating GitHub release draft" >&2

command -v gh &>/dev/null || {
    echo "  WARNING: gh (GitHub CLI) not found — skipping release creation" >&2
    echo "  Install with: https://cli.github.com" >&2
    if ! $DRY_RUN; then
        exit 0
    fi
}

# Collect assets
ASSETS=()
WHEEL="$(find "${PROJECT_ROOT}/dist" -name "samplemind-${VERSION}*.whl" 2>/dev/null | head -1 || true)"
[[ -n "$WHEEL" ]] && ASSETS+=("$WHEEL")

if [[ "$OS" == "Darwin" ]]; then
    DMG_ASSET="$(find "${PROJECT_ROOT}/app/src-tauri/target" -name "*.dmg" 2>/dev/null | head -1 || true)"
    [[ -n "$DMG_ASSET" ]] && ASSETS+=("$DMG_ASSET")
elif [[ "$OS" == "Linux" ]]; then
    APPIMAGE="$(find "${PROJECT_ROOT}/app/src-tauri/target" -name "*.AppImage" 2>/dev/null | head -1 || true)"
    [[ -n "$APPIMAGE" ]] && ASSETS+=("$APPIMAGE")
fi

ASSET_ARGS=()
for asset in "${ASSETS[@]}"; do
    ASSET_ARGS+=("$asset")
done

run gh release create "v${VERSION}" \
    --title "SampleMind v${VERSION}" \
    --generate-notes \
    --draft \
    "${ASSET_ARGS[@]}"

echo "==> Release v${VERSION} complete!" >&2
