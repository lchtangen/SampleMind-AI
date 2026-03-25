# Phase 8 — VST3/AU Plugin with JUCE 8

> Build a JUCE 8 C++ plugin (VST3 + AU) that runs inside FL Studio and communicates with the
> Python backend via a local socket.

---

## Prerequisites

- Phases 1–7 complete
- Basic C++ knowledge (classes, pointers, templates)
- JUCE installed from https://juce.com/
- macOS: Xcode 15+
- Windows: Visual Studio 2022 with C++ Desktop Development

---

## Goal State

- JUCE 8 project configured with VST3 + AU targets
- Minimal `AudioProcessor` and `AudioProcessorEditor` with search field
- Python sidecar server responding to socket requests
- `C++ ↔ Unix socket ↔ Python` IPC working

---

## 1. Architecture

```
┌─────────────────────────────────────┐
│   FL Studio (DAW)                   │
│   ┌─────────────────────────────┐   │
│   │  SampleMind AU/VST3 Plugin  │   │
│   │  ┌──────────────────────┐   │   │
│   │  │  PluginEditor (UI)   │   │   │
│   │  │  Search field        │   │   │
│   │  │  Sample list         │   │   │
│   │  │  Waveform preview    │   │   │
│   │  └──────────┬───────────┘   │   │
│   │             │ IPC socket    │   │
│   │  ┌──────────▼───────────┐   │   │
│   │  │  PythonSidecar       │   │   │
│   │  │  (ChildProcess mgr)  │   │   │
│   │  └──────────────────────┘   │   │
│   └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │ Unix domain socket (~/tmp/samplemind.sock)
┌──────────────▼──────────────────────┐
│  Python sidecar process             │
│  src/samplemind/sidecar/server.py   │
│  ← librosa analysis                 │
│  ← SQLModel database                │
└─────────────────────────────────────┘
```

---

## 2. JUCE 8 Learning Path for C++ Beginners

C++ is more complex than Python. Here is the recommended order:

```
Step 1 — C++ fundamentals (2-4 weeks)
  - Classes and inheritance
  - Pointers and references
  - std::unique_ptr and std::shared_ptr (smart pointers)
  - Resource: "A Tour of C++" by Bjarne Stroustrup

Step 2 — JUCE fundamentals (2-4 weeks)
  - Download Projucer (JUCE's project generator)
  - Follow "Getting Started with JUCE" tutorial
  - Build a simple "Hello World" plugin
  - Resource: https://juce.com/learn/tutorials/

Step 3 — SampleMind Plugin (ongoing)
  - Add socket communication
  - Build search UI
  - Implement drag-and-drop to FL Studio
```

---

## 3. JUCE 8 — CMakeLists.txt

```cmake
# filename: plugin/CMakeLists.txt
# JUCE 8 uses CMake as its build system (Projucer is optional)

cmake_minimum_required(VERSION 3.22)
project(SampleMindPlugin VERSION 0.1.0)

# ── Load JUCE ──────────────────────────────────────────────────────────────
# Assumes JUCE is cloned to ./JUCE/
add_subdirectory(JUCE)

# ── Plugin configuration ───────────────────────────────────────────────────
juce_add_plugin(SampleMind
    # Plugin metadata
    COMPANY_NAME "SampleMind"
    PLUGIN_MANUFACTURER_CODE "SmAI"
    PLUGIN_CODE "SmPl"
    FORMATS VST3 AU          # Build both formats

    # Plugin type: instrument plugin (not an effect)
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE

    PRODUCT_NAME "SampleMind"
    BUNDLE_ID "com.samplemind.plugin"

    HARDENED_RUNTIME_ENABLED TRUE
    HARDENED_RUNTIME_OPTIONS
        "com.apple.security.cs.allow-unsigned-executable-memory"
)

# ── Source files ───────────────────────────────────────────────────────────
target_sources(SampleMind PRIVATE
    src/PluginProcessor.cpp
    src/PluginProcessor.h
    src/PluginEditor.cpp
    src/PluginEditor.h
    src/PythonSidecar.cpp
    src/PythonSidecar.h
    src/IPCSocket.cpp
    src/IPCSocket.h
)

# ── JUCE modules we need ───────────────────────────────────────────────────
target_compile_definitions(SampleMind PUBLIC
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
)

target_link_libraries(SampleMind PRIVATE
    juce::juce_audio_utils
    juce::juce_gui_basics
    juce::juce_audio_processors
    juce_recommended_config_flags
    juce_recommended_lto_flags
    juce_recommended_warning_flags
)
```

---

## 4. PluginProcessor — The Audio Processor

```cpp
// filename: plugin/src/PluginProcessor.h

#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "PythonSidecar.h"

/**
 * AudioProcessor is the core of a JUCE plugin.
 * It handles the audio signal and holds state.
 * SampleMind is a pure UI plugin — we don't touch the audio buffer.
 */
class SampleMindProcessor : public juce::AudioProcessor {
public:
    SampleMindProcessor();
    ~SampleMindProcessor() override;

    // ── Audio functions (required by JUCE, unused for us) ────────────────
    void prepareToPlay(double sampleRate, int samplesPerBlock) override {}
    void releaseResources() override {}
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override {}

    // ── Plugin info ────────────────────────────────────────────────────────
    const juce::String getName() const override { return "SampleMind"; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }

    // ── Preset handling (not used yet) ─────────────────────────────────────
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return "Default"; }
    void changeProgramName(int, const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override {}
    void setStateInformation(const void*, int) override {}

    // ── UI creation ────────────────────────────────────────────────────────
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    // ── Sidecar access for UI ──────────────────────────────────────────────
    PythonSidecar& getSidecar() { return *sidecar; }

private:
    std::unique_ptr<PythonSidecar> sidecar;  // Smart pointer — auto-cleans up
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SampleMindProcessor)
};
```

---

## 5. PythonSidecar — C++ Class that Starts Python

```cpp
// filename: plugin/src/PythonSidecar.h

#pragma once
#include <juce_core/juce_core.h>
#include <string>

/**
 * Manages the lifecycle of the Python sidecar process.
 * Starts Python when the plugin loads, stops on unload.
 * Communicates via Unix domain socket.
 */
class PythonSidecar {
public:
    PythonSidecar();
    ~PythonSidecar();

    /** Start Python sidecar (called in PluginProcessor constructor). */
    bool start();

    /** Stop Python sidecar (called in destructor). */
    void stop();

    /** Check if the sidecar process is running. */
    bool isRunning() const;

    /**
     * Send a JSON request to Python and return a JSON response.
     * Blocking — do NOT call from the audio thread!
     */
    std::string sendRequest(const std::string& jsonRequest);

private:
    juce::ChildProcess process;      // JUCE cross-platform process wrapper
    juce::File socketPath;           // Unix socket path
    bool running = false;

    juce::File findPythonExecutable();

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PythonSidecar)
};
```

---

## 6. Python Sidecar Server

```python
# filename: src/samplemind/sidecar/server.py

import json
import socket
import struct
import argparse
from pathlib import Path
from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository


def handle_request(data: dict) -> dict:
    """
    Handle a JSON request from the JUCE plugin.
    Always returns a JSON response.
    """
    action = data.get("action")

    if action == "search":
        # SampleRepository uses static methods — no instance required
        samples = SampleRepository.search(
            query=data.get("query"),
            energy=data.get("energy"),
            instrument=data.get("instrument"),
            bpm_min=data.get("bpm_min"),
            bpm_max=data.get("bpm_max"),
        )
        return {
            "status": "ok",
            "samples": [
                {
                    "id": s.id,
                    "filename": s.filename,
                    "path": s.path,
                    "bpm": s.bpm,
                    "key": s.key,
                    "instrument": s.instrument,
                    "mood": s.mood,
                    "energy": s.energy,
                }
                for s in samples
            ]
        }

    elif action == "analyze":
        path = data.get("path")
        if not path or not Path(path).exists():
            return {"status": "error", "message": f"File not found: {path}"}
        try:
            result = analyze_file(path)
            return {"status": "ok", **result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif action == "ping":
        return {"status": "ok", "message": "SampleMind sidecar running"}

    return {"status": "error", "message": f"Unknown action: {action}"}


def run_socket_server(socket_path: str):
    """
    Run a Unix domain socket server.
    Listens for JSON requests from the JUCE plugin.

    Protocol: length-prefixed JSON
      - 4 byte big-endian int: length of the JSON message
      - N bytes: JSON data (UTF-8)
    """
    sock_file = Path(socket_path)
    if sock_file.exists():
        sock_file.unlink()

    # init_orm() creates all SQLModel tables if they don't exist yet.
    # It is idempotent — safe to call every time the sidecar starts.
    init_orm()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(socket_path)
        server.listen(5)
        print(f"SampleMind sidecar listening on: {socket_path}")

        while True:
            conn, _ = server.accept()
            with conn:
                try:
                    # Read length prefix (4 bytes)
                    length_bytes = conn.recv(4)
                    if not length_bytes:
                        continue
                    length = struct.unpack(">I", length_bytes)[0]

                    # Read JSON data
                    data_bytes = b""
                    while len(data_bytes) < length:
                        chunk = conn.recv(min(4096, length - len(data_bytes)))
                        if not chunk:
                            break
                        data_bytes += chunk

                    request = json.loads(data_bytes.decode("utf-8"))
                    response = handle_request(request)

                    # Send response
                    response_bytes = json.dumps(response).encode("utf-8")
                    conn.sendall(struct.pack(">I", len(response_bytes)))
                    conn.sendall(response_bytes)

                except Exception as e:
                    print(f"Socket error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", default="/tmp/samplemind_plugin.sock")
    args = parser.parse_args()
    run_socket_server(args.socket)
```

---

## 7. macOS AU Validation

All AU plugins on macOS must pass the `auval` tool test:

```bash
# Build and install the plugin
$ cmake --build build/ --config Release
$ cp -r build/SampleMind_artefacts/AU/SampleMind.component \
    ~/Library/Audio/Plug-Ins/Components/

# Validate the plugin (can take 1-2 minutes)
$ auval -v aufx SmPl SmAI

# Expected output:
# * * PASS
# AU Validation Tool vx.x.x
# ...
# AU VALIDATION SUCCEEDED
```

---

## Migration Notes

- Plugin code lives in `plugin/` — a separate CMake project
- Python sidecar server lives in `src/samplemind/sidecar/`
- Plugin is built separately from the Tauri app

---

## Testing Checklist

```bash
# Start Python sidecar
$ uv run python src/samplemind/sidecar/server.py --socket /tmp/test.sock &

# Test socket communication
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

# Build JUCE plugin
$ cd plugin/ && cmake -B build && cmake --build build
```

---

## Troubleshooting

**Compile error: JUCE modules not found**
```cmake
# Confirm the JUCE folder exists next to CMakeLists.txt:
$ ls plugin/JUCE/CMakeLists.txt
# If not: git clone https://github.com/juce-framework/JUCE plugin/JUCE
```

**AU plugin rejected by macOS Gatekeeper**
```bash
# Sign the plugin with Developer ID (requires Apple Developer account):
$ codesign -s "Developer ID Application: Your Name" --deep \
    ~/Library/Audio/Plug-Ins/Components/SampleMind.component
```

**Python sidecar not starting**
```
Check that Python 3.13 is installed and available at the path
findPythonExecutable() returns. Add debug logging in C++:
DBG("Python path: " + pythonExe.getFullPathName());
```

---

## 8. JUCE Plugin Advanced (2026)

### CMakePresets.json

Add `CMakePresets.json` to `plugin/` for reproducible builds across platforms:

```json
{
  "version": 3,
  "cmakeMinimumRequired": {"major": 3, "minor": 22, "patch": 0},
  "configurePresets": [
    {
      "name": "macos-release",
      "displayName": "macOS Release (Xcode)",
      "generator": "Xcode",
      "binaryDir": "${sourceDir}/build-macos-release",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Release",
        "JUCE_BUILD_EXTRAS": "OFF",
        "JUCE_BUILD_EXAMPLES": "OFF"
      }
    },
    {
      "name": "macos-debug",
      "displayName": "macOS Debug (Xcode)",
      "generator": "Xcode",
      "binaryDir": "${sourceDir}/build-macos-debug",
      "cacheVariables": {"CMAKE_BUILD_TYPE": "Debug"}
    },
    {
      "name": "linux-debug",
      "displayName": "Linux Debug (Ninja)",
      "generator": "Ninja",
      "binaryDir": "${sourceDir}/build-linux",
      "cacheVariables": {"CMAKE_BUILD_TYPE": "Debug"}
    }
  ],
  "buildPresets": [
    {"name": "macos-release", "configurePreset": "macos-release", "configuration": "Release"},
    {"name": "macos-debug",   "configurePreset": "macos-debug",   "configuration": "Debug"},
    {"name": "linux-debug",   "configurePreset": "linux-debug"}
  ]
}
```

Build with presets:
```bash
cd plugin
cmake --preset macos-release
cmake --build --preset macos-release
```

### Custom LookAndFeel (Dark Theme)

```cpp
// plugin/src/SampleMindLookAndFeel.h
#pragma once
#include <juce_gui_basics/juce_gui_basics.h>

class SampleMindLookAndFeel : public juce::LookAndFeel_V4 {
public:
    SampleMindLookAndFeel() {
        // Background colors
        setColour(juce::ResizableWindow::backgroundColourId,  juce::Colour(0xFF1A1A2E));
        setColour(juce::DocumentWindow::backgroundColourId,   juce::Colour(0xFF1A1A2E));

        // Button colors
        setColour(juce::TextButton::buttonColourId,           juce::Colour(0xFF16213E));
        setColour(juce::TextButton::buttonOnColourId,         juce::Colour(0xFFE94560));
        setColour(juce::TextButton::textColourOnId,           juce::Colours::white);
        setColour(juce::TextButton::textColourOffId,          juce::Colour(0xFFCBD5E0));

        // TextEditor colors
        setColour(juce::TextEditor::backgroundColourId,       juce::Colour(0xFF0F3460));
        setColour(juce::TextEditor::textColourId,             juce::Colours::white);
        setColour(juce::TextEditor::highlightColourId,        juce::Colour(0xFFE94560));
        setColour(juce::TextEditor::outlineColourId,          juce::Colour(0xFF2D3748));

        // ListBox colors
        setColour(juce::ListBox::backgroundColourId,          juce::Colour(0xFF16213E));
        setColour(juce::ListBox::textColourId,                juce::Colour(0xFFE2E8F0));
    }

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SampleMindLookAndFeel)
};
```

Apply in `PluginEditor`:
```cpp
// PluginEditor.cpp constructor
SampleMindAudioProcessorEditor::SampleMindAudioProcessorEditor(SampleMindAudioProcessor& p)
    : AudioProcessorEditor(&p), processorRef(p)
{
    lookAndFeel = std::make_unique<SampleMindLookAndFeel>();
    setLookAndFeel(lookAndFeel.get());
    setSize(600, 400);
}

SampleMindAudioProcessorEditor::~SampleMindAudioProcessorEditor() {
    setLookAndFeel(nullptr);  // Must reset before destruction
}
```

### Sidecar Lifecycle Management

```cpp
// plugin/src/PluginProcessor.cpp

void SampleMindAudioProcessor::prepareToPlay(double /*sampleRate*/, int /*blockSize*/) {
    if (!pythonSidecar.isRunning()) {
        juce::File sidecarPath = getSidecarPath();
        if (!sidecarPath.exists()) {
            DBG("SampleMind: sidecar binary not found at " + sidecarPath.getFullPathName());
            return;
        }
        if (!pythonSidecar.launch(sidecarPath)) {
            DBG("SampleMind: failed to launch sidecar");
            return;
        }
        // Wait for "ready" signal (up to 5 seconds)
        juce::String readyLine;
        for (int i = 0; i < 50 && !readyLine.contains("ready"); ++i) {
            juce::Thread::sleep(100);
            readyLine = pythonSidecar.readProcessOutput(1024);
        }
        DBG("SampleMind: sidecar ready");
        startTimer(5000);  // Start health check timer
    }
}

void SampleMindAudioProcessor::releaseResources() {
    stopTimer();
    pythonSidecar.shutdown();
}

void SampleMindAudioProcessor::timerCallback() {
    // Health check: send ping every 5 seconds
    if (!pythonSidecar.ping()) {
        DBG("SampleMind: sidecar health check failed — restarting");
        pythonSidecar.shutdown();
        prepareToPlay(getSampleRate(), getBlockSize());
    }
}
```

### AU Validation Script

```bash
#!/bin/bash
# scripts/validate-au.sh
set -euo pipefail

PLUGIN_NAME="SampleMind"
MANUFACTURER_CODE="SmAI"
PLUGIN_TYPE_CODE="SmPl"

echo "Installing AU plugin for validation..."
cp -R "plugin/build-macos-release/SampleMind_artefacts/Release/AU/${PLUGIN_NAME}.component" \
    ~/Library/Audio/Plug-Ins/Components/

echo "Clearing AU cache..."
killall -9 AudioComponentRegistrar 2>/dev/null || true

echo "Running auval..."
auval -v aufx "${PLUGIN_TYPE_CODE}" "${MANUFACTURER_CODE}"

echo "AU validation passed for ${PLUGIN_NAME}."
```

Run before every release:
```bash
chmod +x scripts/validate-au.sh
./scripts/validate-au.sh
```

### JUCE Plugin Code Signing

Sign after building (replace `<TEAM>` and `<NAME>` with your Apple Developer credentials):

```bash
# Sign the AU component:
codesign --deep --force --options runtime \
  --sign "Developer ID Application: <NAME> (<TEAM>)" \
  ~/Library/Audio/Plug-Ins/Components/SampleMind.component

# Sign the VST3:
codesign --deep --force --options runtime \
  --sign "Developer ID Application: <NAME> (<TEAM>)" \
  ~/Library/Audio/Plug-Ins/VST3/SampleMind.vst3

# Verify signing:
codesign --verify --verbose ~/Library/Audio/Plug-Ins/Components/SampleMind.component
spctl --assess --type execute ~/Library/Audio/Plug-Ins/Components/SampleMind.component

---

## 8. Plugin State Save/Restore

DAWs save plugin parameters with the project file. SampleMind stores
the current search query, selected filters, and last-played sample.

```cpp
// plugin/Source/PluginProcessor.cpp

/**
 * getStateInformation — called by the DAW when saving the project.
 *
 * We serialize a simple JSON blob using JUCE's MemoryOutputStream.
 * JUCE's XmlElement is simpler but JSON matches our sidecar protocol.
 *
 * State schema:
 *   {
 *     "version": 1,
 *     "query": "trap kick",
 *     "filters": {"instrument": "kick", "energy": "high"},
 *     "last_sample_id": 42,
 *     "volume": 0.8
 *   }
 */
void SampleMindAudioProcessor::getStateInformation(juce::MemoryBlock& destData)
{
    juce::DynamicObject::Ptr state = new juce::DynamicObject();
    state->setProperty("version",        1);
    state->setProperty("query",          currentQuery);
    state->setProperty("last_sample_id", lastSampleId);
    state->setProperty("volume",         masterVolume);

    // Build filters object
    auto* filters = new juce::DynamicObject();
    filters->setProperty("instrument", filterInstrument);
    filters->setProperty("energy",     filterEnergy);
    state->setProperty("filters", juce::var(filters));

    juce::MemoryOutputStream stream(destData, false);
    juce::JSON::writeToStream(stream, juce::var(state.get()));
}

/**
 * setStateInformation — called by the DAW when loading a saved project.
 *
 * Must be robust: if the state is malformed or from an old version,
 * fall back to sensible defaults rather than crash.
 */
void SampleMindAudioProcessor::setStateInformation(const void* data, int sizeInBytes)
{
    juce::String jsonStr(static_cast<const char*>(data), (size_t)sizeInBytes);
    juce::var parsed = juce::JSON::parse(jsonStr);

    if (!parsed.isObject()) {
        DBG("SampleMind: invalid state JSON — using defaults");
        return;
    }

    int version = parsed["version"];
    if (version > 1) {
        DBG("SampleMind: state version " << version << " > 1 — may be missing fields");
    }

    currentQuery    = parsed["query"].toString();
    lastSampleId    = (int) parsed["last_sample_id"];
    masterVolume    = (float) parsed["volume"];

    if (auto* filters = parsed["filters"].getDynamicObject()) {
        filterInstrument = filters->getProperty("instrument").toString();
        filterEnergy     = filters->getProperty("energy").toString();
    }

    // Notify editor to refresh UI with restored state
    if (auto* editor = dynamic_cast<SampleMindAudioProcessorEditor*>(getActiveEditor()))
        editor->refreshFromState();
}
```

---

## 9. Preset Management

Allow users to save and recall plugin presets (saved search configurations).

```cpp
// plugin/Source/PresetManager.h
/**
 * PresetManager — save/load named plugin configurations.
 *
 * Presets are stored as JSON files in:
 *   macOS: ~/Library/Application Support/SampleMind/Presets/
 *   Win:   %APPDATA%\SampleMind\Presets\
 *
 * Each preset file:
 *   {
 *     "name": "Trap Production Kit",
 *     "version": 1,
 *     "query": "trap",
 *     "filters": { "instrument": "kick", "energy": "high" },
 *     "tags": ["trap", "production", "808"]
 *   }
 */
class PresetManager
{
public:
    explicit PresetManager(SampleMindAudioProcessor& processor);

    // Returns list of preset names available on disk
    juce::StringArray getPresetNames() const;

    // Save current processor state as a named preset
    void savePreset(const juce::String& name);

    // Load a named preset and apply to processor
    bool loadPreset(const juce::String& name);

    // Delete a preset file
    bool deletePreset(const juce::String& name);

private:
    SampleMindAudioProcessor& mProcessor;
    juce::File getPresetsDir() const;
    juce::File getPresetFile(const juce::String& name) const;
};
```

```cpp
// plugin/Source/PresetManager.cpp
juce::File PresetManager::getPresetsDir() const
{
    return juce::File::getSpecialLocation(juce::File::userApplicationDataDirectory)
        .getChildFile("SampleMind").getChildFile("Presets");
}

void PresetManager::savePreset(const juce::String& name)
{
    juce::MemoryBlock stateData;
    mProcessor.getStateInformation(stateData);

    auto presetFile = getPresetFile(name);
    getPresetsDir().createDirectory();
    presetFile.replaceWithData(stateData.getData(), stateData.getSize());
    DBG("Preset saved: " << presetFile.getFullPathName());
}

bool PresetManager::loadPreset(const juce::String& name)
{
    auto presetFile = getPresetFile(name);
    if (!presetFile.existsAsFile()) return false;

    juce::MemoryBlock data;
    if (!presetFile.loadFileAsData(data)) return false;

    mProcessor.setStateInformation(data.getData(), (int) data.getSize());
    return true;
}
```

---

## 10. Plugin MIDI Output — Send Sample BPM to DAW

When a sample is selected in the plugin, send MIDI notes/CC to the DAW
so the tempo track can be updated automatically.

```cpp
// plugin/Source/PluginProcessor.cpp

/**
 * processBlock — runs on the audio thread. MUST NOT block.
 *
 * MIDI output strategy:
 *   CC #14 = BPM integer part (0-127 → 60-187 BPM range)
 *   CC #15 = BPM fractional part × 100 (e.g. 140.5 → CC14=80, CC15=50)
 *   CC #16 = energy (0=low, 64=mid, 127=high)
 *   Note-on C3 (36) = "sample loaded" signal for DAW automation
 *
 * All MIDI is added to midiMessages output buffer — DAW routes it freely.
 */
void SampleMindAudioProcessor::processBlock(
    juce::AudioBuffer<float>& buffer,
    juce::MidiBuffer& midiMessages)
{
    buffer.clear();  // SampleMind is FX plugin — passes audio through

    if (pendingSampleLoad.exchange(false)) {
        // Send BPM CC pair at sample position 0
        int bpm_int  = juce::jlimit(60, 187, (int)currentBpm);
        int bpm_frac = juce::jlimit(0, 99, (int)((currentBpm - bpm_int) * 100));
        int energy_cc = (filterEnergy == "high") ? 127 : (filterEnergy == "mid") ? 64 : 0;

        midiMessages.addEvent(juce::MidiMessage::controllerEvent(1, 14, bpm_int - 60), 0);
        midiMessages.addEvent(juce::MidiMessage::controllerEvent(1, 15, bpm_frac), 1);
        midiMessages.addEvent(juce::MidiMessage::controllerEvent(1, 16, energy_cc), 2);
        // Note-on to signal "sample loaded" — velocity = sample ID mod 127
        midiMessages.addEvent(juce::MidiMessage::noteOn(1, 36, (uint8)(lastSampleId % 127 + 1)), 3);
        midiMessages.addEvent(juce::MidiMessage::noteOff(1, 36, (uint8)0), 24);
    }
}
```
```

