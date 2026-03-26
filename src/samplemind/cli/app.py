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
from samplemind.cli.commands.tag import auto_tag_samples, tag_samples

console = Console(stderr=True)
app = typer.Typer(help="SampleMind AI — Audio Sample Library Manager")

_JSON_HELP = "Output machine-readable JSON to stdout (for Tauri/IPC consumers)."


@app.command()
def version() -> None:
    """Show the current version."""
    typer.echo(__version__)


@app.command("import")
def import_(
    source: str = typer.Argument(..., help="Folder containing WAV files"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
    workers: int = typer.Option(0, "--workers", "-w", help="Parallel workers (0 = auto)"),
    auto_tag: bool = typer.Option(
        False, "--auto-tag",
        help="Auto-tag imported samples using LocalAIEngine (rule-based if no model)",
    ),
    deduplicate: bool = typer.Option(
        False, "--deduplicate", "--dedup",
        help="Skip files whose SHA-256 fingerprint already exists in the library",
    ),
) -> None:
    """Import WAV samples into the library."""
    import_samples(source, json_output=json, workers=workers,
                   auto_tag=auto_tag, deduplicate=deduplicate)


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
    name: str | None = typer.Argument(None, help="Partial filename to identify the sample"),
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
    auto: bool = typer.Option(False, "--auto", help="AI auto-tag one sample via LocalAIEngine"),
    auto_all: bool = typer.Option(False, "--auto-all", help="AI auto-tag entire library"),
    model: str | None = typer.Option(None, "--model", help="Path to GGUF model file"),
    workers: int = typer.Option(4, "--workers", help="Parallel workers for --auto-all"),
    download_model: bool = typer.Option(
        False, "--download-model", help="Download the default Llama 3.2 1B model first"
    ),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Tag a sample with genre, mood, energy — or auto-tag via LocalAIEngine.

    \b
    Manual tagging:
      samplemind tag kick_128 --genre trap --energy high
    AI auto-tag one sample (rule-based fallback if model not found):
      samplemind tag kick_128 --auto
    AI auto-tag entire library:
      samplemind tag --auto-all --workers 4
    Download the Llama model then auto-tag:
      samplemind tag --auto-all --download-model
    """
    if auto or auto_all or download_model:
        sample_name = None if auto_all else name
        auto_tag_samples(sample_name, model, workers, download_model, json)
    else:
        if not name:
            console.print("[red]Error:[/red] name argument is required for manual tagging.")
            raise typer.Exit(1)
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


# ── Phase 8: Sidecar server ──────────────────────────────────────────────────

@app.command("sidecar")
def sidecar_cmd(
    socket: str = typer.Option(
        None,
        "--socket",
        help="Unix socket path (default: ~/tmp/samplemind.sock)",
    ),
) -> None:
    """Start the Python sidecar IPC server for the JUCE VST3/AU plugin.

    Binds a Unix domain socket and dispatches JSON requests from the plugin
    to the SampleRepository and Audio Analyzer.  Signals readiness with a
    single JSON line on stdout:  {"status": "ready", "version": 2, ...}
    """
    import asyncio

    from samplemind.sidecar.server import DEFAULT_SOCKET_PATH, run_server

    asyncio.run(run_server(socket_path=socket or DEFAULT_SOCKET_PATH))


# ── Phase 7: FL Studio integration ───────────────────────────────────────────

@app.command("export-to-fl")
def export_to_fl(
    energy: str | None = typer.Option(None, "--energy", help="Filter by energy [low|mid|high]"),
    instrument: str | None = typer.Option(None, "--instrument", help="Filter by instrument type"),
    dest: str | None = typer.Option(None, "--dest", help="Override FL Studio target folder"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Export samples to FL Studio's Patches/Samples/SampleMind folder.

    Auto-detects FL Studio 20/21 installation paths.  Use --dest to override.
    Skips files already up-to-date in the destination.
    """
    import json as _json
    from pathlib import Path

    from samplemind.data.orm import init_orm
    from samplemind.data.repositories.sample_repository import SampleRepository
    from samplemind.integrations.filesystem import export_to_fl_studio

    init_orm()
    samples = SampleRepository.search(energy=energy, instrument=instrument)
    paths = [Path(s.path) for s in samples if Path(s.path).exists()]

    try:
        result = export_to_fl_studio(paths, dest_dir=Path(dest) if dest else None)
    except RuntimeError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    if json:
        typer.echo(_json.dumps(result))
    else:
        console.print(
            f"[green]Exported[/green] {result['copied']} file(s) to "
            f"{result['targets']} FL Studio folder(s) "
            f"({result['skipped']} skipped — already up to date)"
        )


@app.command("midi-sync")
def midi_sync(
    bpm: float = typer.Argument(..., help="BPM value to send via MIDI CC"),
    port: str = typer.Option("IAC Driver Bus 1", "--port", help="MIDI output port name"),
) -> None:
    """Send BPM to FL Studio via MIDI CC on the IAC Driver (macOS) or loopMIDI (Windows).

    Encodes BPM as a 14-bit value across CC 14 (MSB) and CC 46 (LSB) on channel 1.
    FL Studio must be configured to receive these CCs via a MIDI controller mapping.
    """
    from samplemind.integrations.midi import send_bpm_via_midi

    try:
        send_bpm_via_midi(bpm, port_name=port)
    except RuntimeError as exc:
        console.print(f"[red]MIDI error:[/red] {exc}")
        raise typer.Exit(1) from exc

    console.print(f"[green]Sent[/green] BPM={bpm:.1f} via MIDI CC to {port!r}")


# ── Phase 9: Sample Pack management ──────────────────────────────────────────

@app.command("pack")
def pack_cmd(
    action: str = typer.Argument(..., help="Action: create | import | verify | list"),
    path: str = typer.Argument("", help="Source folder (create) or .smpack file (import/verify)"),
    name: str | None = typer.Option(None, "--name", help="Pack name (create only)"),
    version_str: str = typer.Option("1.0.0", "--version", help="Semver version string (create only)"),
    author: str = typer.Option("unknown", "--author", help="Pack author (create only)"),
    description: str = typer.Option("", "--description", help="Pack description (create only)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output .smpack path (create only)"),
    dest: str | None = typer.Option(None, "--dest", help="Destination folder (import only)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Verify checksums without importing (import/verify)"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Manage .smpack sample pack archives.

    \b
    Actions:
      create  — Build a .smpack archive from a folder of WAV files
      import  — Verify and import a .smpack into the library
      verify  — Verify checksums only (alias for import --dry-run)
      list    — List .smpack files in the default packs directory
    """
    import json as _json
    from pathlib import Path

    from samplemind.packs.builder import PackBuildError, create_pack
    from samplemind.packs.importer import PackIntegrityError, import_pack

    if action == "create":
        if not path:
            console.print("[red]Error:[/red] path to WAV folder is required for 'create'", style="")
            raise typer.Exit(1)
        try:
            result_path = create_pack(
                Path(path),
                name=name or Path(path).name,
                version=version_str,
                author=author,
                description=description,
                output_path=Path(output) if output else None,
            )
        except PackBuildError as exc:
            console.print(f"[red]Pack build error:[/red] {exc}")
            raise typer.Exit(1) from exc

        if json:
            typer.echo(_json.dumps({"smpack": str(result_path)}))
        else:
            console.print(f"[green]Created:[/green] {result_path}")

    elif action in ("import", "verify"):
        if not path:
            console.print("[red]Error:[/red] path to .smpack file is required", style="")
            raise typer.Exit(1)
        is_dry = dry_run or action == "verify"
        try:
            samples = import_pack(
                Path(path),
                dest_dir=Path(dest) if dest else None,
                dry_run=is_dry,
            )
        except FileNotFoundError as exc:
            console.print(f"[red]Not found:[/red] {exc}")
            raise typer.Exit(1) from exc
        except ValueError as exc:
            console.print(f"[red]Invalid pack:[/red] {exc}")
            raise typer.Exit(1) from exc
        except PackIntegrityError as exc:
            console.print(f"[red]Integrity error:[/red] {exc}")
            raise typer.Exit(1) from exc

        if json:
            typer.echo(_json.dumps({"imported": len(samples), "dry_run": is_dry}))
        else:
            label = "Verified" if is_dry else "Imported"
            console.print(f"[green]{label}:[/green] {len(samples)} sample(s)")

    elif action == "list":
        from samplemind.core.config import get_settings
        db_url = get_settings().database_url
        db_parent = Path(db_url.removeprefix("sqlite:///")).parent
        packs_dir = db_parent / "packs"
        if not packs_dir.exists():
            console.print("No packs directory found.")
            raise typer.Exit(0)
        smpack_files = sorted(packs_dir.rglob("*.smpack"))
        if json:
            typer.echo(_json.dumps({"packs": [str(p) for p in smpack_files]}))
        else:
            if not smpack_files:
                console.print("No .smpack files found.")
            for p in smpack_files:
                console.print(str(p))

    else:
        console.print(f"[red]Unknown action:[/red] {action!r}. Use: create | import | verify | list")
        raise typer.Exit(1)


# ── Phase 13: Cloud Sync ──────────────────────────────────────────────────────


@app.command("sync")
def sync_cmd(
    action: str = typer.Argument(..., help="push | pull | status"),
    paths: list[str] = typer.Argument(default=None, help="Files/dirs to push (push only)"),
    dest: str = typer.Option("", "--dest", "-d", help="Destination dir for pull"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Cloud sync — push/pull audio files to S3-compatible storage (R2, S3, B2)."""
    import json as _json
    from pathlib import Path as _Path

    if action == "push":
        from samplemind.sync.file_sync import push_files

        resolved = [_Path(p) for p in (paths or [])]
        if not resolved:
            console.print("[red]Error:[/red] Provide at least one file or directory to push.")
            raise typer.Exit(1)
        result = push_files(resolved)
        if json:
            typer.echo(_json.dumps(result))
        else:
            console.print(
                f"[green]Uploaded:[/green] {result['uploaded']}  "
                f"Skipped: {result['skipped']}  Errors: {result['errors']}"
            )

    elif action == "pull":
        from samplemind.sync.file_sync import pull_files

        dst = _Path(dest) if dest else _Path.cwd()
        result = pull_files(dst)
        if json:
            typer.echo(_json.dumps(result))
        else:
            console.print(
                f"[green]Downloaded:[/green] {result['downloaded']}  "
                f"Skipped: {result['skipped']}  Errors: {result['errors']}"
            )

    elif action == "status":
        from samplemind.sync.config import get_sync_settings

        s = get_sync_settings()
        data = {
            "endpoint": s.endpoint_url,
            "bucket": s.bucket,
            "prefix": s.prefix,
            "dry_run": s.dry_run,
            "credentials_set": bool(s.access_key),
        }
        if json:
            typer.echo(_json.dumps(data))
        else:
            console.print_json(_json.dumps(data))

    else:
        console.print(f"[red]Unknown action:[/red] {action!r}. Use: push | pull | status")
        raise typer.Exit(1)


# ── Phase 11: Semantic Search ─────────────────────────────────────────────────


@app.command("similar")
def similar_cmd(
    path: str = typer.Argument(..., help="Reference WAV file path"),
    top_k: int = typer.Option(10, "--top", "-k", help="Number of results"),
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Find samples similar to a reference file using audio feature embeddings."""
    import json as _json
    from pathlib import Path as _Path

    from samplemind.data.orm import init_orm
    from samplemind.data.repositories.sample_repository import SampleRepository
    from samplemind.search.embeddings import embed_audio
    from samplemind.search.vector_index import VectorIndex

    ref = _Path(path)
    if not ref.exists():
        typer.echo(f"File not found: {path}", err=True)
        raise typer.Exit(1)

    init_orm()

    vec = embed_audio(ref)
    idx = VectorIndex()
    idx.ensure_tables()
    sample_ids = idx.search_audio(vec, k=top_k)
    idx.close()

    samples = [SampleRepository.get_by_id(sid) for sid in sample_ids]
    samples = [s for s in samples if s is not None]

    if json:
        from samplemind.core.models.sample import SamplePublic
        typer.echo(_json.dumps([SamplePublic.model_validate(s).model_dump(mode="json") for s in samples]))
    else:
        from rich.console import Console
        from rich.table import Table

        console = Console(stderr=True)
        t = Table(title=f"Top {top_k} Similar Samples")
        t.add_column("ID", justify="right")
        t.add_column("Filename")
        t.add_column("BPM", justify="right")
        t.add_column("Energy")
        for s in samples:
            t.add_row(str(s.id), s.filename, f"{s.bpm:.1f}" if s.bpm else "-", s.energy or "-")
        console.print(t)


# ── Phase 12: AI Curation ─────────────────────────────────────────────────────


@app.command("curate")
def curate_cmd(
    action: str = typer.Argument(
        "analyze",
        help="Sub-command: analyze | playlist | gaps  (default: analyze)",
    ),
    prompt: str | None = typer.Option(None, "--prompt", "-p", help="Curation goal for 'analyze'"),
    # playlist options
    arc: str | None = typer.Option(
        None,
        "--arc",
        help="Energy arc for 'playlist', comma-separated: e.g. low,mid,high,high",
    ),
    mood: str | None = typer.Option(None, "--mood", help="Mood filter for 'playlist'"),
    instrument: str | None = typer.Option(None, "--instrument", help="Instrument filter for 'playlist'"),
    # gaps options
    target_kicks: int = typer.Option(10, "--kicks", help="Target kick count for 'gaps'"),
    target_snares: int = typer.Option(8, "--snares", help="Target snare count for 'gaps'"),
    target_hihats: int = typer.Option(12, "--hihats", help="Target hihat count for 'gaps'"),
    # shared
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
    model: str = typer.Option("claude-haiku-4-5-20251001", "--model", help="pydantic-ai model ID"),
) -> None:
    """AI-powered library curation.

    \b
    Sub-commands:
      analyze   Run CuratorAgent (requires Claude API key) — default
      playlist  Generate an energy-arc playlist from the library (offline)
      gaps      Analyse missing instrument types vs a target profile (offline)

    \b
    Examples:
      samplemind curate
      samplemind curate analyze --prompt "dark trap set"
      samplemind curate playlist --arc low,mid,high,high --mood dark
      samplemind curate gaps --kicks 20 --snares 15 --json
    """
    import json as _json

    from samplemind.data.orm import init_orm

    init_orm()

    _console = __import__("rich.console", fromlist=["Console"]).Console(stderr=True)

    # ── playlist sub-command ─────────────────────────────────────────────────
    if action == "playlist":
        from samplemind.agent.playlist import playlist_by_energy

        _arc = [e.strip() for e in (arc or "low,mid,high").split(",")]
        samples = playlist_by_energy(_arc, mood=mood, instrument=instrument)

        if json:
            typer.echo(_json.dumps([
                {"id": s.id, "filename": s.filename, "energy": s.energy,
                 "mood": s.mood, "bpm": s.bpm, "key": s.key}
                for s in samples
            ]))
        else:
            from rich.table import Table

            table = Table(show_header=True, header_style="bold cyan", box=None)
            table.add_column("#", width=4)
            table.add_column("Filename", min_width=30)
            table.add_column("Energy", width=7)
            table.add_column("Mood", width=12)
            table.add_column("BPM", justify="right", width=7)
            table.add_column("Key", width=8)
            for i, s in enumerate(samples, 1):
                table.add_row(
                    str(i), s.filename, s.energy or "", s.mood or "",
                    str(s.bpm or ""), s.key or "",
                )
            _console.print(f"\n[bold]Playlist — arc: {' → '.join(_arc)}[/bold]")
            _console.print(table)
            _console.print(f"\n[green]{len(samples)} track(s) generated.[/green]")
        return

    # ── gaps sub-command ─────────────────────────────────────────────────────
    if action == "gaps":
        from samplemind.agent.playlist import gap_analysis

        target = {"kick": target_kicks, "snare": target_snares, "hihat": target_hihats}
        result = gap_analysis(target)

        if json:
            typer.echo(_json.dumps(result))
        else:
            _console.print("\n[bold]Library Gap Analysis[/bold]")
            for inst, data in result.items():
                surplus = data.get("surplus", 0)
                color = "green" if surplus >= 0 else "red"
                sign = "+" if surplus >= 0 else ""
                _console.print(
                    f"  {inst:10s} {data.get('actual', 0):3d}/{data.get('target', 0):3d}"
                    f"  [{color}]{sign}{surplus}[/{color}]"
                )
        return

    # ── analyze sub-command (default — calls CuratorAgent) ───────────────────
    if action not in ("analyze",):
        # Treat any unrecognised action as a free-form prompt for backward compat
        prompt = prompt or action

    from samplemind.agent.curator import CuratorAgent

    _prompt = prompt or "Analyse my sample library and suggest improvements."
    agent = CuratorAgent(model_id=model)

    try:
        result = agent.curate_sync(_prompt)
    except Exception as exc:
        typer.echo(f"Curation failed: {exc}", err=True)
        raise typer.Exit(1) from exc

    if json:
        typer.echo(_json.dumps({
            "recommendations": result.recommendations,
            "suggested_tags": result.suggested_tags,
            "gap_analysis": result.gap_analysis,
            "energy_arc": result.energy_arc,
        }))
    else:
        _console.print("[bold]Curation Recommendations[/bold]")
        for rec in result.recommendations:
            _console.print(f"  • {rec}")
        if result.energy_arc:
            _console.print(f"\nEnergy arc: {' → '.join(result.energy_arc)}")
        if result.gap_analysis:
            _console.print("\n[bold]Gap Analysis[/bold]")
            for inst, data in result.gap_analysis.items():
                surplus = data.get("surplus", 0)
                symbol = "+" if surplus >= 0 else ""
                _console.print(
                    f"  {inst}: {data.get('actual', 0)}/{data.get('target', 0)} ({symbol}{surplus})"
                )


# ── Phase 14: Analytics ───────────────────────────────────────────────────────


@app.command("analytics")
def analytics_cmd(
    json: bool = typer.Option(False, "--json", help=_JSON_HELP),
    export_html: str | None = typer.Option(None, "--export-html", help="Render Plotly dashboard to HTML file"),
) -> None:
    """Show library analytics: BPM distribution, key heatmap, mood breakdown."""
    import json as _json

    from samplemind.analytics.engine import get_bpm_buckets, get_summary
    from samplemind.data.orm import init_orm

    init_orm()

    summary = get_summary()

    if json:
        typer.echo(_json.dumps({
            "total": summary.total,
            "by_energy": summary.by_energy,
            "by_mood": summary.by_mood,
            "by_instrument": summary.by_instrument,
            "bpm_min": summary.bpm_min,
            "bpm_max": summary.bpm_max,
            "bpm_mean": summary.bpm_mean,
        }))
        return

    from rich.console import Console
    from rich.table import Table

    console = Console(stderr=True)
    console.print(f"[bold]Library Analytics[/bold] — {summary.total} sample(s)\n")

    # Energy breakdown
    t = Table(title="Energy")
    t.add_column("Level")
    t.add_column("Count", justify="right")
    for level in ("low", "mid", "high"):
        t.add_row(level, str(summary.by_energy.get(level, 0)))
    console.print(t)

    # BPM summary
    if summary.bpm_mean is not None:
        console.print(
            f"\nBPM: min={summary.bpm_min:.1f}  "
            f"max={summary.bpm_max:.1f}  "
            f"mean={summary.bpm_mean:.1f}"
        )

    # BPM buckets
    buckets = get_bpm_buckets()
    if buckets:
        t2 = Table(title="\nBPM Distribution")
        t2.add_column("Range")
        t2.add_column("Count", justify="right")
        for b in buckets:
            t2.add_row(b.label, str(b.count))
        console.print(t2)

    if export_html:
        try:
            from pathlib import Path

            import plotly.graph_objects as go  # noqa: F401
            import plotly.io as pio

            from samplemind.analytics.charts import (
                bpm_histogram_chart,
                energy_bar_chart,
            )

            figs = [bpm_histogram_chart(), energy_bar_chart()]
            html_parts = [pio.to_html(f, full_html=False, include_plotlyjs="cdn") for f in figs]
            html = "<html><body>" + "\n".join(html_parts) + "</body></html>"
            Path(export_html).write_text(html)
            typer.echo(f"Dashboard exported to {export_html}", err=True)
        except ImportError:
            typer.echo("plotly not installed — run: uv sync --extra analytics", err=True)
            raise typer.Exit(1)


# ── Phase 16 stub ────────────────────────────────────────────────────────────

@app.command("generate")
def generate_cmd(
    prompt: str = typer.Argument(..., help="Text description of the sound to generate"),
    duration: float = typer.Option(5.0, "--duration", "-d", help="Duration in seconds"),
    bpm: float | None = typer.Option(None, "--bpm", help="Target BPM hint"),
    key: str | None = typer.Option(None, "--key", help="Target key hint, e.g. 'C major'"),
    backend: str = typer.Option(
        "mock",
        "--backend",
        "-b",
        help="Backend: mock | audiocraft | stable_audio",
    ),
    auto_import: bool = typer.Option(False, "--import", help="Auto-import into library after generation"),
    json_output: bool = typer.Option(False, "--json", help=_JSON_HELP),
) -> None:
    """Generate an audio sample from a text prompt using AI. [Phase 16]"""
    import json as _json

    from samplemind.generation.models import GenerationRequest
    from samplemind.generation.pipeline import generate

    req = GenerationRequest(
        prompt=prompt,
        duration_seconds=duration,
        bpm=bpm,
        key=key,
        backend=backend,
    )
    try:
        result = generate(req, auto_import=auto_import)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)
    except ImportError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    if json_output:
        typer.echo(_json.dumps(result.model_dump(mode="json")))
    else:
        console.print(f"[green]Generated:[/green] {result.output_path}")
        if result.sample_id is not None:
            console.print(f"[dim]Imported as sample #{result.sample_id}[/dim]")
