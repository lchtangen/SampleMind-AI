# Fase 8 — VST3/AU Plugin med JUCE 8

> Bygg et JUCE 8 C++-plugin (VST3 + AU) som kjører inne i FL Studio og snakker med Python-backend
> via en lokal socket.

---

## Forutsetninger

- Fase 1–7 fullført
- C++ grunnleggende kunnskap (klasser, pekere, templates)
- JUCE installert fra https://juce.com/
- macOS: Xcode 15+
- Windows: Visual Studio 2022 med C++ Desktop Development

---

## Mål etter denne fasen

- JUCE 8-prosjekt konfigurert med VST3 + AU targets
- Minimal `AudioProcessor` og `AudioProcessorEditor` med søkefelt
- Python sidecar-server som svarer på socket-forespørsler
- `C++ ↔ Unix socket ↔ Python` IPC fungerer

---

## 1. Arkitektur

```
┌─────────────────────────────────────┐
│   FL Studio (DAW)                   │
│   ┌─────────────────────────────┐   │
│   │  SampleMind AU/VST3 Plugin  │   │
│   │  ┌──────────────────────┐   │   │
│   │  │  PluginEditor (UI)   │   │   │
│   │  │  Søkefelt            │   │   │
│   │  │  Sample-liste        │   │   │
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
│  Python sidecar-prosess             │
│  src/samplemind/sidecar/server.py   │
│  ← librosa analyse                  │
│  ← SQLModel database                │
└─────────────────────────────────────┘
```

---

## 2. JUCE 8-læringsveien for nybegynnere i C++

C++ er mer komplekst enn Python. Her er en anbefalt rekkefølge:

```
Steg 1 — C++ grunnleggende (2-4 uker)
  - Klasser og arv
  - Pekere og referanser
  - std::unique_ptr og std::shared_ptr (smart pointers)
  - Ressurs: "A Tour of C++" av Bjarne Stroustrup

Steg 2 — JUCE grunnleggende (2-4 uker)
  - Last ned Projucer (JUCE's prosjektgenerator)
  - Følg "Getting Started with JUCE" tutorial
  - Bygg et enkelt "Hello World" plugin
  - Ressurs: https://juce.com/learn/tutorials/

Steg 3 — SampleMind Plugin (pågående)
  - Legg til socket-kommunikasjon
  - Bygg søke-UI
  - Implementer drag-and-drop til FL Studio
```

---

## 3. JUCE 8 — CMakeLists.txt

```cmake
# filename: plugin/CMakeLists.txt
# JUCE 8 bruker CMake som build-system (Projucer er valgfritt)

cmake_minimum_required(VERSION 3.22)
project(SampleMindPlugin VERSION 0.1.0)

# ── Last inn JUCE ──────────────────────────────────────────────────────────
# Forutsetter at JUCE er klonet til ./JUCE/
add_subdirectory(JUCE)

# ── Plugin-konfigurasjon ───────────────────────────────────────────────────
juce_add_plugin(SampleMind
    # Plugin-metadata
    COMPANY_NAME "SampleMind"
    PLUGIN_MANUFACTURER_CODE "SmAI"
    PLUGIN_CODE "SmPl"
    FORMATS VST3 AU          # Bygg begge formater

    # Plugin-type: instrument-plugin (ikke effekt)
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE

    # Plugin-navn og beskrivelse
    PRODUCT_NAME "SampleMind"
    BUNDLE_ID "com.samplemind.plugin"

    # macOS minimumversjon
    HARDENED_RUNTIME_ENABLED TRUE
    HARDENED_RUNTIME_OPTIONS
        "com.apple.security.cs.allow-unsigned-executable-memory"
)

# ── Kildefiler ─────────────────────────────────────────────────────────────
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

# ── JUCE-moduler vi trenger ────────────────────────────────────────────────
target_compile_definitions(SampleMind PUBLIC
    JUCE_WEB_BROWSER=0          # Ingen innebygd nettleser
    JUCE_USE_CURL=0             # Ingen HTTP-klient
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

## 4. PluginProcessor — Audio-prosessoren

```cpp
// filename: plugin/src/PluginProcessor.h

#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "PythonSidecar.h"

/**
 * AudioProcessor er kjernen av et JUCE-plugin.
 * Den håndterer lydsignalet og holder oversikt over tilstand.
 * SampleMind er en ren UI-plugin — vi berører ikke audio-bufferet.
 */
class SampleMindProcessor : public juce::AudioProcessor {
public:
    SampleMindProcessor();
    ~SampleMindProcessor() override;

    // ── Lydfunksjoner (påkrevd av JUCE, men ubrukt for oss) ──────────────
    void prepareToPlay(double sampleRate, int samplesPerBlock) override {}
    void releaseResources() override {}
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override {}

    // ── Plugin-info ────────────────────────────────────────────────────────
    const juce::String getName() const override { return "SampleMind"; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }

    // ── Preset-håndtering (ikke brukt ennå) ────────────────────────────────
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return "Default"; }
    void changeProgramName(int, const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override {}
    void setStateInformation(const void*, int) override {}

    // ── UI-opprettelse ─────────────────────────────────────────────────────
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }

    // ── Sidecar-tilgang for UI ─────────────────────────────────────────────
    PythonSidecar& getSidecar() { return *sidecar; }

private:
    std::unique_ptr<PythonSidecar> sidecar;  // Smart pointer — auto-rydder opp
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SampleMindProcessor)
};
```

---

## 5. PythonSidecar — C++ klasse som starter Python

```cpp
// filename: plugin/src/PythonSidecar.h

#pragma once
#include <juce_core/juce_core.h>
#include <string>
#include <functional>

/**
 * Håndterer livssyklusen til Python sidecar-prosessen.
 * Starter Python ved plugin-innlasting, stopper ved utlasting.
 * Kommuniserer via Unix domain socket.
 */
class PythonSidecar {
public:
    PythonSidecar();
    ~PythonSidecar();

    /** Start Python sidecar (kalles i PluginProcessor constructor). */
    bool start();

    /** Stopp Python sidecar (kalles i destructor). */
    void stop();

    /** Sjekk om sideckar-prosessen kjører. */
    bool isRunning() const;

    /**
     * Send en JSON-forespørsel til Python og returner JSON-svar.
     * Blokkerende — kall ikke fra audio-tråden!
     */
    std::string sendRequest(const std::string& jsonRequest);

private:
    juce::ChildProcess process;      // JUCE cross-platform prosess-wrapper
    juce::File socketPath;           // Unix socket sti
    bool running = false;

    // Finn Python-kjørbar fil (bundlet i plugin eller system)
    juce::File findPythonExecutable();

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PythonSidecar)
};
```

```cpp
// filename: plugin/src/PythonSidecar.cpp

#include "PythonSidecar.h"

PythonSidecar::PythonSidecar() {
    socketPath = juce::File::getSpecialLocation(
        juce::File::tempDirectory).getChildFile("samplemind_plugin.sock");
}

PythonSidecar::~PythonSidecar() {
    stop();
}

bool PythonSidecar::start() {
    juce::File pythonExe = findPythonExecutable();
    if (!pythonExe.exists()) {
        DBG("Finner ikke Python: " + pythonExe.getFullPathName());
        return false;
    }

    // Finn sidecar-serveren relativt til plugin-bundlet
    juce::File serverScript = juce::File::getSpecialLocation(
        juce::File::currentApplicationFile)
        .getSiblingFile("samplemind_sidecar/server.py");

    // Start Python som bakgrunnsprosess
    juce::StringArray args;
    args.add(pythonExe.getFullPathName());
    args.add(serverScript.getFullPathName());
    args.add("--socket");
    args.add(socketPath.getFullPathName());

    running = process.start(args);
    if (running) {
        juce::Thread::sleep(500);  // Vent på at Python starter
    }
    return running;
}

void PythonSidecar::stop() {
    if (running) {
        process.kill();
        running = false;
        socketPath.deleteFile();
    }
}

std::string PythonSidecar::sendRequest(const std::string& jsonRequest) {
    // Koble til Unix socket
    // (Forenklet — en produksjonsversjon bruker non-blocking I/O)
    // TODO: Implementer med juce::Socket eller Boost.Asio
    return "{}";  // Placeholder
}

juce::File PythonSidecar::findPythonExecutable() {
#if JUCE_MAC
    return juce::File("/usr/bin/python3");
#elif JUCE_WINDOWS
    return juce::File("C:\\Python313\\python.exe");
#else
    return juce::File("/usr/bin/python3");
#endif
}
```

---

## 6. Python Sidecar Server

```python
# filename: src/samplemind/sidecar/server.py

import json
import socket
import os
import argparse
from pathlib import Path
from samplemind.data.db import init_db
from samplemind.data.repository import SampleRepository
from samplemind.analyzer.audio_analysis import analyze_file


def handle_request(data: dict) -> dict:
    """
    Håndter en JSON-forespørsel fra JUCE-pluginet.
    Returner alltid et JSON-svar.
    """
    action = data.get("action")

    if action == "search":
        # Søk i biblioteket
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
        # Analyser en enkelt fil
        path = data.get("path")
        if not path or not Path(path).exists():
            return {"status": "error", "message": f"Fil ikke funnet: {path}"}
        try:
            result = analyze_file(path)
            return {"status": "ok", **result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif action == "ping":
        return {"status": "ok", "message": "SampleMind sidecar kjører"}

    return {"status": "error", "message": f"Ukjent action: {action}"}


def run_socket_server(socket_path: str):
    """
    Kjør en Unix domain socket-server.
    Lytter etter JSON-forespørsler fra JUCE-pluginet.

    Protokoll: length-prefixed JSON
      - 4 byte big-endian int: lengden på JSON-meldingen
      - N byte: JSON-data (UTF-8)
    """
    import struct

    # Slett gammel socket-fil hvis den eksisterer
    sock_file = Path(socket_path)
    if sock_file.exists():
        sock_file.unlink()

    init_db()

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(socket_path)
        server.listen(5)
        print(f"SampleMind sidecar lytter på: {socket_path}")

        while True:
            conn, _ = server.accept()
            with conn:
                try:
                    # Les lengde-prefiks (4 bytes)
                    length_bytes = conn.recv(4)
                    if not length_bytes:
                        continue
                    length = struct.unpack(">I", length_bytes)[0]

                    # Les JSON-data
                    data_bytes = b""
                    while len(data_bytes) < length:
                        chunk = conn.recv(min(4096, length - len(data_bytes)))
                        if not chunk:
                            break
                        data_bytes += chunk

                    request = json.loads(data_bytes.decode("utf-8"))
                    response = handle_request(request)

                    # Send svar
                    response_bytes = json.dumps(response).encode("utf-8")
                    conn.sendall(struct.pack(">I", len(response_bytes)))
                    conn.sendall(response_bytes)

                except Exception as e:
                    print(f"Socket feil: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", default="/tmp/samplemind_plugin.sock")
    args = parser.parse_args()
    run_socket_server(args.socket)
```

---

## 7. PluginEditor — UI-klassen

```cpp
// filename: plugin/src/PluginEditor.h

#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "PluginProcessor.h"

/**
 * PluginEditor er UI-komponenten som vises inne i FL Studio.
 * Inneholder søkefelt, sample-liste og preview-seksjon.
 */
class SampleMindEditor : public juce::AudioProcessorEditor,
                          public juce::TextEditor::Listener {
public:
    explicit SampleMindEditor(SampleMindProcessor&);
    ~SampleMindEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;

    // Kalles når brukeren skriver i søkefeltet
    void textEditorTextChanged(juce::TextEditor&) override;

private:
    SampleMindProcessor& processor;

    juce::TextEditor searchBox;          // Søkefelt øverst
    juce::ListBox sampleList;            // Resultat-liste
    juce::Label statusLabel;             // Status/feilmelding

    // Send søkeforespørsel til Python sidecar
    void performSearch(const juce::String& query);

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SampleMindEditor)
};
```

---

## 8. macOS AU-validering

Alle AU-plugins på macOS må bestå `auval`-verktøyets test:

```bash
# Bygg og installer pluginet
$ cmake --build build/ --config Release
$ cp -r build/SampleMind_artefacts/AU/SampleMind.component \
    ~/Library/Audio/Plug-Ins/Components/

# Valider pluginet (kan ta 1-2 minutter)
$ auval -v aufx SmPl SmAI

# Forventet output:
# * * PASS
# AU Validation Tool vx.x.x
# ...
# AU VALIDATION SUCCEEDED
```

---

## Migrasjonsnotater

- Plugin-koden lever i `plugin/` — eget CMake-prosjekt
- Python sidecar-serveren lever i `src/samplemind/sidecar/`
- Plugin bygges separat fra Tauri-appen

---

## Testsjekkliste

```bash
# Bygg Python sidecar
$ uv run python src/samplemind/sidecar/server.py --socket /tmp/test.sock &

# Test socket-kommunikasjon
$ python -c "
import socket, json, struct
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
    s.connect('/tmp/test.sock')
    req = json.dumps({'action': 'ping'}).encode()
    s.sendall(struct.pack('>I', len(req)) + req)
    length = struct.unpack('>I', s.recv(4))[0]
    print(json.loads(s.recv(length)))
"
# Forventet: {'status': 'ok', 'message': 'SampleMind sidecar kjører'}

# Bygg JUCE-pluginet
$ cd plugin/ && cmake -B build && cmake --build build
```

---

## Feilsøking

**Kompileringsfeil: JUCE-moduler ikke funnet**
```cmake
# Bekreft at JUCE-mappen eksisterer ved siden av CMakeLists.txt:
$ ls plugin/JUCE/CMakeLists.txt
# Hvis ikke: git clone https://github.com/juce-framework/JUCE plugin/JUCE
```

**AU-plugin godkjennes ikke av macOS Gatekeeper**
```bash
# Signer pluginet med Developer ID (krever Apple Developer-konto):
$ codesign -s "Developer ID Application: Ditt Navn" --deep \
    ~/Library/Audio/Plug-Ins/Components/SampleMind.component
```

**Python sidecar starter ikke**
```
Sjekk at Python 3.13 er installert og tilgjengelig på stien
findPythonExecutable() returnerer. Legg til logging i C++ for feilsøking:
DBG("Python sti: " + pythonExe.getFullPathName());
```
