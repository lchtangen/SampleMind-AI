"""Plotly figure factories for the analytics dashboard.

Phase 14 — Analytics.
Each function returns a plotly.graph_objects.Figure:
  bpm_histogram_chart()    -- BPM distribution histogram
  key_heatmap_chart()      -- 12-semitone x major/minor heatmap
  mood_donut_chart()       -- mood label proportions
  energy_bar_chart()       -- low/mid/high energy counts
  growth_timeline_chart()  -- cumulative library size over time

All functions raise ImportError with an install hint when plotly is absent.
Install with: uv sync --extra analytics
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import plotly.graph_objects as go  # only for type hints — not imported at runtime


_PLOTLY_INSTALL_HINT = (
    "plotly is required for chart generation. "
    "Install it with: uv sync --extra analytics"
)


def _require_plotly() -> Any:
    """Return the plotly.graph_objects module or raise ImportError."""
    try:
        import plotly.graph_objects as go  # noqa: PLC0415

        return go
    except ImportError as exc:
        raise ImportError(_PLOTLY_INSTALL_HINT) from exc


# ── Chart factories ───────────────────────────────────────────────────────────


def bpm_histogram_chart(buckets: int = 10) -> "go.Figure":
    """BPM distribution histogram.

    Args:
        buckets: Number of histogram bins.

    Returns:
        plotly.graph_objects.Figure with a Bar trace showing BPM bucket counts.
    """
    go = _require_plotly()
    from samplemind.analytics.engine import get_bpm_buckets  # noqa: PLC0415

    data = get_bpm_buckets(buckets=buckets)
    labels = [b.label for b in data]
    counts = [b.count for b in data]

    fig = go.Figure(
        data=[go.Bar(x=labels, y=counts, name="BPM Distribution")],
        layout=go.Layout(
            title="BPM Distribution",
            xaxis_title="BPM Range",
            yaxis_title="Sample Count",
        ),
    )
    return fig


def key_heatmap_chart() -> "go.Figure":
    """12-semitone × major/minor heatmap of key frequency.

    Returns:
        plotly.graph_objects.Figure with a Heatmap trace.
        Rows: major / minor. Columns: C, C#, D, D#, E, F, F#, G, G#, A, A#, B
    """
    go = _require_plotly()
    from samplemind.analytics.engine import get_key_counts  # noqa: PLC0415

    key_counts = get_key_counts()
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    modes = ["maj", "min"]

    # Build 2×12 grid
    z = [[key_counts.get(f"{note} {mode}", 0) for note in notes] for mode in modes]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=notes,
            y=["Major", "Minor"],
            colorscale="Blues",
            hoverongaps=False,
        ),
        layout=go.Layout(
            title="Key Distribution Heatmap",
            xaxis_title="Note",
            yaxis_title="Mode",
        ),
    )
    return fig


def mood_donut_chart() -> "go.Figure":
    """Donut chart of mood label proportions.

    Returns:
        plotly.graph_objects.Figure with a Pie (hole=0.4) trace.
    """
    go = _require_plotly()
    from samplemind.analytics.engine import get_summary  # noqa: PLC0415

    summary = get_summary()
    labels = list(summary.by_mood.keys())
    values = list(summary.by_mood.values())

    fig = go.Figure(
        data=[go.Pie(labels=labels, values=values, hole=0.4, name="Mood")],
        layout=go.Layout(title="Mood Distribution"),
    )
    return fig


def energy_bar_chart() -> "go.Figure":
    """Bar chart of low / mid / high energy sample counts.

    Returns:
        plotly.graph_objects.Figure with a Bar trace.
    """
    go = _require_plotly()
    from samplemind.analytics.engine import get_summary  # noqa: PLC0415

    summary = get_summary()
    # Always show all three levels even if count is zero
    levels = ["low", "mid", "high"]
    counts = [summary.by_energy.get(level, 0) for level in levels]

    fig = go.Figure(
        data=[go.Bar(x=levels, y=counts, name="Energy Level")],
        layout=go.Layout(
            title="Energy Distribution",
            xaxis_title="Energy Level",
            yaxis_title="Sample Count",
        ),
    )
    return fig


def growth_timeline_chart(
    bucket: str = "week",
) -> "go.Figure":
    """Line chart showing cumulative library growth over time.

    Args:
        bucket: Time granularity — "day", "week", or "month".

    Returns:
        plotly.graph_objects.Figure with a Scatter (mode="lines+markers") trace.
    """
    go = _require_plotly()
    from samplemind.analytics.engine import get_growth_timeline  # noqa: PLC0415

    timeline = get_growth_timeline(bucket=bucket)  # type: ignore[arg-type]
    periods = [t["period"] for t in timeline]
    counts = [t["count"] for t in timeline]

    fig = go.Figure(
        data=[
            go.Scatter(
                x=periods,
                y=counts,
                mode="lines+markers",
                name="Library Growth",
            )
        ],
        layout=go.Layout(
            title=f"Library Growth ({bucket}ly)",
            xaxis_title="Period",
            yaxis_title="Cumulative Sample Count",
        ),
    )
    return fig
