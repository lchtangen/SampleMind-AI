# Phase 10 Agent — Production & Release

Handles: CI/CD, code signing, notarization, feature flags, crash reporter, Universal Binary, GitHub Actions release.

## Triggers
Phase 10, CI/CD, GitHub Actions, `release.yml`, macOS signing, notarization, `codesign`, `xcrun notarytool`, entitlements, Universal Binary, `universal-apple-darwin`, feature flags, crash reporter, "prepare a release", "sign the app", "notarize"

**File patterns:** `app/src-tauri/entitlements.plist`, `.github/workflows/release.yml`, `.github/workflows/ci.yml`

**Code patterns:** `xcrun notarytool`, `codesign`, `APPLE_SIGNING_IDENTITY`, `universal-apple-darwin`

## Key Files
- `.github/workflows/python-lint.yml` — CI pipeline (ruff + pytest + clippy + alembic check)
- `.github/workflows/release.yml` — release pipeline (sign + notarize + upload)
- `app/src-tauri/entitlements.plist` — macOS sandbox entitlements
- `app/src-tauri/tauri.conf.json` — bundle id and signing config
- `docs/en/phase-10-production.md`

## macOS Required Entitlements
```xml
<key>com.apple.security.automation.apple-events</key><true/>
<key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/>
<key>com.apple.security.files.user-selected.read-write</key><true/>
<key>com.apple.security.assets.music.read-write</key><true/>
```

## CI Pipeline
```
ruff check → ruff format --check → pyright → pytest (--cov, fail_under=60) → alembic check → cargo clippy
```

## Signing & Notarization (macOS)
```bash
# Build Universal Binary
pnpm tauri build --target universal-apple-darwin
# Notarize
xcrun notarytool submit app.dmg --apple-id $APPLE_ID --team-id $TEAM_ID
```

## Rules
1. `cargo clippy -- -D warnings` must pass before any release
2. Coverage must stay ≥ 60% before release
3. `alembic check` must pass (no migration drift)
4. New entitlements require a security review comment in PR
5. All release builds must be Universal Binary on macOS (Intel + Apple Silicon)
6. Feature flags gate unreleased features in production builds

