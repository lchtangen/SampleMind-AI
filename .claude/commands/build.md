# /build — Build the Project

Build the Tauri desktop app, Python package, or JUCE plugin.

## Arguments

$ARGUMENTS
Targets:
  (none)       — build Tauri app in dev mode
  dev          — start Tauri dev server with HMR
  release      — build Tauri production bundle (.dmg / .msi / .AppImage)
  universal    — build macOS Universal Binary (arm64 + x86_64) — macOS only
  python       — build Python wheel with uv build
  sidecar      — build PyInstaller sidecar binary
  plugin       — build JUCE plugin with CMake
  check        — check if all build tools are installed

---

Build the target specified in: $ARGUMENTS

**Step 1 — Detect build target:**
Parse $ARGUMENTS to determine what to build.

**Step 2 — Check prerequisites based on target:**

*For Tauri targets (dev/release/universal):*
- Check `pnpm` is installed: `pnpm --version`
- Check `cargo` is installed: `cargo --version`
- Check node_modules exist: `app/node_modules/` directory
- If not: run `cd app && pnpm install` first
- Check `app/src-tauri/resources/samplemind-sidecar` exists for release builds

*For python:*
- Check `uv` is installed

*For sidecar:*
- Check PyInstaller: `uv run pyinstaller --version`
- Check spec file exists: `samplemind-sidecar.spec`

*For plugin:*
- Check CMake: `cmake --version`
- Check JUCE submodule: `plugin/JUCE/CMakeLists.txt`
- Check Xcode CLI (macOS): `xcode-select -p`

**Step 3 — Run the build:**

```bash
# dev
cd app && pnpm tauri dev

# release
cd app && pnpm tauri build

# universal (macOS only)
cd app && pnpm tauri build --target universal-apple-darwin

# python
uv build

# sidecar
uv run pyinstaller samplemind-sidecar.spec
cp dist/samplemind-sidecar app/src-tauri/resources/

# plugin
cd plugin && cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build

# check
echo "Checking build tools..." && pnpm --version && cargo --version && uv --version && cmake --version
```

**Step 4 — Report output:**
Show where the built artifact is located:
- Tauri release: `app/src-tauri/target/release/bundle/`
- Python wheel: `dist/`
- Sidecar: `dist/samplemind-sidecar`
- JUCE plugin: `plugin/build/SampleMind_artefacts/`

Suggest next steps (e.g., install AU plugin to `~/Library/Audio/Plug-Ins/Components/`).
