"""
samplemind.__main__ — Entry point for `python -m samplemind`.

Delegates directly to the Typer CLI application defined in
samplemind.cli.app so that both `uv run samplemind` and
`python -m samplemind` invoke the same command tree.
"""

from samplemind.cli.app import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
