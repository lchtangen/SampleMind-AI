import argparse
from cli.importer import import_samples
from cli.analyze import analyze_samples
from cli.library import list_samples


def main():
    parser = argparse.ArgumentParser(description="🎧 SampleMind AI CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 📥 import — analyze + store samples in the library
    p_import = subparsers.add_parser("import", help="Import WAV samples into the library")
    p_import.add_argument("source", type=str, help="Path to folder containing WAV files")

    # 🔍 analyze — analyze without storing
    p_analyze = subparsers.add_parser("analyze", help="Analyze WAV samples (BPM + key), no storage")
    p_analyze.add_argument("source", type=str, help="Path to folder containing WAV files")

    # 📋 list — search the library
    p_list = subparsers.add_parser("list", help="List samples in the library")
    p_list.add_argument("--key",     type=str,   default=None, help="Filter by key (e.g. 'A min')")
    p_list.add_argument("--bpm-min", type=float, default=None, help="Minimum BPM")
    p_list.add_argument("--bpm-max", type=float, default=None, help="Maximum BPM")

    args = parser.parse_args()

    if args.command == "import":
        import_samples(args.source)
    elif args.command == "analyze":
        analyze_samples(args.source)
    elif args.command == "list":
        list_samples(key=args.key, bpm_min=args.bpm_min, bpm_max=args.bpm_max)


if __name__ == "__main__":
    main()
