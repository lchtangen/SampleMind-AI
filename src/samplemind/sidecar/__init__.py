"""Unix domain socket server for JUCE plugin IPC.

Phase 8 — VST3/AU Plugin.
Runs as a background process that the JUCE plugin's PythonSidecar class
connects to over a Unix domain socket. Exposes the SampleRepository and
Audio Analyzer to the plugin via a length-prefixed JSON protocol (version 2).

Socket path: ~/tmp/samplemind.sock
Protocol:    4-byte big-endian length prefix + UTF-8 JSON body
Version:     {"version": 2, "action": "..."}

See: docs/en/phase-08-vst-plugin.md
"""
