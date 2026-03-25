# Phase 8 Agent — JUCE VST3/AU Plugin

Handles: JUCE 8, VST3/AU, sidecar IPC, Unix socket, plugin state, preset manager, MIDI output.

## Triggers
- Phase 8, JUCE, VST3, AU plugin, sidecar, Unix socket, PluginProcessor, PluginEditor, auval, preset manager

## Key Files
- `plugin/Source/PluginProcessor.cpp`
- `plugin/Source/PluginEditor.cpp`
- `plugin/Source/SampleMindSidecar.h`
- `plugin/Source/PresetManager.h`
- `src/samplemind/sidecar/server.py`

## Sidecar Protocol (JSON lines over Unix socket)

```json
→ {"version": 2, "action": "search", "query": "dark kick", "top": 20}
← {"version": 2, "status": "ok", "results": [...]}
```

## MIDI Output Encoding (processBlock)

```cpp
// CC #14 = BPM int part (value - 60)
// CC #15 = BPM fractional × 100
// CC #16 = energy (0=low, 64=mid, 127=high)
// Note C3 (36) = "sample loaded" signal
```

## Rules
1. `processBlock` MUST NOT block the audio thread — all IPC is async
2. State JSON: `getStateInformation` / `setStateInformation` — version field required
3. `auval -v aufx SmPl SmAI` must pass before release
4. Preset files: `~/Library/Application Support/SampleMind/Presets/*.json` (macOS)
5. Plugin ID: `{"SmAI", "SmPl", "Augm"}` (4-char codes)
6. Sidecar "ready" message: `{"status": "ready", "version": 2}`

