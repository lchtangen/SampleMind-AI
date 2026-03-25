"""Serve the Flask web UI."""

import sys


def serve(port: int = 5000) -> None:
    """Launch the Flask web UI."""
    # Lazy import to avoid circular dependency:
    # web/app.py → cli/commands.import_ → cli/commands.__init__ → serve → web/app.py
    from samplemind.web.app import create_app

    flask_app = create_app()
    print(f"🎧 SampleMind AI web UI → http://localhost:{port}", file=sys.stderr)
    print(f"   Login             → http://localhost:{port}/login", file=sys.stderr)
    flask_app.run(debug=False, port=port, host="127.0.0.1")
