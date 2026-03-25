# Fase 10 — Produksjon og distribusjon

> Signer, notariser og distribuer SampleMind som en native macOS `.app` og Windows `.exe` via GitHub Actions.

---

## Forutsetninger

- Fase 1–9 fullført
- Apple Developer-konto (for macOS-signering og notarisering)
- GitHub-repository med Actions aktivert
- `gh`-verktøyet installert lokalt

---

## Mål etter denne fasen

- macOS `.app` signert med Developer ID og godkjent av Apple Gatekeeper
- Tauri-bundle konfigurert for `.dmg` (macOS) og `.msi` (Windows)
- Python-sidecar pakket inn via PyInstaller og inkludert i bundle-et
- Universal Binary for arm64 + x86_64 (Apple Silicon + Intel)
- GitHub Actions CI/CD: `ci.yml` (test + lint) og `release.yml` (sign + publish)
- Automatisk versjonsynkronisering på tvers av fire config-filer

---

## 1. Versjonskontroll — ett sted å endre

Prosjektet har fire filer som alle inneholder versjonsnummeret:

```
pyproject.toml           ← Python-pakken
app/src-tauri/Cargo.toml ← Tauri/Rust-app
app/src-tauri/tauri.conf.json ← Tauri-bundle
app/package.json         ← npm/pnpm
```

Bruk dette skriptet for å oppdatere alle på én gang:

```bash
# filename: scripts/bump-version.sh

#!/usr/bin/env bash
# Bruk: ./scripts/bump-version.sh 1.2.0

set -euo pipefail

NEW_VERSION="$1"

if [[ -z "${NEW_VERSION}" ]]; then
    echo "Bruk: $0 <versjon>"
    echo "Eksempel: $0 1.2.0"
    exit 1
fi

echo "Oppdaterer til versjon ${NEW_VERSION}..."

# pyproject.toml
sed -i "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml

# Cargo.toml (kun app-pakken, ikke avhengigheter)
sed -i "0,/^version = \".*\"/s//version = \"${NEW_VERSION}\"/" app/src-tauri/Cargo.toml

# tauri.conf.json
sed -i "s/\"version\": \".*\"/\"version\": \"${NEW_VERSION}\"/" app/src-tauri/tauri.conf.json

# package.json
sed -i "s/\"version\": \".*\"/\"version\": \"${NEW_VERSION}\"/" app/package.json

echo "Ferdig. Sjekk endringene med: git diff"
```

---

## 2. PyInstaller — pakk Python-sidecaren

Python-sidecaren (`server.py`) må pakkes som en selvstendig kjørbar fil slik at sluttbrukere ikke trenger å installere Python.

```bash
# filename: scripts/build-sidecar.sh

#!/usr/bin/env bash
# Kjøres på macOS (for macOS-bundle) og Windows (for Windows-bundle).

set -euo pipefail

# Bygg enkelfil-executable av Python-sidecaren
uv run pyinstaller \
    --onefile \
    --name samplemind-sidecar \
    --hidden-import samplemind.analyzer.audio_analysis \
    --hidden-import samplemind.data.repositories.sample_repository \
    --hidden-import soundfile \
    --hidden-import librosa \
    src/samplemind/sidecar/server.py

# Kopier til Tauri-ressursmappe (Tauri bundler henter herfra)
cp dist/samplemind-sidecar app/src-tauri/resources/
echo "Sidecar bygget: app/src-tauri/resources/samplemind-sidecar"
```

PyInstaller-spesifikasjon for finere kontroll:

```python
# filename: samplemind-sidecar.spec

# -*- mode: python ; coding: utf-8 -*-
# Kjør med: uv run pyinstaller samplemind-sidecar.spec

a = Analysis(
    ["src/samplemind/sidecar/server.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "samplemind.analyzer.audio_analysis",
        "samplemind.data.repositories.sample_repository",
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
    upx=True,            # Komprimér executable (macOS + Linux)
    console=True,        # stdout/stderr synlig for feilsøking
)
```

I `tauri.conf.json`, konfigurer sidecar som en ekstern kjørbar fil:

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
    <!-- Brukeren velger filer — OS gir tilgang uten sandbox-brudd -->
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>

    <!-- Musikk-mappe -->
    <key>com.apple.security.assets.music.read-write</key>
    <true/>

    <!-- Kjøre delprosesser (Python-sidecar, AppleScript) -->
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>

    <!-- AppleScript til andre apps (FL Studio) -->
    <key>com.apple.security.automation.apple-events</key>
    <true/>

    <!-- Nettverkstilkobling for fremtidige API-kall -->
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
</plist>
```

Aktiver entitlements i `tauri.conf.json`:

```json
{
  "bundle": {
    "macOS": {
      "entitlements": "entitlements.plist",
      "signingIdentity": "Developer ID Application: Ditt Navn (TEAMID)",
      "providerShortName": "TEAMID"
    }
  }
}
```

---

## 4. Universal Binary (arm64 + x86_64)

For å støtte både Apple Silicon (M1/M2/M3) og Intel Mac-er i én enkelt `.app`:

```bash
# macOS GitHub Actions runner (macos-14 = Apple Silicon, macos-13 = Intel)
# For Universal Binary trenger vi begge arkitekturene:

# Bygg Rust for begge targets
$ rustup target add aarch64-apple-darwin
$ rustup target add x86_64-apple-darwin

# Tauri bygger Universal Binary automatisk med:
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

      - name: Installer uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Installer avhengigheter
        run: uv sync --all-extras

      - name: Kjør pytest
        run: uv run pytest tests/ -v --tb=short

      - name: Kjør ruff linter
        run: uv run ruff check src/ tests/

      - name: Kjør ruff formatter (check-only)
        run: uv run ruff format --check src/ tests/

  rust:
    name: Rust — clippy + test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Installer Rust toolchain
        uses: dtolnay/rust-toolchain@stable
        with:
          components: clippy

      - name: Installer system-avhengigheter (Tauri på Linux)
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev \
            librsvg2-dev patchelf

      - name: Cache Cargo
        uses: Swatinem/rust-cache@v2
        with:
          workspaces: "app/src-tauri -> target"

      - name: Kjør Clippy
        run: cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings

      - name: Kjør Rust-tester
        run: cargo test --manifest-path app/src-tauri/Cargo.toml
```

---

## 6. Release — GitHub Actions med macOS-signering

```yaml
# filename: .github/workflows/release.yml

name: Release

on:
  push:
    tags:
      - "v*"           # Utløses av: git tag v1.0.0 && git push --tags

jobs:
  release-macos:
    name: macOS — bygg, signer, notariser
    runs-on: macos-14   # Apple Silicon runner
    steps:
      - uses: actions/checkout@v4

      - name: Installer uv
        uses: astral-sh/setup-uv@v4

      - name: Installer Rust targets (Universal Binary)
        run: |
          rustup target add aarch64-apple-darwin
          rustup target add x86_64-apple-darwin

      - name: Installer Node + pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "pnpm"
          cache-dependency-path: app/pnpm-lock.yaml

      - name: Installer JS-avhengigheter
        working-directory: app
        run: pnpm install

      - name: Installer Python-avhengigheter + bygg sidecar
        run: |
          uv sync --all-extras
          uv run pyinstaller samplemind-sidecar.spec
          cp dist/samplemind-sidecar app/src-tauri/resources/

      # Importer Developer ID-sertifikat fra GitHub Secrets
      - name: Importer kodesigneringssertifikat
        env:
          MACOS_CERTIFICATE: ${{ secrets.MACOS_CERTIFICATE }}          # Base64-kodet .p12
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

      # Bygg Universal Binary og signer automatisk via Tauri
      - name: Bygg Tauri (Universal Binary)
        working-directory: app
        env:
          APPLE_CERTIFICATE: ${{ secrets.MACOS_CERTIFICATE }}
          APPLE_CERTIFICATE_PASSWORD: ${{ secrets.MACOS_CERTIFICATE_PASSWORD }}
          APPLE_ID: ${{ secrets.APPLE_ID }}                              # din@epost.no
          APPLE_PASSWORD: ${{ secrets.APPLE_APP_SPECIFIC_PASSWORD }}     # App-spesifikt passord
          APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}                    # 10-tegns team-ID
        run: pnpm tauri build --target universal-apple-darwin

      # Last opp til GitHub Release (taggen utløste dette workflowen)
      - name: Last opp til GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            app/src-tauri/target/universal-apple-darwin/release/bundle/dmg/*.dmg
            app/src-tauri/target/universal-apple-darwin/release/bundle/macos/*.app.tar.gz

  release-windows:
    name: Windows — bygg og pakk
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Installer uv
        uses: astral-sh/setup-uv@v4

      - name: Installer Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Installer Node + pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 22

      - name: Installer avhengigheter
        working-directory: app
        run: pnpm install

      - name: Bygg Python-sidecar (Windows)
        run: |
          uv sync --all-extras
          uv run pyinstaller samplemind-sidecar.spec
          copy dist\samplemind-sidecar.exe app\src-tauri\resources\

      - name: Bygg Tauri (Windows)
        working-directory: app
        run: pnpm tauri build

      - name: Last opp til GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            app/src-tauri/target/release/bundle/msi/*.msi
            app/src-tauri/target/release/bundle/nsis/*.exe
```

### Nødvendige GitHub Secrets

Legg til disse i repoets Settings → Secrets → Actions:

| Secret | Beskrivelse |
|--------|-------------|
| `MACOS_CERTIFICATE` | Base64-kodet Developer ID `.p12`-fil |
| `MACOS_CERTIFICATE_PASSWORD` | Passordet for `.p12`-filen |
| `KEYCHAIN_PASSWORD` | Tilfeldig passord for midlertidig keychain |
| `APPLE_ID` | Apple Developer-e-post |
| `APPLE_APP_SPECIFIC_PASSWORD` | App-spesifikt passord fra appleid.apple.com |
| `APPLE_TEAM_ID` | 10-tegns Team ID fra developer.apple.com |

Eksporter sertifikatet:

```bash
# På Mac: Åpne Keychain Access
# Finn "Developer ID Application: Ditt Navn"
# Høyreklikk → Export → .p12-format
# Koder til base64 for GitHub Secret:
$ base64 -i DeveloperID.p12 | pbcopy
# Lim inn verdien i GitHub Secret: MACOS_CERTIFICATE
```

---

## 7. Tauri Auto-oppdaterer

```json
{
  "plugins": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://github.com/username/SampleMind-AI/releases/latest/download/latest.json"
      ],
      "dialog": true,
      "pubkey": "ditt-offentlige-nøkkel-her"
    }
  }
}
```

Generer nøkkelpar for signeringssikkert oppdatering:

```bash
$ pnpm tauri signer generate -w ~/.tauri/samplemind.key
# Publiser den offentlige nøkkelen i tauri.conf.json
# Hold den private nøkkelen hemmelig (GitHub Secret: TAURI_SIGNING_PRIVATE_KEY)
```

---

## 8. Tauri bundle-konfigurasjon (komplett)

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
    "shortDescription": "AI-drevet sample-bibliotek for FL Studio",
    "longDescription": "SampleMind analyserer og organiserer ditt sample-bibliotek med AI for rask søk og integrasjon med FL Studio.",
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

## 9. Lokal release-test (macOS)

```bash
# 1. Bygg sidecar
$ uv run pyinstaller samplemind-sidecar.spec
$ cp dist/samplemind-sidecar app/src-tauri/resources/

# 2. Bygg Tauri i release-modus
$ cd app && pnpm tauri build

# 3. Finn og åpne .app
$ open app/src-tauri/target/release/bundle/macos/SampleMind.app

# 4. Test med auval (AU-plugin, fra fase 8)
$ auval -v aufx SmPl SmAI

# 5. Verifiser kodesignering
$ codesign --verify --deep --strict \
    app/src-tauri/target/release/bundle/macos/SampleMind.app
$ spctl --assess --verbose \
    app/src-tauri/target/release/bundle/macos/SampleMind.app
# Forventet: "accepted" — Gatekeeper godkjenner appen
```

---

## 10. Publiser en release

```bash
# 1. Bump versjon på tvers av alle fire config-filer
$ ./scripts/bump-version.sh 1.0.0

# 2. Commit og tag
$ git add pyproject.toml app/src-tauri/Cargo.toml \
         app/src-tauri/tauri.conf.json app/package.json
$ git commit -m "chore: bump version to 1.0.0"
$ git tag v1.0.0
$ git push && git push --tags

# GitHub Actions release.yml utløses automatisk.
# Ferdig DMG og MSI lastes opp til GitHub Releases.
```

---

## Migrasjonsnotater

- `"bundle": { "active": false }` i `tauri.conf.json` → endre til `true`
- `.github/workflows/python-lint.yml` → erstattes av `ci.yml` (inkluderer linting + tester)
- PyInstaller legges til i `pyproject.toml` som dev-avhengighet: `uv add --dev pyinstaller`
- macOS: krever Apple Developer-konto ($99/år) for distribusjon utenfor TestFlight

---

## Testsjekkliste

```bash
# Python CI lokalt
$ uv run pytest tests/ -v
$ uv run ruff check src/
$ uv run ruff format --check src/

# Rust CI lokalt
$ cargo clippy --manifest-path app/src-tauri/Cargo.toml -- -D warnings
$ cargo test --manifest-path app/src-tauri/Cargo.toml

# Bygg sidecar
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
# Forventet: {'status': 'ok', 'message': 'SampleMind sidecar running'}

# Bygg Tauri
$ cd app && pnpm tauri build
```

---

## Feilsøking

**`codesign: error: The specified item could not be found`**
```bash
# Sjekk at sertifikatet er importert i keychain:
$ security find-identity -v -p codesigning
# Bør vise: "Developer ID Application: Ditt Navn (TEAMID)"
```

**`notarytool: Error: HTTP status code: 401`**
```bash
# Feil app-spesifikt passord. Generer et nytt på:
# https://appleid.apple.com → Sign-In and Security → App-Specific Passwords
```

**PyInstaller: `ModuleNotFoundError: No module named 'librosa'` ved kjøretid**
```python
# Legg til i .spec under hiddenimports:
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
Installer Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe
Tauri MSI-installeren bør inkludere dette automatisk.
```
