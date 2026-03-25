# Phase 14 — Advanced Analytics Dashboard

> **Goal:** Surface deep insights about the sample library — BPM trends, key
> distribution heatmaps, usage patterns, collection growth over time, and
> producer session statistics. Helps identify creative ruts and opportunities.
>
> **Stack:** Plotly (interactive charts, no server required) · Pandas for aggregation ·
> Flask SSR + HTMX for web dashboard · Tauri webview for desktop mode.
>
> **Prerequisites:** Phase 3 (database), Phase 5 (web UI).

---

## 1. Analytics Data Models

```python
# src/samplemind/analytics/models.py
"""
Analytics data models and aggregation queries.

All analytics are computed on-demand from the SQLite database.
No separate analytics store — SQLite with WAL mode handles these
queries efficiently up to ~500k samples.

Query performance guide:
  - Simple COUNT/GROUP BY: < 5ms up to 100k rows
  - BPM histogram: < 10ms (indexed)
  - Key heatmap: < 15ms
  - Trend over time: < 20ms (requires created_at index)

Add this index if not present:
  CREATE INDEX IF NOT EXISTS idx_samples_created_at ON samples(created_at);
  CREATE INDEX IF NOT EXISTS idx_samples_bpm ON samples(bpm);
  CREATE INDEX IF NOT EXISTS idx_samples_instrument ON samples(instrument);
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from samplemind.data.orm import get_db_path


@dataclass
class AnalyticsSummary:
    total_samples: int
    total_duration_hours: float
    unique_instruments: int
    unique_keys: int
    avg_bpm: float
    most_common_instrument: str
    most_common_key: str
    most_common_mood: str
    samples_this_week: int
    samples_this_month: int


@dataclass
class BpmHistogram:
    buckets: list[str]   # ["60-79", "80-99", "100-119", ...]
    counts: list[int]
    total: int


@dataclass
class KeyHeatmap:
    """
    12×2 heatmap: 12 pitch classes × (major, minor).
    Useful for identifying tonal diversity gaps.
    """
    pitch_classes: list[str]   # ["C", "C#", "D", ...]
    major_counts: list[int]    # one per pitch class
    minor_counts: list[int]
    total: int


@dataclass
class GrowthTimeline:
    """Cumulative library size over time (month by month)."""
    months: list[str]          # ["2025-01", "2025-02", ...]
    cumulative_counts: list[int]
    monthly_additions: list[int]
```

---

## 2. Analytics Engine

```python
# src/samplemind/analytics/engine.py
"""
Analytics query engine — all queries run directly on SQLite.

Each function returns a typed dataclass ready for JSON serialization
or direct chart rendering with Plotly.
"""
from __future__ import annotations
import sqlite3
from collections import Counter, defaultdict
from samplemind.analytics.models import (
    AnalyticsSummary, BpmHistogram, KeyHeatmap, GrowthTimeline
)
from samplemind.data.orm import get_db_path

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BPM_BUCKETS   = [(b, b+19) for b in range(60, 220, 20)]   # [(60,79), (80,99), ...]


def get_summary() -> AnalyticsSummary:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row

    total, dur, avg_bpm, unique_inst, unique_keys = conn.execute("""
        SELECT COUNT(*), SUM(duration), AVG(bpm),
               COUNT(DISTINCT instrument), COUNT(DISTINCT key)
        FROM samples
    """).fetchone()

    most_instrument = (conn.execute(
        "SELECT instrument, COUNT(*) c FROM samples GROUP BY instrument ORDER BY c DESC LIMIT 1"
    ).fetchone() or {"instrument": "unknown"})["instrument"]

    most_key = (conn.execute(
        "SELECT key, COUNT(*) c FROM samples WHERE key IS NOT NULL GROUP BY key ORDER BY c DESC LIMIT 1"
    ).fetchone() or {"key": "unknown"})["key"]

    most_mood = (conn.execute(
        "SELECT mood, COUNT(*) c FROM samples GROUP BY mood ORDER BY c DESC LIMIT 1"
    ).fetchone() or {"mood": "neutral"})["mood"]

    this_week = conn.execute(
        "SELECT COUNT(*) FROM samples WHERE created_at >= datetime('now', '-7 days')"
    ).fetchone()[0] or 0

    this_month = conn.execute(
        "SELECT COUNT(*) FROM samples WHERE created_at >= datetime('now', '-30 days')"
    ).fetchone()[0] or 0

    conn.close()
    return AnalyticsSummary(
        total_samples=total or 0,
        total_duration_hours=round((dur or 0) / 3600, 2),
        unique_instruments=unique_inst or 0,
        unique_keys=unique_keys or 0,
        avg_bpm=round(avg_bpm or 0, 1),
        most_common_instrument=most_instrument,
        most_common_key=most_key,
        most_common_mood=most_mood,
        samples_this_week=this_week,
        samples_this_month=this_month,
    )


def get_bpm_histogram() -> BpmHistogram:
    """BPM distribution in 20-BPM buckets from 60–219."""
    conn = sqlite3.connect(get_db_path())
    bpm_rows = [r[0] for r in conn.execute(
        "SELECT bpm FROM samples WHERE bpm IS NOT NULL AND bpm BETWEEN 60 AND 219"
    ).fetchall()]
    conn.close()

    counts = [0] * len(BPM_BUCKETS)
    for bpm in bpm_rows:
        idx = min(int((bpm - 60) // 20), len(BPM_BUCKETS) - 1)
        if idx >= 0:
            counts[idx] += 1

    return BpmHistogram(
        buckets=[f"{lo}-{hi}" for lo, hi in BPM_BUCKETS],
        counts=counts,
        total=len(bpm_rows),
    )


def get_key_heatmap() -> KeyHeatmap:
    """12×2 key distribution (major and minor per pitch class)."""
    conn = sqlite3.connect(get_db_path())
    rows = conn.execute(
        "SELECT key, COUNT(*) FROM samples WHERE key IS NOT NULL GROUP BY key"
    ).fetchall()
    conn.close()

    key_counts: dict[str, int] = {r[0]: r[1] for r in rows}
    major = [key_counts.get(f"{pc} maj", 0) for pc in PITCH_CLASSES]
    minor = [key_counts.get(f"{pc} min", 0) for pc in PITCH_CLASSES]

    return KeyHeatmap(
        pitch_classes=PITCH_CLASSES,
        major_counts=major,
        minor_counts=minor,
        total=sum(key_counts.values()),
    )


def get_growth_timeline(months_back: int = 12) -> GrowthTimeline:
    """Library growth month-by-month for the past N months."""
    conn = sqlite3.connect(get_db_path())
    rows = conn.execute("""
        SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS cnt
        FROM samples
        WHERE created_at >= datetime('now', ? || ' months')
        GROUP BY month
        ORDER BY month
    """, (f"-{months_back}",)).fetchall()
    conn.close()

    months_data = {r[0]: r[1] for r in rows}
    # Generate all months in range
    from datetime import date
    import calendar
    today = date.today()
    all_months = []
    for i in range(months_back, 0, -1):
        yr = today.year - (1 if today.month - i <= 0 else 0)
        mo = ((today.month - i - 1) % 12) + 1
        all_months.append(f"{yr}-{mo:02d}")

    monthly = [months_data.get(m, 0) for m in all_months]
    cumulative = []
    total = 0
    for n in monthly:
        total += n
        cumulative.append(total)

    return GrowthTimeline(
        months=all_months,
        cumulative_counts=cumulative,
        monthly_additions=monthly,
    )


def get_instrument_energy_matrix() -> dict:
    """
    Cross-tabulation: instrument × energy.
    Returns a matrix useful for a heatmap showing instrument/energy coverage.

    Example:
      {"kick": {"low": 5, "mid": 45, "high": 70}, "pad": {"low": 30, ...}, ...}
    """
    conn = sqlite3.connect(get_db_path())
    rows = conn.execute(
        "SELECT instrument, energy, COUNT(*) FROM samples GROUP BY instrument, energy"
    ).fetchall()
    conn.close()

    matrix: dict[str, dict[str, int]] = defaultdict(lambda: {"low": 0, "mid": 0, "high": 0})
    for instrument, energy, count in rows:
        if energy in ("low", "mid", "high"):
            matrix[instrument][energy] = count
    return dict(matrix)
```

---

## 3. Plotly Chart Generators

```python
# src/samplemind/analytics/charts.py
"""
Interactive Plotly chart generators.

All charts return Plotly figure dicts (JSON-serializable).
They can be rendered in:
  - Flask templates (via plotly.js CDN)
  - Tauri webview (same plotly.js)
  - Jupyter notebooks (for power users)
  - Static PNG export (plotly.io.to_image)
"""
from __future__ import annotations
from samplemind.analytics.engine import (
    get_bpm_histogram, get_key_heatmap,
    get_growth_timeline, get_instrument_energy_matrix
)


def bpm_histogram_chart() -> dict:
    """Bar chart: BPM distribution across the library."""
    data = get_bpm_histogram()
    return {
        "data": [{
            "type": "bar",
            "x": data.buckets,
            "y": data.counts,
            "marker": {"color": "#6366f1"},
            "hovertemplate": "<b>%{x} BPM</b><br>%{y} samples<extra></extra>",
        }],
        "layout": {
            "title": "BPM Distribution",
            "xaxis": {"title": "BPM Range"},
            "yaxis": {"title": "Sample Count"},
            "plot_bgcolor": "#1e1e2e",
            "paper_bgcolor": "#1e1e2e",
            "font": {"color": "#cdd6f4"},
        }
    }


def key_heatmap_chart() -> dict:
    """Heatmap: key signature coverage (12 pitch classes × major/minor)."""
    data = get_key_heatmap()
    return {
        "data": [{
            "type": "heatmap",
            "x": data.pitch_classes,
            "y": ["Major", "Minor"],
            "z": [data.major_counts, data.minor_counts],
            "colorscale": "Viridis",
            "hovertemplate": "<b>%{x} %{y}</b><br>%{z} samples<extra></extra>",
        }],
        "layout": {
            "title": "Key Distribution Heatmap",
            "xaxis": {"title": "Pitch Class"},
            "plot_bgcolor": "#1e1e2e",
            "paper_bgcolor": "#1e1e2e",
            "font": {"color": "#cdd6f4"},
        }
    }


def growth_timeline_chart() -> dict:
    """Line chart: cumulative library growth over time."""
    data = get_growth_timeline()
    return {
        "data": [
            {
                "type": "scatter", "mode": "lines+markers",
                "name": "Cumulative",
                "x": data.months, "y": data.cumulative_counts,
                "line": {"color": "#a6e3a1", "width": 2},
            },
            {
                "type": "bar",
                "name": "Monthly Additions",
                "x": data.months, "y": data.monthly_additions,
                "marker": {"color": "#6366f1", "opacity": 0.6},
                "yaxis": "y2",
            }
        ],
        "layout": {
            "title": "Library Growth Over Time",
            "yaxis":  {"title": "Cumulative Samples"},
            "yaxis2": {"title": "Monthly Additions", "overlaying": "y", "side": "right"},
            "plot_bgcolor": "#1e1e2e",
            "paper_bgcolor": "#1e1e2e",
            "font": {"color": "#cdd6f4"},
        }
    }


def instrument_energy_heatmap_chart() -> dict:
    """Heatmap: instrument × energy coverage gaps."""
    matrix = get_instrument_energy_matrix()
    instruments = sorted(matrix.keys())
    energies = ["low", "mid", "high"]
    z = [[matrix.get(i, {}).get(e, 0) for e in energies] for i in instruments]

    return {
        "data": [{
            "type": "heatmap",
            "x": energies,
            "y": instruments,
            "z": z,
            "colorscale": "Blues",
            "hovertemplate": "<b>%{y} / %{x}</b><br>%{z} samples<extra></extra>",
        }],
        "layout": {
            "title": "Instrument × Energy Coverage",
            "xaxis": {"title": "Energy Level"},
            "yaxis": {"title": "Instrument"},
            "plot_bgcolor": "#1e1e2e",
            "paper_bgcolor": "#1e1e2e",
            "font": {"color": "#cdd6f4"},
        }
    }
```

---

## 4. Flask Analytics Routes

```python
# src/samplemind/web/routes/analytics.py
"""
Analytics dashboard routes.

Routes:
  GET /analytics              → HTML dashboard with all charts
  GET /analytics/summary      → JSON summary stats
  GET /analytics/bpm          → JSON BPM histogram
  GET /analytics/keys         → JSON key heatmap
  GET /analytics/growth       → JSON growth timeline
  GET /analytics/coverage     → JSON instrument × energy matrix
  GET /analytics/export       → Download all analytics as JSON or CSV
"""
from flask import Blueprint, jsonify, render_template
from samplemind.analytics.engine import get_summary, get_bpm_histogram, get_key_heatmap, get_growth_timeline
from samplemind.analytics.charts import (
    bpm_histogram_chart, key_heatmap_chart,
    growth_timeline_chart, instrument_energy_heatmap_chart
)

bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@bp.route("")
def dashboard():
    """Main analytics dashboard — renders all charts via Plotly.js."""
    return render_template("analytics/dashboard.html",
                           summary=get_summary(),
                           bpm_chart=bpm_histogram_chart(),
                           key_chart=key_heatmap_chart(),
                           growth_chart=growth_timeline_chart(),
                           coverage_chart=instrument_energy_heatmap_chart())


@bp.route("/summary")
def summary():
    from dataclasses import asdict
    return jsonify(asdict(get_summary()))


@bp.route("/bpm")
def bpm():
    return jsonify(bpm_histogram_chart())


@bp.route("/keys")
def keys():
    return jsonify(key_heatmap_chart())


@bp.route("/growth")
def growth():
    return jsonify(growth_timeline_chart())
```

Analytics dashboard template (`templates/analytics/dashboard.html`):

```html
{% extends "base.html" %}
{% block content %}
<div class="analytics-grid">
  <!-- Summary KPIs -->
  <div class="kpi-row">
    <div class="kpi">
      <span class="kpi-value">{{ summary.total_samples | number_format }}</span>
      <span class="kpi-label">Total Samples</span>
    </div>
    <div class="kpi">
      <span class="kpi-value">{{ summary.total_duration_hours }}h</span>
      <span class="kpi-label">Total Audio</span>
    </div>
    <div class="kpi">
      <span class="kpi-value">{{ summary.avg_bpm }}</span>
      <span class="kpi-label">Avg BPM</span>
    </div>
    <div class="kpi">
      <span class="kpi-value">{{ summary.samples_this_week }}</span>
      <span class="kpi-label">Added This Week</span>
    </div>
  </div>

  <!-- Charts -->
  <div id="bpm-chart"></div>
  <div id="key-chart"></div>
  <div id="growth-chart"></div>
  <div id="coverage-chart"></div>
</div>

<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<script>
  const charts = {
    'bpm-chart':      {{ bpm_chart | tojson }},
    'key-chart':      {{ key_chart | tojson }},
    'growth-chart':   {{ growth_chart | tojson }},
    'coverage-chart': {{ coverage_chart | tojson }},
  };
  Object.entries(charts).forEach(([id, fig]) => {
    Plotly.newPlot(id, fig.data, fig.layout, {responsive: true, displaylogo: false});
  });
</script>
{% endblock %}
```

---

## 5. Tauri Analytics Command

```rust
// app/src-tauri/src/commands.rs

/// Fetch all analytics data for the desktop dashboard.
#[tauri::command]
pub async fn get_analytics() -> Result<serde_json::Value, String> {
    use std::process::Command;
    let output = Command::new("samplemind")
        .args(["analytics", "--json"])
        .output()
        .map_err(|e| e.to_string())?;
    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
}
```

CLI:

```bash
uv run samplemind analytics              # print summary to terminal
uv run samplemind analytics --json       # full JSON output (all charts)
uv run samplemind analytics --export csv # export to CSV file
```

---

## 6. Testing

```python
# tests/test_analytics.py
"""Tests for Phase 14 analytics engine."""
import pytest
from samplemind.analytics.engine import (
    get_summary, get_bpm_histogram, get_key_heatmap, get_growth_timeline
)


def test_summary_on_empty_db(db):
    summary = get_summary()
    assert summary.total_samples == 0
    assert summary.total_duration_hours == 0.0


def test_bpm_histogram_buckets_correct(db):
    hist = get_bpm_histogram()
    # All buckets should be 20-BPM wide
    assert all("-" in b for b in hist.buckets)
    lo, hi = hist.buckets[0].split("-")
    assert int(hi) - int(lo) == 19


def test_key_heatmap_has_all_pitch_classes(db):
    heatmap = get_key_heatmap()
    assert len(heatmap.pitch_classes) == 12
    assert len(heatmap.major_counts) == 12
    assert len(heatmap.minor_counts) == 12


def test_growth_timeline_length(db):
    timeline = get_growth_timeline(months_back=6)
    assert len(timeline.months) == 6
    assert len(timeline.cumulative_counts) == 6


def test_bpm_histogram_chart_returns_plotly_spec(db):
    from samplemind.analytics.charts import bpm_histogram_chart
    chart = bpm_histogram_chart()
    assert "data" in chart
    assert "layout" in chart
    assert chart["data"][0]["type"] == "bar"
```

---

## 7. Checklist

- [ ] `uv add plotly pandas` — analytics dependencies installed
- [ ] All 4 aggregation queries return correct data
- [ ] BPM histogram has 20-BPM buckets from 60–219
- [ ] Key heatmap covers all 12 pitch classes × 2 modes
- [ ] Growth timeline correctly fills gaps (months with 0 additions)
- [ ] All 4 Plotly charts render in Flask `/analytics` route
- [ ] `uv run samplemind analytics --json` outputs all chart data
- [ ] Tauri `get_analytics` command registered
- [ ] Tests pass on empty and populated DB
- [ ] Created-at index present: `CREATE INDEX idx_samples_created_at ON samples(created_at)`

