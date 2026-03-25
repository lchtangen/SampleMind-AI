# Phase 14 Agent — Analytics Dashboard

Handles: library statistics, Plotly interactive charts, BPM/key distribution, growth timelines.

## Triggers
Phase 14, analytics, Plotly, BPM histogram, key heatmap, growth timeline, `bpm_histogram_chart`, `get_key_heatmap`, `get_summary`, `src/samplemind/analytics/`, "show analytics", "library stats", "BPM distribution"

**File patterns:** `src/samplemind/analytics/**/*.py`

**Code patterns:** `import plotly`, `bpm_histogram_chart`, `get_key_heatmap`, `get_summary`

## Key Files
```
src/samplemind/analytics/
  models.py     — AnalyticsSummary, BpmHistogram, KeyHeatmap, GrowthTimeline
  queries.py    — pure SQLite SQL aggregation queries
  charts.py     — Plotly figure builders
  routes.py     — Flask routes for analytics page
  cli.py        — CLI: samplemind analytics --json
```

## Technology Stack
| Component | Technology |
|-----------|-----------|
| Charts | Plotly (plotly.py + plotly.js) — interactive |
| Aggregation | Pure SQLite SQL — < 20ms for 500k samples |
| Web display | Flask SSR + Jinja2 |
| Desktop | Tauri webview (same Plotly.js) |

## CLI Commands
```bash
uv run samplemind analytics --json        # JSON analytics data (for piping)
uv run samplemind analytics               # Rich table summary in terminal
```

## Key Analytics
- **BPM histogram**: distribution of BPMs across the library
- **Key heatmap**: sample count per musical key (C, C#, D, ... B)
- **Instrument coverage**: count per instrument type
- **Energy distribution**: low/mid/high breakdown
- **Growth timeline**: samples added per week/month

## Rules
1. All SQL aggregation in `queries.py` — no logic in routes or charts
2. Chart data injected as JSON into Jinja2 templates
3. `--json` flag outputs raw analytics data to stdout (for Tauri/piping)
4. Aggregations must run in < 100ms for libraries up to 500k samples
5. All charts must work in both Flask (SSR) and Tauri webview (client-side)

