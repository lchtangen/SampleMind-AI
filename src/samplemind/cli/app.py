import typer
from rich.console import Console
from samplemind import __version__
from samplemind.cli.commands.import_ import import_samples
from samplemind.cli.commands.analyze import analyze_samples
from samplemind.cli.commands.library import list_samples, search_library
from samplemind.cli.commands.tag import tag_samples
from samplemind.cli.commands.serve import serve

console = Console(stderr=True)
app = typer.Typer(help="🎧 SampleMind AI — Audio Sample Library Manager")


@app.command()
def version() -> None:
    """Show the current version."""
    console.print(__version__)


@app.command("import")
def import_(source: str = typer.Argument(..., help="Folder containing WAV files")) -> None:
    """Import WAV samples into the library."""
    import_samples(source)


@app.command("analyze")
def analyze(source: str = typer.Argument(..., help="Folder containing WAV files")) -> None:
    """Analyze WAV samples without storing them."""
    analyze_samples(source)


@app.command("list")
def list_cmd(
    key: str | None = typer.Option(None, "--key", help="Filter by key (e.g. 'A min')"),
    bpm_min: float | None = typer.Option(None, "--bpm-min", help="Minimum BPM"),
    bpm_max: float | None = typer.Option(None, "--bpm-max", help="Maximum BPM"),
) -> None:
    """List all samples in the library."""
    list_samples(key=key, bpm_min=bpm_min, bpm_max=bpm_max)


@app.command("search")
def search(
    query: str | None = typer.Argument(None, help="Partial filename or tag"),
    key: str | None = typer.Option(None, "--key", help="Key filter (e.g. 'C maj')"),
    genre: str | None = typer.Option(None, "--genre", help="Genre filter (e.g. trap)"),
    energy: str | None = typer.Option(
        None, "--energy", help="Energy level",
        metavar="[low|mid|high]"
    ),
    instrument: str | None = typer.Option(
        None, "--instrument",
        help="Instrument type",
        metavar="[kick|snare|hihat|bass|pad|lead|loop|sfx|unknown]"
    ),
    bpm_min: float | None = typer.Option(None, "--bpm-min", help="Minimum BPM"),
    bpm_max: float | None = typer.Option(None, "--bpm-max", help="Maximum BPM"),
) -> None:
    """Search the library with multiple filters."""
    search_library(
        query=query, key=key, bpm_min=bpm_min, bpm_max=bpm_max,
        genre=genre, energy=energy, instrument=instrument
    )


@app.command("tag")
def tag(
    name: str = typer.Argument(..., help="Partial filename to identify the sample"),
    genre: str | None = typer.Option(None, "--genre", help="Genre (e.g. trap, lofi, house)"),
    mood: str | None = typer.Option(None, "--mood", help="Mood (e.g. dark, chill, euphoric)"),
    energy: str | None = typer.Option(None, "--energy", help="Energy level [low|mid|high]"),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated free tags"),
) -> None:
    """Tag a sample with genre, mood, energy."""
    tag_samples(name, genre=genre, mood=mood, energy=energy, tags=tags)


@app.command("serve")
def serve_cmd(
    port: int = typer.Option(5000, "--port", "-p", help="Port for Flask web UI")
) -> None:
    """Launch the Flask web UI."""
    serve(port=port)
