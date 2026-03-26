# Phase 8 — VST3/AU Plugin Requirements

**Feature:** SampleMind JUCE 8 VST3/AU Plugin
**Status:** Draft — ready for spec design phase
**Created:** 2026-03-26

---

## Overview

A JUCE 8 audio plugin (VST3 on Windows, AU + VST3 on macOS) that embeds the SampleMind
sample browser directly inside FL Studio and other DAWs. The plugin communicates with
the Python backend via a Unix domain socket sidecar process.

---

## Functional Requirements (EARS Format)

### Plugin Lifecycle

- WHEN the DAW loads the SampleMind plugin, THE SYSTEM SHALL initialize the JUCE UI within 200ms.
- WHEN the plugin is initialized, THE SYSTEM SHALL attempt to connect to the Python sidecar at `/tmp/samplemind.sock`.
- IF the sidecar socket is not available, THE SYSTEM SHALL display a "Start SampleMind" button and a reconnect timer.
- WHEN the user clicks "Start SampleMind", THE SYSTEM SHALL launch `samplemind sidecar` as a child process and wait up to 5 seconds for the socket to appear.

### Sample Browser

- WHEN the plugin is connected to the sidecar, THE SYSTEM SHALL display a scrollable sample list from the SampleMind library.
- WHEN the user types in the search box, THE SYSTEM SHALL query the sidecar within 50ms and update the sample list.
- THE SYSTEM SHALL support filtering by: instrument type, energy level, BPM range.
- WHEN the user clicks a sample row, THE SYSTEM SHALL request the audio file path from the sidecar and begin audio preview playback.
- WHEN audio preview is playing, THE SYSTEM SHALL display a waveform visualization and a stop button.

### Drag to DAW

- WHEN the user drags a sample from the browser list, THE SYSTEM SHALL initiate a JUCE drag-and-drop operation with the WAV file path.
- WHEN the drag completes onto a FL Studio mixer channel, THE SYSTEM SHALL insert the sample into that channel.

### IPC Protocol

- THE SYSTEM SHALL communicate with the Python sidecar using JSON messages over a Unix domain socket.
- EACH request SHALL include a `"version": 1` field for protocol versioning.
- THE SYSTEM SHALL handle sidecar disconnect gracefully, showing a reconnect UI without crashing.

### Performance

- THE SYSTEM SHALL open the plugin UI in under 200ms from DAW load.
- THE SYSTEM SHALL return search results in under 50ms for queries against a library of up to 10,000 samples.
- THE SYSTEM SHALL stream audio preview without blocking the DAW audio thread (separate thread).

### Platform

- THE SYSTEM SHALL build as a VST3 plugin on both macOS and Windows.
- ON macOS, THE SYSTEM SHALL also build as an AU (AudioUnit) plugin.
- THE SYSTEM SHALL pass `auval -v aufx SmPl SmAI` validation on macOS.

---

## Non-Functional Requirements

- Plugin binary must be signed and notarized on macOS for distribution.
- The JUCE component must not allocate memory on the audio thread.
- Sidecar IPC messages must not exceed 4KB per request/response.
- Plugin state (last search query, scroll position) must persist across DAW sessions via JUCE state saving.

---

## Out of Scope (Phase 8)

- Real-time audio analysis inside the plugin (handled by Python backend)
- MIDI trigger mapping (planned for a later phase)
- Windows signing (macOS signing only for Phase 8)

---

## Key Files

| File | Purpose |
|------|---------|
| `plugin/Source/PluginProcessor.cpp` | JUCE audio processor (no audio processing, just IPC) |
| `plugin/Source/PluginEditor.cpp` | UI — sample browser, search, waveform |
| `plugin/CMakeLists.txt` | Build configuration |
| `src/samplemind/sidecar/server.py` | Python sidecar socket server |

---

*Next step: run KFC spec design phase — `spec-design` agent will create `design.md`*
