"""asyncio Unix socket server — the JUCE plugin's Python IPC endpoint.

Phase 8 — VST3/AU Plugin.
Starts an asyncio server on ~/tmp/samplemind.sock and dispatches incoming
JSON requests to the SampleRepository and Audio Analyzer.

Startup signals readiness with: {"status": "ready", "version": 2}
Health pings respond with:       {"status": "ok", "action": "ping"}
"""
# TODO: implement in Phase 8 — VST3/AU Plugin
