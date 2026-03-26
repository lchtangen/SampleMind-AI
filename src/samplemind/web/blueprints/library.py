"""
Library blueprint — auth, library view, HTMX partials, and API endpoints.

Routes:
  GET  /login              → login page
  POST /login              → authenticate and redirect
  GET  /register           → registration page
  POST /register           → create account and redirect
  GET  /logout             → clear session and redirect to /login
  GET  /                   → main library view (login-protected)
  GET  /samples/partial    → HTMX partial: sample table fragment
  GET  /api/samples        → JSON endpoint for live search
  POST /api/tag            → update tags on a sample
  POST /api/import-files   → import specific file paths
  GET  /api/status         → health check + library stats
  GET  /audio/<id>         → stream a WAV file for playback
"""

from __future__ import annotations

import functools
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.core.models.sample import SampleCreate, SampleUpdate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.data.repositories.user_repository import UserRepository

library_bp = Blueprint("library", __name__)


@library_bp.before_app_request
def _setup() -> None:
    """Ensure all SQLModel tables exist before the first request.

    init_orm() is idempotent — safe to call on every startup.
    It imports both models and calls SQLModel.metadata.create_all(engine).
    """
    init_orm()


# ── Auth helpers ──────────────────────────────────────────────────────────────


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
            return redirect(url_for("library.login_get"))
        return fn(*args, **kwargs)

    return wrapper


# ── Auth routes ───────────────────────────────────────────────────────────────


@library_bp.route("/login", methods=["GET"])
def login_get():
    if session.get("user_id"):
        return redirect(url_for("library.index"))
    return render_template("login.html", message=request.args.get("message"))


@library_bp.route("/login", methods=["POST"])
def login_post():
    from samplemind.core.auth import verify_password

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = UserRepository.get_by_email(username) or UserRepository.get_by_username(
        username
    )
    if user is None or not verify_password(password, user.hashed_password):
        return render_template(
            "login.html", error="Invalid email/username or password", username=username
        )

    if not user.is_active:
        return render_template(
            "login.html", error="Account is deactivated", username=username
        )

    UserRepository.record_login(user.user_id)
    session["user_id"] = user.user_id
    session.permanent = True
    return redirect(url_for("library.index"))


@library_bp.route("/register", methods=["GET"])
def register_get():
    if session.get("user_id"):
        return redirect(url_for("library.index"))
    return render_template("register.html")


@library_bp.route("/register", methods=["POST"])
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
        return render_template(
            "register.html", error=error, email=email, username=username
        )

    user = UserRepository.create(
        email=email,
        username=username,
        hashed_password=hash_password(password),
    )
    session["user_id"] = user.user_id
    session.permanent = True
    return redirect(url_for("library.index"))


@library_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("library.login_get", message="You have been signed out"))


# ── Library routes ────────────────────────────────────────────────────────────


@library_bp.route("/")
@login_required
def index():
    """Main page. Reads filter params from the URL query string."""
    filters = {
        "query": request.args.get("q"),
        "genre": request.args.get("genre"),
        "energy": request.args.get("energy"),
        "key": request.args.get("key"),
        "instrument": request.args.get("instrument"),
        "bpm_min": request.args.get("bpm_min", type=float),
        "bpm_max": request.args.get("bpm_max", type=float),
    }
    samples = SampleRepository.search(**filters)
    total = SampleRepository.count()
    current_user = _get_current_user()
    return render_template(
        "index.html",
        samples=samples,
        total=total,
        filters=filters,
        current_user=current_user,
    )


@library_bp.route("/samples/partial")
def samples_partial():
    """HTMX partial: returns only the sample table fragment.

    Called when any search filter changes (triggered by hx-get on the inputs).
    All filter parameters are optional — omitting one means "any value".
    """
    samples = SampleRepository.search(
        query=request.args.get("q"),
        energy=request.args.get("energy"),
        instrument=request.args.get("instrument"),
        bpm_min=float(request.args["bpm_min"]) if request.args.get("bpm_min") else None,
        bpm_max=float(request.args["bpm_max"]) if request.args.get("bpm_max") else None,
        key=request.args.get("key"),
        genre=request.args.get("genre"),
    )
    return render_template("partials/sample_table.html", samples=samples)


@library_bp.route("/audio/<int:sample_id>")
def audio(sample_id: int):
    """Serve the audio file for a sample with HTTP Range support.

    conditional=True enables Range requests so WaveSurfer.js can seek
    large audio files without downloading them fully first.
    Returns 404 if the row doesn't exist or the file has been moved/deleted.
    """
    sample = SampleRepository.get_by_id(sample_id)
    if not sample:
        abort(404)
    path = Path(sample.path)
    if not path.exists():
        abort(404)
    return send_file(
        str(path),
        mimetype="audio/wav",
        conditional=True,
        etag=True,
        last_modified=path.stat().st_mtime,
    )


# ── JSON API routes ───────────────────────────────────────────────────────────


@library_bp.route("/api/samples")
def api_samples():
    """JSON endpoint for live search. Returns a list of sample dicts."""
    filters = {
        "query": request.args.get("q"),
        "genre": request.args.get("genre"),
        "energy": request.args.get("energy"),
        "key": request.args.get("key"),
        "instrument": request.args.get("instrument"),
        "bpm_min": request.args.get("bpm_min", type=float),
        "bpm_max": request.args.get("bpm_max", type=float),
    }
    rows = SampleRepository.search(**filters)
    return jsonify(
        [
            {
                "id": s.id,
                "filename": s.filename,
                "path": s.path,
                "bpm": s.bpm,
                "key": s.key,
                "mood": s.mood,
                "energy": s.energy,
                "instrument": s.instrument,
                "genre": s.genre,
                "tags": s.tags,
            }
            for s in rows
        ]
    )


@library_bp.route("/api/tag", methods=["POST"])
def api_tag():
    """Update tags on a sample from the web UI.

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


@library_bp.route("/api/import-files", methods=["POST"])
def api_import_files():
    """Import a specific list of WAV file paths (drag-drop individual files).

    Expects: { "paths": ["/abs/path/to/a.wav", ...] }
    """
    data = request.json or {}
    paths = data.get("paths", [])

    if not paths:
        return jsonify({"error": "paths list is required"}), 400

    imported, errors = 0, []

    for file_path in paths:
        if not file_path.lower().endswith(".wav"):
            continue
        fp = Path(file_path)
        if not fp.is_file():
            errors.append(f"Not found: {file_path}")
            continue
        try:
            r = analyze_file(file_path)
            data_obj = SampleCreate(
                filename=fp.name,
                path=str(fp.resolve()),
                bpm=r.get("bpm"),
                key=r.get("key"),
                mood=r.get("mood"),
                energy=r.get("energy"),
                instrument=r.get("instrument"),
            )
            SampleRepository.upsert(data_obj)
            imported += 1
        except Exception as e:
            errors.append(f"{fp.name}: {e}")

    return jsonify({"ok": True, "imported": imported, "errors": errors})


@library_bp.route("/api/bulk-tag", methods=["POST"])
def api_bulk_tag():
    """Apply the same tag update to multiple samples at once.

    Expects JSON body:
        { "paths": ["/abs/path/a.wav", ...], "genre": "trap", "mood": "dark", ... }

    Only non-null fields in the body are written; omitted fields are left unchanged.
    Returns { "ok": true, "updated": N } where N is the number of rows written.
    """
    data = request.json or {}
    paths = data.get("paths", [])
    if not paths:
        return jsonify({"error": "paths list is required"}), 400

    update = SampleUpdate(
        genre=data.get("genre"),
        mood=data.get("mood"),
        energy=data.get("energy"),
        tags=data.get("tags"),
    )
    updated = sum(1 for p in paths if SampleRepository.tag(p, update))
    return jsonify({"ok": True, "updated": updated})


@library_bp.route("/analytics")
@login_required
def analytics():
    """Analytics dashboard — BPM distribution, energy/mood/instrument breakdowns."""
    from samplemind.analytics.engine import get_bpm_buckets, get_key_counts, get_summary

    summary = get_summary()
    bpm_buckets = get_bpm_buckets(buckets=8)
    key_counts = get_key_counts()
    return render_template(
        "analytics/dashboard.html",
        summary=summary,
        bpm_buckets=bpm_buckets,
        key_counts=key_counts,
    )


@library_bp.route("/api/status")
def api_status():
    """Health check + library stats."""
    return jsonify({"ok": True, "total": SampleRepository.count()})


@library_bp.route("/api/export-to-fl", methods=["POST"])
@login_required
def api_export_to_fl():
    """Export filtered samples to the FL Studio SampleMind folder.

    JSON body (all fields optional):
        energy     — filter: "low" | "mid" | "high"
        instrument — filter: "kick" | "snare" | "hihat" | ...
        dest       — absolute path override for the destination folder

    Returns:
        200  {"ok": true,  "copied": N, "skipped": M, "targets": T}
        400  {"error": "dest must be an absolute path"}
        500  {"error": "<RuntimeError from export_to_fl_studio>"}
    """
    from samplemind.integrations.filesystem import export_to_fl_studio

    data = request.json or {}
    energy: str | None = data.get("energy") or None
    instrument: str | None = data.get("instrument") or None
    dest_raw: str | None = data.get("dest") or None

    dest_dir: Path | None = None
    if dest_raw:
        dest_dir = Path(dest_raw)
        if not dest_dir.is_absolute():
            return jsonify({"error": "dest must be an absolute path"}), 400

    samples = SampleRepository.search(energy=energy, instrument=instrument)
    sample_paths = [Path(s.path) for s in samples if Path(s.path).exists()]

    try:
        result = export_to_fl_studio(sample_paths, dest_dir=dest_dir)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({"ok": True, **result})

