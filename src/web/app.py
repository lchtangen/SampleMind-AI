"""
app.py — SampleMind AI Flask web server

Routes:
  GET  /              → main library view (with optional filter params)
  GET  /api/samples   → JSON endpoint used by app.js for live search
  POST /api/tag       → update tags on a sample via the web UI
  POST /api/import    → import a folder of WAV files (called from Tauri via JS)
  GET  /api/status    → health check + library stats
  GET  /audio/<id>    → stream a WAV file to the browser for playback

Flask concepts:
- @app.route("/path") decorates a function as a URL handler
- request.args = query string params (?key=value)
- request.json = parsed JSON body from POST requests
- jsonify() converts a dict/list to a JSON response
- send_file() streams a file back to the browser
"""

import sys
import os

# Make sure imports from src/ work when running from inside src/web/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, render_template, request, jsonify, send_file
from data.database import init_db, search_samples, tag_sample, get_all_samples, count_samples

app = Flask(__name__)


@app.route("/")
def index():
    """
    Main page. Reads filter params from the URL query string so
    bookmarking a filtered view works.
    Example: /?genre=trap&energy=high
    """
    init_db()
    filters = {
        "query":      request.args.get("q"),
        "genre":      request.args.get("genre"),
        "energy":     request.args.get("energy"),
        "key":        request.args.get("key"),
        "instrument": request.args.get("instrument"),
        "bpm_min":    request.args.get("bpm_min", type=float),
        "bpm_max":    request.args.get("bpm_max", type=float),
    }
    samples = search_samples(**filters)
    total = count_samples()
    return render_template("index.html", samples=samples, total=total, filters=filters)


@app.route("/api/samples")
def api_samples():
    """
    JSON endpoint for live search (called by app.js as you type).
    Returns a list of sample dicts instead of rendered HTML.
    """
    init_db()
    filters = {
        "query":      request.args.get("q"),
        "genre":      request.args.get("genre"),
        "energy":     request.args.get("energy"),
        "key":        request.args.get("key"),
        "instrument": request.args.get("instrument"),
        "bpm_min":    request.args.get("bpm_min", type=float),
        "bpm_max":    request.args.get("bpm_max", type=float),
    }
    rows = search_samples(**filters)
    # sqlite3.Row objects aren't JSON-serializable, so convert to plain dicts
    return jsonify([dict(r) for r in rows])


@app.route("/api/tag", methods=["POST"])
def api_tag():
    """
    Update tags on a sample from the web UI.
    Expects JSON body: { "path": "...", "genre": "...", "mood": "...", ... }
    """
    data = request.json or {}
    path = data.get("path")
    if not path:
        return jsonify({"error": "path is required"}), 400

    updated = tag_sample(
        path=path,
        genre=data.get("genre"),
        mood=data.get("mood"),
        energy=data.get("energy"),
        tags=data.get("tags"),
    )
    if updated:
        return jsonify({"ok": True})
    return jsonify({"error": "Sample not found"}), 404


@app.route("/api/import", methods=["POST"])
def api_import():
    """
    Import a folder of WAV files, triggered from the Tauri desktop app.

    Flow:
      1. Tauri Rust opens a native folder-picker dialog
      2. JS receives the selected path
      3. JS POSTs {"path": "/chosen/folder"} here
      4. Flask runs the importer and returns results

    The importer runs synchronously — for large folders this blocks,
    but it's fine for now. Future: use Server-Sent Events for progress.
    """
    data = request.json or {}
    folder = data.get("path", "").strip()

    if not folder:
        return jsonify({"error": "path is required"}), 400
    if not os.path.isdir(folder):
        return jsonify({"error": f"Not a directory: {folder}"}), 400

    # Capture importer output by redirecting stdout temporarily
    import io, contextlib
    from cli.importer import import_samples

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            import_samples(folder)
        output = buf.getvalue()
        # Count how many were imported from the output line
        imported = sum(1 for line in output.splitlines() if line.strip().startswith("✅"))
        return jsonify({"ok": True, "imported": imported, "log": output})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/import-files", methods=["POST"])
def api_import_files():
    """
    Import a specific list of WAV file paths.
    Used when the user drag-drops individual files (not a whole folder).

    Expects: { "paths": ["/abs/path/to/a.wav", "/abs/path/to/b.wav", ...] }
    """
    data  = request.json or {}
    paths = data.get("paths", [])

    if not paths:
        return jsonify({"error": "paths list is required"}), 400

    import io, contextlib
    from analyzer.audio_analysis import analyze_file
    from data.database import init_db, save_sample

    init_db()
    imported, errors = 0, []

    for file_path in paths:
        if not file_path.lower().endswith(".wav"):
            continue
        if not os.path.isfile(file_path):
            errors.append(f"Not found: {file_path}")
            continue
        try:
            r = analyze_file(file_path)
            save_sample(
                filename=os.path.basename(file_path),
                path=os.path.abspath(file_path),
                bpm=r["bpm"], key=r["key"],
                mood=r["mood"], energy=r["energy"],
                instrument=r["instrument"],
            )
            imported += 1
        except Exception as e:
            errors.append(f"{os.path.basename(file_path)}: {e}")

    return jsonify({"ok": True, "imported": imported, "errors": errors})


@app.route("/api/status")
def api_status():
    """Health check + library stats. Used by the JS to know the server is up."""
    init_db()
    return jsonify({"ok": True, "total": count_samples()})


@app.route("/audio/<int:sample_id>")
def stream_audio(sample_id):
    """
    Stream a WAV file by its database ID so the browser can play it.
    The browser's <audio> tag will call this URL.
    """
    init_db()
    from data.database import _connect
    with _connect() as conn:
        row = conn.execute("SELECT path FROM samples WHERE id = ?", (sample_id,)).fetchone()
    if not row or not os.path.exists(row["path"]):
        return "File not found", 404
    return send_file(row["path"], mimetype="audio/wav")


if __name__ == "__main__":
    init_db()
    print("🎧 SampleMind AI running at http://localhost:5000")
    app.run(debug=True, port=5000)
