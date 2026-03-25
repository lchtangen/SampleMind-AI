"""Length-prefixed JSON message schema for the JUCE sidecar protocol (v2).

Phase 8 — VST3/AU Plugin.
Defines the wire format:
  Request:  [4-byte big-endian int: payload length] [UTF-8 JSON bytes]
  Response: [4-byte big-endian int: payload length] [UTF-8 JSON bytes]

Supported actions: ping, search, analyze, batch_analyze
"""
# TODO: implement in Phase 8 — VST3/AU Plugin
