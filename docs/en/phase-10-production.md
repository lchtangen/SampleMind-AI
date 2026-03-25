# Phase 10 — Production and Distribution

> Sign, notarize, and distribute SampleMind as a native macOS `.app` and Windows `.exe` via GitHub Actions.

---

## Prerequisites

- Phases 1–9 complete
- Apple Developer account (for macOS signing and notarization)
- GitHub repository with Actions enabled
- `gh` CLI installed locally

---

## Goal State

- macOS `.app` signed with Developer ID and approved by Apple Gatekeeper
- Tauri bundle configured for `.dmg` (macOS) and `.msi` (Windows)
- Python sidecar bundled via PyInstaller and included in the app bundle
- Universal Binary for arm64 + x86_64 (Apple Silicon + Intel)
- GitHub Actions CI/CD: `ci.yml` (test + lint) and `release.yml` (sign + publish)
- Automatic version synchronization across all four config files

---

## 1. Version Management — One Place to Change

The project has four files that each contain the version number:

```
pyproject.toml                  ← Python package
app/src-tauri/Cargo.toml        ← Tauri/Rust app
app/src-tauri/tauri.conf.json   ← Tauri bundle
app/package.json                ← npm/pnpm
```

Use this script to update all four at once:

```bash
# filename: scripts/bump-version.sh

#!/usr/bin/env bash
# Usage: ./scripts/bump-version.sh 1.2.0

set -euo pipefail

NEW_VERSION="$1"

if [[ -z "${NEW_VERSION}" ]]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.2.0"
    exit 1
fi

echo "Bumping to version ${NEW_VERSION}..."

# pyproject.toml
sed -i "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml

# Cargo.toml (only the app package, not dependencies)
sed -i "0,/^version = \".*\"/s//version = \"${NEW_VERSION}\"/" app/src-tauri/Cargo.toml

# tauri.conf.json
sed -i "s/\"version\": \".*\"/\"version\": \"${NEW_VERSION}\"/" app/src-tauri/tauri.conf.json

# package.json
sed -i "s/\"version\": \".*\"/\"version\": \"${NEW_VERSION}\"/" app/package.json

echo "Done. Review changes with: git diff"
```

---

## 2. PyInstaller — Bundle the Python Sidecar

The Python sidecar (`server.py`) must be packaged as a standalone executable so end users do not need Python installed.

```bash
# filename: scripts/build-sidecar.sh

#!/usr/bin/env bash
# Run on macOS (for macOS bundle) and Windows (for Windows bundle).

set -euo pipefail

# Build a single-file executable from the Python sidecar
uv run pyinstaller \
    --onefile \
    --name samplemind-sidecar \
    --hidden-import samplemind.analyzer.audio_analysis \
    --hidden-import samplemind.data.repository \
    --hidden-import soundfile \
    --hidden-import librosa \
    src/samplemind/sidecar/server.py

# Copy to the Tauri resources folder (Tauri bundler picks it up from here)
cp dist/samplemind-sidecar app/src-tauri/resources/
echo "Sidecar built: app/src-tauri/resources/samplemind-sidecar"
```

PyInstaller spec file for finer-grained control:

```python
# filename: samplemind-sidecar.spec

# -*- mode: python ; coding: utf-8 -*-
# Run with: uv run pyinstaller samplemind-sidecar.spec

a = Analysis(
    ["src/samplemind/sidecar/server.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "samplemind.analyzer.audio_analysis",
        "samplemind.data.repository",
        "soundfile",
        "librosa",
        "scipy.signal",
        "scipy.fft",
        "soxr",
    ],
    hookspath=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="samplemind-sidecar",
    debug=False,
    strip=False,
    upx=True,            # Compress the executable (macOS + Linux)
    console=True,        # Keep stdout/stderr visible for debugging
)
```

In `tauri.conf.json`, declare the sidecar as an external binary:

```json
{
  "bundle": {
    "active": true,
    "resources": ["resources/*"],
    "externalBin": ["resources/samplemind-sidecar"]
  }
}
```

---

## 3. macOS — entitlements.plist

```xml
<!-- filename: app/src-tauri/entitlements.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- User selects files — OS grants access without sandbox violations -->
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>

    <!-- Access to the Music folder -->
    <key>com.apple.security.assets.music.read-write</key>
    <true/>

    <!-- Run subprocesses (Python sidecar, AppleScript) -->
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>

    <!-- AppleScript automation to other apps (FL Studio) -->
    <key>com.apple.security.automation.apple-events</key>
    <true/>

    <!-- Network client access for future API calls -->
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
</plist>
```

Enable entitlements in `tauri.conf.json`:

```json
{
  "bundle": {
    "macOS": {
      "entitlements": "entitlements.plist",
      "signingIdentity": "Developer ID Application: Your Name (TEAMID)",
      "providerShortName": "TEAMID"
    }
  }
}
```

---

## 4. Universal Binary (arm64 + x86_64)

To support both Apple Silicon (M1/M2/M3) and Intel Macs in a single `.app`:

```bash
# macOS GitHub Actions runners:
# macos-14 = Apple Silicon (arm64)
# macos-13 = Intel (x86_64)
# For a Universal Binary we need both architectures:

# Add Rust targets
$ rustup target add aarch64-apple-darwin
$ rustup target add x86_64-apple-darwin

# Tauri builds a Universal Binary automatically with:
$ pnpm tauri build --target universal-apple-darwin
```

---

## 5. CI — GitHub Actions

```yaml
# filename: .github/workflows/ci.yml

name: CI

on:
  push:
    branches: [master, main]
  pull_request:
    branches: [master, main]

jobs:
  python:
    name: Python — test + lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run pytest
        run: uv run pytest tests/ -v --tb=short

      - name: Run ruff linter
        run: uv run ruff check src/ tests/

      - name: Run ruff formatter (check only)
        run: uv run ruff format --check src/ tests/

  rust:
    name: Rust — clippy + test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Rust toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy

      - name: Install system dependencies (Tauri on Linux)
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev \
            librsvg2-dev patchelf

      - name: Cache Cargo
        uses: Swatinem/rust-cache@v2
        with:
          workspaces: "app/src-tauri -> target"

      - name: Run Clippy
        run: cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings

      - name: Run Rust tests
        run: cargo test --manifest-path app/src-tauri/Cargo.toml
```

---

## 6. Release — GitHub Actions with macOS Signing

```yaml
# filename: .github/workflows/release.yml

name: Release

on:
  push:
    tags:
      - "v*"           # Triggered by: git tag v1.0.0 && git push --tags

jobs:
  release-macos:
    name: macOS — build, sign, notarize
    runs-on: macos-14   # Apple Silicon runner
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Add Rust targets (Universal Binary)
        run: |
          rustup target add aarch64-apple-darwin
          rustup target add x86_64-apple-darwin

      - name: Install Node + pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "pnpm"
          cache-dependency-path: app/pnpm-lock.yaml

      - name: Install JS dependencies
        working-directory: app
        run: pnpm install

      - name: Install Python dependencies and build sidecar
        run: |
          uv sync --all-extras
          uv run pyinstaller samplemind-sidecar.spec
          cp dist/samplemind-sidecar app/src-tauri/resources/

      # Import the Developer ID certificate from GitHub Secrets
      - name: Import code signing certificate
        env:
          MACOS_CERTIFICATE: ${{ secrets.MACOS_CERTIFICATE }}          # Base64-encoded .p12
          MACOS_CERTIFICATE_PASSWORD: ${{ secrets.MACOS_CERTIFICATE_PASSWORD }}
          KEYCHAIN_PASSWORD: ${{ secrets.KEYCHAIN_PASSWORD }}
        run: |
          echo "$MACOS_CERTIFICATE" | base64 --decode > certificate.p12
          security create-keychain -p "$KEYCHAIN_PASSWORD" build.keychain
          security default-keychain -s build.keychain
          security unlock-keychain -p "$KEYCHAIN_PASSWORD" build.keychain
          security import certificate.p12 -k build.keychain \
            -P "$MACOS_CERTIFICATE_PASSWORD" -T /usr/bin/codesign
          security set-key-partition-list \
            -S apple-tool:,apple: -s -k "$KEYCHAIN_PASSWORD" build.keychain

      # Build Universal Binary — Tauri handles signing and notarization automatically
      - name: Build Tauri (Universal Binary)
        working-directory: app
        env:
          APPLE_CERTIFICATE: ${{ secrets.MACOS_CERTIFICATE }}
          APPLE_CERTIFICATE_PASSWORD: ${{ secrets.MACOS_CERTIFICATE_PASSWORD }}
          APPLE_ID: ${{ secrets.APPLE_ID }}                            # your@email.com
          APPLE_PASSWORD: ${{ secrets.APPLE_APP_SPECIFIC_PASSWORD }}   # App-specific password
          APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}                  # 10-character team ID
        run: pnpm tauri build --target universal-apple-darwin

      # Upload to the GitHub Release created by the tag push
      - name: Upload to GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            app/src-tauri/target/universal-apple-darwin/release/bundle/dmg/*.dmg
            app/src-tauri/target/universal-apple-darwin/release/bundle/macos/*.app.tar.gz

  release-windows:
    name: Windows — build and package
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install Node + pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Install dependencies
        working-directory: app
        run: pnpm install

      - name: Build Python sidecar (Windows)
        run: |
          uv sync --all-extras
          uv run pyinstaller samplemind-sidecar.spec
          copy dist\samplemind-sidecar.exe app\src-tauri\resources\

      - name: Build Tauri (Windows)
        working-directory: app
        run: pnpm tauri build

      - name: Upload to GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            app/src-tauri/target/release/bundle/msi/*.msi
            app/src-tauri/target/release/bundle/nsis/*.exe
```

### Required GitHub Secrets

Add these in repository Settings → Secrets → Actions:

| Secret | Description |
|--------|-------------|
| `MACOS_CERTIFICATE` | Base64-encoded Developer ID `.p12` file |
| `MACOS_CERTIFICATE_PASSWORD` | Password protecting the `.p12` file |
| `KEYCHAIN_PASSWORD` | Random password for the temporary build keychain |
| `APPLE_ID` | Apple Developer email address |
| `APPLE_APP_SPECIFIC_PASSWORD` | App-specific password from appleid.apple.com |
| `APPLE_TEAM_ID` | 10-character Team ID from developer.apple.com |

Export and encode the certificate:

```bash
# On Mac: Open Keychain Access
# Find "Developer ID Application: Your Name"
# Right-click → Export → .p12 format
# Encode to base64 for the GitHub Secret:
$ base64 -i DeveloperID.p12 | pbcopy
# Paste the value into GitHub Secret: MACOS_CERTIFICATE
```

---

## 7. Tauri Auto-Updater

```json
{
  "plugins": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://github.com/username/SampleMind-AI/releases/latest/download/latest.json"
      ],
      "dialog": true,
      "pubkey": "your-public-key-here"
    }
  }
}
```

Generate a signing key pair for secure update verification:

```bash
$ pnpm tauri signer generate -w ~/.tauri/samplemind.key
# Publish the public key in tauri.conf.json under plugins.updater.pubkey
# Keep the private key secret (GitHub Secret: TAURI_SIGNING_PRIVATE_KEY)
```

---

## 8. Complete Tauri Bundle Configuration

```json
{
  "bundle": {
    "active": true,
    "targets": "all",
    "identifier": "com.samplemind.app",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "resources": ["resources/*"],
    "externalBin": ["resources/samplemind-sidecar"],
    "copyright": "© 2025 SampleMind",
    "category": "Music",
    "shortDescription": "AI-powered sample library for FL Studio",
    "longDescription": "SampleMind analyzes and organizes your sample library with AI for fast search and seamless FL Studio integration.",
    "macOS": {
      "entitlements": "entitlements.plist",
      "signingIdentity": null,
      "providerShortName": null,
      "frameworks": [],
      "minimumSystemVersion": "12.0"
    },
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": ""
    }
  }
}
```

---

## 9. Local Release Test (macOS)

```bash
# 1. Build the sidecar
$ uv run pyinstaller samplemind-sidecar.spec
$ cp dist/samplemind-sidecar app/src-tauri/resources/

# 2. Build Tauri in release mode
$ cd app && pnpm tauri build

# 3. Find and open the .app
$ open app/src-tauri/target/release/bundle/macos/SampleMind.app

# 4. Test the AU plugin with auval (Phase 8)
$ auval -v aufx SmPl SmAI

# 5. Verify code signing
$ codesign --verify --deep --strict \
    app/src-tauri/target/release/bundle/macos/SampleMind.app
$ spctl --assess --verbose \
    app/src-tauri/target/release/bundle/macos/SampleMind.app
# Expected: "accepted" — Gatekeeper approves the app
```

---

## 10. Publishing a Release

```bash
# 1. Bump version across all four config files
$ ./scripts/bump-version.sh 1.0.0

# 2. Commit and tag
$ git add pyproject.toml app/src-tauri/Cargo.toml \
         app/src-tauri/tauri.conf.json app/package.json
$ git commit -m "chore: bump version to 1.0.0"
$ git tag v1.0.0
$ git push && git push --tags

# The GitHub Actions release.yml workflow triggers automatically.
# The finished DMG and MSI are uploaded to GitHub Releases.
```

---

## Migration Notes

- `"bundle": { "active": false }` in `tauri.conf.json` → change to `true`
- `.github/workflows/python-lint.yml` → superseded by `ci.yml` (includes linting + tests)
- Add PyInstaller as a dev dependency: `uv add --dev pyinstaller`
- macOS distribution outside TestFlight requires an Apple Developer account ($99/year)

---

## Testing Checklist

```bash
# Python CI locally
$ uv run pytest tests/ -v
$ uv run ruff check src/
$ uv run ruff format --check src/

# Rust CI locally
$ cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
$ cargo test --manifest-path app/src-tauri/Cargo.toml

# Build and test the sidecar
$ uv run pyinstaller samplemind-sidecar.spec
$ ./dist/samplemind-sidecar --socket /tmp/test.sock &
$ python -c "
import socket, json, struct
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
    s.connect('/tmp/test.sock')
    req = json.dumps({'action': 'ping'}).encode()
    s.sendall(struct.pack('>I', len(req)) + req)
    length = struct.unpack('>I', s.recv(4))[0]
    print(json.loads(s.recv(length)))
"
# Expected: {'status': 'ok', 'message': 'SampleMind sidecar running'}

# Build Tauri
$ cd app && pnpm tauri build
```

---

## Troubleshooting

**`codesign: error: The specified item could not be found`**
```bash
# Verify the certificate is imported in the keychain:
$ security find-identity -v -p codesigning
# Should show: "Developer ID Application: Your Name (TEAMID)"
```

**`notarytool: Error: HTTP status code: 401`**
```bash
# Wrong app-specific password. Generate a new one at:
# https://appleid.apple.com → Sign-In and Security → App-Specific Passwords
```

**PyInstaller: `ModuleNotFoundError: No module named 'librosa'` at runtime**
```python
# Add to the .spec file under hiddenimports:
hiddenimports=[
    "librosa",
    "librosa.core",
    "librosa.feature",
    "scipy.fft",
    "numba.core",
]
```

**Windows: `VCRUNTIME140.dll not found`**
```
Install the Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe
The Tauri MSI installer should bundle this automatically.
```
