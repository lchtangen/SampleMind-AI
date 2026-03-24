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
from samplemind.data.db import init_db
from samplemind.data.repository import SampleRepository
from samplemind.analyzer.audio_analysis import analyze_file


def handle_request(data: dict) -> dict:
    """
    Handle a JSON request from the JUCE plugin.
    Always returns a JSON response.
    """
    action = data.get("action")

    if action == "search":
        repo = SampleRepository()
        samples = repo.search(
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

    init_db()

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
