# Phase 10 Agent — Production & CI/CD

Handles: GitHub Actions CI, macOS signing/notarization, Windows Trusted Signing, feature flags, update channels, crash analytics.

## Triggers
- Phase 10, CI/CD, GitHub Actions, signing, notarization, release, feature flag, update channel, crash report, Sentry

## Key Files
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `src/samplemind/core/feature_flags.py`
- `src/samplemind/core/crash_reporter.py`

## CI Matrix

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
    python-version: ["3.13"]
```

## Release Pipeline

```
push tag v*.*.* →
  ├── macOS: pnpm tauri build --target universal-apple-darwin
  │     → codesign → notarize → staple → .dmg
  └── Windows: pnpm tauri build
        → Trusted Signing → .msi + .exe
```

## Feature Flag Rules

```python
FLAG_DEFAULTS = {
    "semantic_search":  {"enabled": False, "rollout_pct": 0},
    "ai_curation":      {"enabled": False, "rollout_pct": 0},
    "cloud_sync":       {"enabled": False, "rollout_pct": 0},
    "waveform_editor":  {"enabled": True,  "rollout_pct": 100},
    "playlist_builder": {"enabled": True,  "rollout_pct": 100},
}
```

## Rules
1. CI must pass: `uv run ruff check` + `uv run pytest -m "not slow"` + `cargo clippy -- -D warnings`
2. Coverage minimum: 60% (`fail_under = 60` in pyproject.toml)
3. `cargo clippy` warnings = CI failure (no suppressions without comment)
4. Signing secrets in GitHub Secrets only — never in code
5. Update channels: `stable` (monthly), `beta` (weekly), `nightly` (daily)
6. Crash reports: `~/.samplemind/crashes/crash_*.json`, submitted to Sentry on next startup

