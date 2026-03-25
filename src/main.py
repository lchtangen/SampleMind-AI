import argparse

from cli.analyze import analyze_samples
from cli.importer import import_samples
from cli.library import list_samples, search_library
from cli.tagger import tag_samples


def _serve(port: int):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from data.database import init_db
    from web.app import app
    init_db()
    print(f"🎧 SampleMind AI web UI → http://localhost:{port}")
    app.run(debug=False, port=port)


def main():
    parser = argparse.ArgumentParser(description="🎧 SampleMind AI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 📥 import — analyze + store
    p = subparsers.add_parser("import", help="Import WAV samples into the library")
    p.add_argument("source", help="Folder containing WAV files")

    # 🔍 analyze — analyze without storing
    p = subparsers.add_parser("analyze", help="Analyze WAV samples (BPM + key), no storage")
    p.add_argument("source", help="Folder containing WAV files")

    # 📋 list — browse the library
    p = subparsers.add_parser("list", help="List all samples in the library")
    p.add_argument("--key",     default=None, help="Filter by key (e.g. 'A min')")
    p.add_argument("--bpm-min", type=float, default=None, help="Minimum BPM")
    p.add_argument("--bpm-max", type=float, default=None, help="Maximum BPM")

    # 🔎 search — multi-filter search
    p = subparsers.add_parser("search", help="Search the library with multiple filters")
    p.add_argument("query",        nargs="?", default=None, help="Partial filename or tag")
    p.add_argument("--key",        default=None, help="Key filter (e.g. 'C maj')")
    p.add_argument("--genre",      default=None, help="Genre filter (e.g. trap)")
    p.add_argument("--energy",     default=None, choices=["low", "mid", "high"])
    p.add_argument("--instrument", default=None,
                   choices=["kick","snare","hihat","bass","pad","lead","loop","sfx","unknown"])
    p.add_argument("--bpm-min", type=float, default=None)
    p.add_argument("--bpm-max", type=float, default=None)

    # 🏷️ tag — manually set genre/mood/energy/tags
    p = subparsers.add_parser("tag", help="Tag a sample with genre, mood, energy")
    p.add_argument("name",     help="Partial filename to identify the sample")
    p.add_argument("--genre",  default=None, help="Genre (e.g. trap, lofi, house)")
    p.add_argument("--mood",   default=None, help="Mood (e.g. dark, chill, euphoric)")
    p.add_argument("--energy", default=None, choices=["low", "mid", "high"])
    p.add_argument("--tags",   default=None, help="Comma-separated free tags")

    # 🌐 serve — launch the web UI
    p = subparsers.add_parser("serve", help="Launch the web UI at localhost:5000")
    p.add_argument("--port", type=int, default=5000)

    args = parser.parse_args()

    if args.command == "import":
        import_samples(args.source)
    elif args.command == "analyze":
        analyze_samples(args.source)
    elif args.command == "list":
        list_samples(key=args.key, bpm_min=args.bpm_min, bpm_max=args.bpm_max)
    elif args.command == "search":
        search_library(query=args.query, key=args.key, bpm_min=args.bpm_min,
                       bpm_max=args.bpm_max, genre=args.genre, energy=args.energy,
                       instrument=args.instrument)
    elif args.command == "tag":
        tag_samples(args.name, genre=args.genre, mood=args.mood,
                    energy=args.energy, tags=args.tags)
    elif args.command == "serve":
        _serve(args.port)


if __name__ == "__main__":
    main()
