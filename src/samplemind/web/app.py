"""
SampleMind AI Flask web server — Application Factory.

Usage:
    from samplemind.web.app import create_app
    app = create_app()          # production
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})  # tests

A module-level ``app`` instance is kept for backward compatibility with
the legacy Tauri sidecar (``src/main.py``) and ``serve.py``.
"""

from __future__ import annotations

from typing import Any

from flask import Flask, render_template
from flask_cors import CORS

from samplemind.core.config import get_settings


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Application Factory.

    Parameters
    ----------
    config:
        Optional dict of Flask config overrides (used in tests).

    Returns
    -------
    Flask
        A fully-configured Flask application with blueprints registered.
    """
    settings = get_settings()

    flask_app = Flask(__name__, template_folder="templates", static_folder="static")
    flask_app.secret_key = settings.flask_secret_key

    # Allow CORS for Tauri WebView and any frontend origin in dev
    CORS(flask_app, origins=["http://localhost:5174", "tauri://localhost"])

    # Apply test/runtime overrides
    if config:
        flask_app.config.update(config)

    # Initialise ORM (idempotent — safe to call multiple times)
    from samplemind.data.orm import init_orm

    init_orm()

    # Register blueprints
    from samplemind.web.blueprints.import_ import import_bp
    from samplemind.web.blueprints.library import library_bp

    flask_app.register_blueprint(library_bp)
    flask_app.register_blueprint(import_bp)

    # Error handlers
    @flask_app.errorhandler(404)
    def not_found(e: Exception) -> tuple[str, int]:
        return render_template("404.html"), 404

    @flask_app.errorhandler(500)
    def server_error(e: Exception) -> tuple[str, int]:
        return render_template("500.html"), 500

    return flask_app


# Module-level app kept for backward compat with src/main.py and Tauri dev mode.
# New code should call create_app() instead.
app = create_app()
