"""
SampleMind AI Flask web server

Routes:
  GET  /              → main library view (login-protected)
  GET  /login         → login page
  POST /login         → authenticate and redirect
  GET  /register      → registration page
  POST /register      → create account and redirect
  GET  /logout        → clear session and redirect to /login
  GET  /api/samples   → JSON endpoint used by app.js for live search
  POST /api/tag       → update tags on a sample via the web UI
  POST /api/import    → import a folder of WAV files (called from Tauri via JS)
  GET  /api/status    → health check + library stats
  GET  /audio/<id>    → stream a WAV file to the browser for playback
"""

import contextlib
import functools
import io
import os
import sys

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.cli.commands.import_ import import_samples
from samplemind.core.config import get_settings
from samplemind.core.models.sample import SampleCreate, SampleUpdate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.data.repositories.user_repository import UserRepository

_settings = get_settings()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = _settings.FLASK_SECRET_KEY

# ── One-time startup initialisation ──────────────────────────────────────────
# Called before the first request to ensure both DB layers are ready.
# init_orm() is idempotent — safe to call multiple times.
_orm_initialised = False


@app.before_request
def _bootstrap_databases() -> None:
    global _orm_initialised  # noqa: PLW0603
    if not _orm_initialised:
        init_orm()   # creates all SQLModel tables (users, samples, …) if absent
        _orm_initialised = True


# ── Auth helpers ───────────────────────────────────────────────────────────────


def _get_current_user():
    """Return the User object for the active session, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return UserRepository.get_by_id(user_id)


def login_required(fn):
    """Decorator: redirect unauthenticated requests to /login."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login_get"))
        return fn(*args, **kwargs)

    return wrapper


# ── Auth routes ────────────────────────────────────────────────────────────────


@app.route("/login", methods=["GET"])
def login_get():
    if session.get("user_id"):
        return redirect(url_for("index"))
    return render_template("login.html", message=request.args.get("message"))


@app.route("/login", methods=["POST"])
def login_post():
    from samplemind.core.auth import verify_password

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = UserRepository.get_by_email(username) or UserRepository.get_by_username(username)
    if user is None or not verify_password(password, user.hashed_password):
        return render_template("login.html", error="Invalid email/username or password", username=username)

    if not user.is_active:
        return render_template("login.html", error="Account is deactivated", username=username)

    UserRepository.record_login(user.user_id)
    session["user_id"] = user.user_id
    session.permanent = True
    return redirect(url_for("index"))


@app.route("/register", methods=["GET"])
def register_get():
    if session.get("user_id"):
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_post():
    from samplemind.core.auth import hash_password

    email = request.form.get("email", "").strip().lower()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    error = None
    if not email or not username or not password:
        error = "All fields are required"
    elif password != confirm:
        error = "Passwords do not match"
    elif len(password) < 8:
        error = "Password must be at least 8 characters"
    elif not any(c.isupper() for c in password):
        error = "Password must contain at least one uppercase letter"
    elif not any(c.isdigit() for c in password):
        error = "Password must contain at least one digit"
    elif UserRepository.exists_by_email(email):
        error = "Email already registered"
    elif UserRepository.exists_by_username(username):
        error = "Username already taken"

    if error:
        return render_template("register.html", error=error, email=email, username=username)

    user = UserRepository.create(
        email=email,
        username=username,
        hashed_password=hash_password(password),
    )
    session["user_id"] = user.user_id
    session.permanent = True
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_get", message="You have been signed out"))


# ── Library routes ─────────────────────────────────────────────────────────────


@app.route("/")
@login_required
def index():
    """Main page. Reads filter params from the URL query string."""
    filters = {
        "query":      request.args.get("q"),
        "genre":      request.args.get("genre"),
        "energy":     request.args.get("energy"),
        "key":        request.args.get("key"),
        "instrument": request.args.get("instrument"),
        "bpm_min":    request.args.get("bpm_min", type=float),
        "bpm_max":    request.args.get("bpm_max", type=float),
    }
    samples = SampleRepository.search(**filters)
    total = SampleRepository.count()
    current_user = _get_current_user()
    return render_template("index.html", samples=samples, total=total, filters=filters, current_user=current_user)


@app.route("/api/samples")
def api_samples():
    """
    JSON endpoint for live search (called by app.js as you type).
    Returns a list of sample dicts instead of rendered HTML.
    """
    filters = {
        "query":      request.args.get("q"),
        "genre":      request.args.get("genre"),
        "energy":     request.args.get("energy"),
        "key":        request.args.get("key"),
        "instrument": request.args.get("instrument"),
        "bpm_min":    request.args.get("bpm_min", type=float),
        "bpm_max":    request.args.get("bpm_max", type=float),
    }
    rows = SampleRepository.search(**filters)
    return jsonify([
        {
            "id": s.id, "filename": s.filename, "path": s.path,
            "bpm": s.bpm, "key": s.key, "mood": s.mood,
            "energy": s.energy, "instrument": s.instrument,
            "genre": s.genre, "tags": s.tags,
        }
        for s in rows
    ])


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

    update = SampleUpdate(
        genre=data.get("genre"),
        mood=data.get("mood"),
        energy=data.get("energy"),
        tags=data.get("tags"),
    )
    updated = SampleRepository.tag(path, update)
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
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            import_samples(folder)
        output = buf.getvalue()
        # Count how many were imported from the output
        imported = output.count("✔")
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

    imported, errors = 0, []

    for file_path in paths:
        if not file_path.lower().endswith(".wav"):
            continue
        if not os.path.isfile(file_path):
            errors.append(f"Not found: {file_path}")
            continue
        try:
            r = analyze_file(file_path)
            data_obj = SampleCreate(
                filename=os.path.basename(file_path),
                path=os.path.abspath(file_path),
                bpm=r.get("bpm"), key=r.get("key"),
                mood=r.get("mood"), energy=r.get("energy"),
                instrument=r.get("instrument"),
            )
            SampleRepository.upsert(data_obj)
            imported += 1
        except Exception as e:
            errors.append(f"{os.path.basename(file_path)}: {e}")

    return jsonify({"ok": True, "imported": imported, "errors": errors})


@app.route("/api/status")
def api_status():
    """Health check + library stats. Used by the JS to know the server is up."""
    return jsonify({"ok": True, "total": SampleRepository.count()})


@app.route("/audio/<int:sample_id>")
def stream_audio(sample_id):
    """
    Stream a WAV file by its database ID so the browser can play it.
    The browser's <audio> tag will call this URL.
    """
    sample = SampleRepository.get_by_id(sample_id)
    if not sample or not os.path.exists(sample.path):
        return "File not found", 404
    return send_file(sample.path, mimetype="audio/wav")
