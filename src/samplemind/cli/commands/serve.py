"""Serve the Flask web UI."""

import sys

from samplemind.data.database import init_db
from samplemind.data.orm import init_orm
from samplemind.web.app import app as flask_app


def serve(port: int = 5000) -> None:
    """Launch the Flask web UI."""
    # Initialise both DB layers before the first request arrives so that
    # the login/register routes can access the `users` table immediately.
    init_orm()   # SQLModel: creates `users` table if absent
    init_db()    # sqlite3:  creates `samples` table if absent
    print(f"🎧 SampleMind AI web UI → http://localhost:{port}", file=sys.stderr)
    print(f"   Login             → http://localhost:{port}/login", file=sys.stderr)
    flask_app.run(debug=False, port=port, host="127.0.0.1")
