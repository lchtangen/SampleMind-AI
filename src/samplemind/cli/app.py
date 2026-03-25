from rich.console import Console
import typer

from samplemind import __version__
from samplemind.cli.commands.analyze import analyze_samples
from samplemind.cli.commands.api import serve_api
from samplemind.cli.commands.duplicates import find_library_duplicates
from samplemind.cli.commands.export import export_samples
from samplemind.cli.commands.health import health_cmd
from samplemind.cli.commands.import_ import import_samples
from samplemind.cli.commands.library import list_samples, search_library
from samplemind.cli.commands.serve import serve
from samplemind.cli.commands.stats import print_stats
from samplemind.cli.commands.tag import tag_samples

console = Console(stderr=True)
app = typer.Typer(help="SampleMind AI — Audio Sample Library Manager")

_JSON_HELP = "Output machine-readable JSON to stdout (for Tauri/IPC consumers)."


@app.command()
def version() -> None:
    """Show the current version."""
    console.print(__version__)


@app.command("import")
def import_(
    source: str = typer.Argument(..., help="Folder containing WAV files"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
    workers: int = typer.Option(0, "--workers", "-w", help="Parallel workers (0 = auto)"),
) -> None:
    """Import WAV samples into the library."""
    import_samples(source, json_output=json, workers=workers)


@app.command("analyze")
def analyze(
    source: str = typer.Argument(..., help="Folder containing WAV files"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Analyze WAV samples without storing them."""
    analyze_samples(source, json_output=json)


@app.command("list")
def list_cmd(
    key: str | None = typer.Option(None, "--key", help="Filter by key (e.g. 'A min')"),
    bpm_min: float | None = typer.Option(None, "--bpm-min", help="Minimum BPM"),
    bpm_max: float | None = typer.Option(None, "--bpm-max", help="Maximum BPM"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """List all samples in the library."""
    list_samples(key=key, bpm_min=bpm_min, bpm_max=bpm_max, json_output=json)


@app.command("search")
def search(
    query: str | None = typer.Argument(None, help="Partial filename or tag"),
    key: str | None = typer.Option(None, "--key", help="Key filter (e.g. 'C maj')"),
    genre: str | None = typer.Option(None, "--genre", help="Genre filter (e.g. trap)"),
    energy: str | None = typer.Option(
        None, "--energy", help="Energy level", metavar="[low|mid|high]"
    ),
    instrument: str | None = typer.Option(
        None,
        "--instrument",
        help="Instrument type",
        metavar="[kick|snare|hihat|bass|pad|lead|loop|sfx|unknown]",
    ),
    bpm_min: float | None = typer.Option(None, "--bpm-min", help="Minimum BPM"),
    bpm_max: float | None = typer.Option(None, "--bpm-max", help="Maximum BPM"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Search the library with multiple filters."""
    search_library(
        query=query,
        key=key,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
        genre=genre,
        energy=energy,
        instrument=instrument,
        json_output=json,
    )


@app.command("tag")
def tag(
    name: str = typer.Argument(..., help="Partial filename to identify the sample"),
    genre: str | None = typer.Option(
        None, "--genre", help="Genre (e.g. trap, lofi, house)"
    ),
    mood: str | None = typer.Option(
        None, "--mood", help="Mood (e.g. dark, chill, euphoric)"
    ),
    energy: str | None = typer.Option(
        None, "--energy", help="Energy level [low|mid|high]"
    ),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated free tags"),
) -> None:
    """Tag a sample with genre, mood, energy."""
    tag_samples(name, genre=genre, mood=mood, energy=energy, tags=tags)


@app.command("serve")
def serve_cmd(
    port: int = typer.Option(5000, "--port", "-p", help="Port for Flask web UI"),
) -> None:
    """Launch the Flask web UI."""
    serve(port=port)


@app.command("api")
def api_cmd(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(
        False, "--reload", help="Enable uvicorn auto-reload (dev only)"
    ),
) -> None:
    """Launch the FastAPI REST API server (auth + JSON endpoints)."""
    serve_api(host=host, port=port, reload=reload)


@app.command("duplicates")
def duplicates_cmd(
    remove: bool = typer.Option(
        False,
        "--remove",
        help="Delete all but the earliest-imported copy of each duplicate group.",
    ),
) -> None:
    """Detect (and optionally remove) exact duplicate WAV files in the library.

    Duplicate detection uses SHA-256 of the first 64 KB of each file.
    Without --remove, lists duplicate groups and exits with code 1 if any are found.
    With --remove, deletes duplicate files from disk and removes their DB records,
    keeping the copy with the earliest imported_at timestamp.
    """
    find_library_duplicates(remove=remove)


@app.command("export")
def export_cmd(
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Destination folder (default: ./samplemind-export).",
    ),
    organize: str | None = typer.Option(
        None,
        "--organize",
        help="Create subfolders by: instrument | mood | genre",
        metavar="[instrument|mood|genre]",
    ),
    energy: str | None = typer.Option(
        None,
        "--energy",
        help="Filter by energy level [low|mid|high]",
    ),
    instrument: str | None = typer.Option(
        None,
        "--instrument",
        help="Filter by instrument [kick|snare|hihat|bass|pad|lead|loop|sfx|unknown]",
    ),
    mood: str | None = typer.Option(
        None,
        "--mood",
        help="Filter by mood [dark|chill|aggressive|euphoric|melancholic|neutral]",
    ),
    bpm_min: float | None = typer.Option(None, "--bpm-min", help="Minimum BPM"),
    bpm_max: float | None = typer.Option(None, "--bpm-max", help="Maximum BPM"),
) -> None:
    """Export filtered samples to a folder with FL Studio-compatible naming.

    Files are renamed to: {stem}_{bpm}bpm_{key}_{energy}.wav
    Use --organize to group them into subfolders by instrument, mood, or genre.
    """
    from pathlib import Path

    export_samples(
        target=Path(target) if target else None,
        organize=organize,
        energy=energy,
        instrument=instrument,
        mood=mood,
        bpm_min=bpm_min,
        bpm_max=bpm_max,
    )


@app.command("stats")
def stats_cmd(
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Print a Rich summary of library statistics.

    Shows total count, BPM distribution (min/max/mean/median), and
    breakdowns by energy level, instrument type, and mood.
    """
    print_stats(json_output=json)


@app.command("health")
def health(
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Run system health checks (database + audio libraries).

    Exits 0 when all checks pass, 1 when any check fails.
    """
    health_cmd(json_output=json)


# ── Phase 7 stubs ────────────────────────────────────────────────────────────

@app.command("export-to-fl")
def export_to_fl(
    energy: str | None = typer.Option(None, "--energy", help="Filter by energy [low|mid|high]"),
    instrument: str | None = typer.Option(None, "--instrument", help="Filter by instrument type"),
) -> None:
    """Export samples to FL Studio's Samples/SampleMind folder. [Phase 7]"""
    typer.echo("Not yet implemented — Phase 7 (FL Studio Integration)", err=True)
    raise typer.Exit(1)


@app.command("midi-sync")
def midi_sync(
    bpm: float = typer.Argument(..., help="BPM to broadcast via MIDI clock"),
) -> None:
    """Send BPM as MIDI clock to FL Studio via IAC Driver. [Phase 7]"""
    typer.echo("Not yet implemented — Phase 7 (FL Studio Integration)", err=True)
    raise typer.Exit(1)


# ── Phase 9 stub ─────────────────────────────────────────────────────────────

@app.command("pack")
def pack_cmd(
    action: str = typer.Argument(..., help="Action: create | import | verify | list"),
) -> None:
    """Manage .smpack sample pack archives (create, import, verify). [Phase 9]"""
    typer.echo("Not yet implemented — Phase 9 (Sample Packs)", err=True)
    raise typer.Exit(1)


# ── Phase 11 stub ────────────────────────────────────────────────────────────

@app.command("similar")
def similar_cmd(
    path: str = typer.Argument(..., help="Reference WAV file path"),
    top_k: int = typer.Option(10, "--top", "-k", help="Number of results"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Find samples similar to a reference file using semantic search. [Phase 11]"""
    typer.echo("Not yet implemented — Phase 11 (Semantic Search)", err=True)
    raise typer.Exit(1)


# ── Phase 12 stub ────────────────────────────────────────────────────────────

@app.command("curate")
def curate_cmd(
    prompt: str | None = typer.Argument(None, help="Curation goal (e.g. 'dark trap set')"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """AI-powered library curation and smart playlist generation. [Phase 12]"""
    typer.echo("Not yet implemented — Phase 12 (AI Curation)", err=True)
    raise typer.Exit(1)


# ── Phase 14 stub ────────────────────────────────────────────────────────────

@app.command("analytics")
def analytics_cmd(
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Show library analytics: BPM distribution, key heatmap, mood breakdown. [Phase 14]"""
    typer.echo("Not yet implemented — Phase 14 (Analytics)", err=True)
    raise typer.Exit(1)


# ── Phase 16 stub ────────────────────────────────────────────────────────────

@app.command("generate")
def generate_cmd(
    prompt: str = typer.Argument(..., help="Text description of the sound to generate"),
    duration: float = typer.Option(4.0, "--duration", "-d", help="Duration in seconds"),
    backend: str = typer.Option("audiocraft", "--backend", help="Backend [audiocraft|stable_audio|mock]"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Generate an audio sample from a text prompt using AI. [Phase 16]"""
    typer.echo("Not yet implemented — Phase 16 (AI Generation)", err=True)
    raise typer.Exit(1)
