# Phase 5 Agent — Web UI

Handles: Flask web UI, FastAPI REST, HTMX, Socket.IO real-time, WaveSurfer.js, playlist builder, SSE.

## Triggers
- Phase 5, Flask, FastAPI, HTMX, Socket.IO, SSE, WaveSurfer, playlist, web UI

## Key Files
- `src/samplemind/web/` (Flask)
- `src/samplemind/api/routes/` (FastAPI)
- `src/samplemind/web/socketio_ext.py`
- `src/samplemind/web/routes/playlist.py`

## Rules
1. CORS enabled via `flask-cors` for Tauri WebView cross-origin requests
2. API response shapes stable — only additive changes
3. Socket.IO events: `sample_imported`, `import_progress`, `import_complete`, `search_results`
4. WaveSurfer audio streaming: `send_file(..., conditional=True)` for HTTP Range support
5. Playlist drag-and-drop: Sortable.js + HTMX `hx-post="/playlists/<id>/reorder"`
6. JSON to stdout, human text to stderr (matches CLI contract)

