# /build — Build the Project

Build the Tauri desktop app, Python package, or JUCE plugin.

## Arguments

$ARGUMENTS
Targets:
  (none)       — build Tauri app in dev mode
  dev          — start Tauri dev server with HMR
  release      — build Tauri production bundle (.dmg / .msi / .AppImage)
  universal    — build macOS Universal Binary (arm64 + x86_64) — macOS only
  windows      — build Windows installer (.msi + NSIS) — requires Windows or cross-compile
  python       — build Python wheel with uv build
  sidecar      — build PyInstaller sidecar binary
  plugin       — build JUCE plugin with CMake
  check        — check if all build tools are installed

---

Build the target specified in: $ARGUMENTS

**Step 1 — Detect build target:**
Parse $ARGUMENTS to determine what to build.

**Step 2 — Check prerequisites based on target:**

*For Tauri targets (dev/release/universal/windows):*
- Check `pnpm` is installed: `pnpm --version`
- Check `cargo` is installed: `cargo --version`
- Check node_modules exist: `app/node_modules/` directory
- If not: run `cd app && pnpm install` first
- Check `app/src-tauri/binaries/samplemind-server` exists for release builds
- For universal: verify running on macOS (`uname -s` = Darwin)
- For windows: check `x86_64-pc-windows-msvc` target is installed (`rustup target list --installed`)

*For python:*
- Check `uv` is installed
- Check `pyproject.toml` exists

*For sidecar:*
- Check PyInstaller: `uv run pyinstaller --version`
- Check spec file exists: `samplemind-sidecar.spec`
- Note: sidecar must be built on target OS (macOS binary for macOS, Linux for Linux)

*For plugin:*
- Check CMake: `cmake --version`
- Check JUCE submodule: `plugin/JUCE/CMakeLists.txt`
- Check Xcode CLI (macOS): `xcode-select -p`
- Check CMakePresets: `plugin/CMakePresets.json` (use presets if available)

**Step 3 — Run the build:**

```bash
# dev
cd app && pnpm tauri dev

# release (current platform)
cd app && pnpm tauri build

# universal (macOS only)
cd app && pnpm tauri build --target universal-apple-darwin

# windows (cross-compile or on Windows)
cd app && pnpm tauri build --target x86_64-pc-windows-msvc

# python wheel
uv build

# sidecar (run on target OS)
uv run pyinstaller samplemind-sidecar.spec --noconfirm
# Copy to Tauri resources:
cp dist/samplemind-sidecar app/src-tauri/binaries/samplemind-server-$(rustc -vV | grep host | cut -d' ' -f2)

# plugin (using CMakePresets if available)
cd plugin
if [ -f CMakePresets.json ]; then
  cmake --preset macos-release && cmake --build --preset macos-release
else
  cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build
fi

# check
echo "Checking build tools..." && pnpm --version && cargo --version && uv --version && cmake --version
```

**Step 4 — Sidecar checksum (for release builds):**
After building the sidecar, generate and save its SHA-256:
```bash
sha256sum dist/samplemind-sidecar > app/src-tauri/resources/samplemind-sidecar.sha256
echo "Sidecar SHA-256:"
cat app/src-tauri/resources/samplemind-sidecar.sha256
```

**Step 5 — Universal Binary validation (for universal builds):**
After a universal macOS build, verify both architectures are present:
```bash
lipo -info "app/src-tauri/target/universal-apple-darwin/release/bundle/macos/SampleMind.app/Contents/MacOS/SampleMind"
# Expected output: Architectures in the fat file: ... are: x86_64 arm64
```

**Step 6 — Report output:**
Show where the built artifact is located:
- Tauri release (macOS): `app/src-tauri/target/release/bundle/dmg/` or `bundle/macos/`
- Tauri release (Windows): `app/src-tauri/target/release/bundle/msi/` or `bundle/nsis/`
- Tauri release (Linux): `app/src-tauri/target/release/bundle/appimage/` or `bundle/deb/`
- Tauri universal: `app/src-tauri/target/universal-apple-darwin/release/bundle/`
- Python wheel: `dist/*.whl`
- Sidecar: `dist/samplemind-sidecar`
- JUCE plugin: `plugin/build/SampleMind_artefacts/Release/`

Suggest next steps (e.g., install AU plugin to `~/Library/Audio/Plug-Ins/Components/`).
