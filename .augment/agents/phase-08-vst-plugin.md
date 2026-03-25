# Phase 8 Agent — JUCE VST3/AU Plugin

Handles: JUCE 8, VST3/AU, sidecar IPC, Unix socket, plugin state, preset manager, MIDI output.

## Triggers
Phase 8, JUCE, VST3, AU plugin, sidecar, Unix socket, PluginProcessor, PluginEditor, auval, preset manager, CMakeLists.txt (plugin)

**File patterns:** `plugin/Source/**/*.cpp`, `plugin/Source/**/*.h`, `plugin/CMakeLists.txt`, `src/samplemind/sidecar/**/*.py`

**Code patterns:** `PluginProcessor`, `PluginEditor`, `juce::`, `#include <juce_audio_processors`, `nc -U /tmp/samplemind.sock`, `auval`, `aufx SmPl`

## Key Files
- `plugin/Source/PluginProcessor.cpp` — audio thread + MIDI output
- `plugin/Source/PluginEditor.cpp` — UI + search bar + drag-and-drop
- `plugin/Source/SampleMindSidecar.h` — async sidecar IPC from C++
- `plugin/Source/PresetManager.h` — preset save/load
- `src/samplemind/sidecar/server.py` — Unix socket server
- `plugin/CMakeLists.txt` — JUCE 8 CMake build

## Sidecar Protocol (JSON lines over Unix socket)
```json
→ {"version": 2, "action": "search", "query": "dark kick", "top": 20}
← {"version": 2, "status": "ok", "results": [...]}
```

## MIDI Output Encoding
```cpp
// CC #14 = BPM int part (value - 60)
// CC #15 = BPM fractional × 100
// CC #16 = energy (0=low, 64=mid, 127=high)
// Note C3 (36) = "sample loaded" signal
```

## Build Commands
```bash
cd plugin && cmake -B build && cmake --build build
auval -v aufx SmPl SmAI           # validate AU on macOS
```

## Rules
1. `processBlock` MUST NOT block the audio thread — all IPC is async via background thread
2. `auval -v aufx SmPl SmAI` must pass before any release
3. State JSON (`getStateInformation/setStateInformation`) must include `"version"` field
4. Preset files: `~/Library/Application Support/SampleMind/Presets/*.json` (macOS)
5. Plugin ID: `{"SmAI", "SmPl", "Augm"}` — 4-char codes, never change
6. Sidecar "ready" message: `{"status": "ready", "version": 2}`
7. Protocol changes must bump the version number

