"""Serve the Flask web UI."""

from samplemind.data.database import init_db
from samplemind.web.app import app as flask_app


def serve(port: int = 5000):
    """Launch the Flask web UI."""
    init_db()
    print(f"🎧 SampleMind AI web UI → http://localhost:{port}")
    flask_app.run(debug=False, port=port)
