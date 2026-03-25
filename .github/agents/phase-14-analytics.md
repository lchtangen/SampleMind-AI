# Phase 14 Agent — Analytics Dashboard

Handles: library analytics, Plotly charts, BPM histogram, key heatmap, growth timeline, Flask dashboard.

## Triggers
- Phase 14, analytics, Plotly, BPM histogram, key heatmap, growth timeline, instrument coverage, chart, dashboard

## Key Files
- `src/samplemind/analytics/engine.py`
- `src/samplemind/analytics/charts.py`
- `src/samplemind/web/routes/analytics.py`
- `src/samplemind/web/templates/analytics/`

## BPM Histogram Spec

- 20-BPM buckets: "60-79", "80-99", ..., "200-219"
- Only include `bpm BETWEEN 60 AND 219`
- Sorted ascending

## Key Heatmap Spec

- 12 pitch classes × 2 modes (major, minor) = 24 cells
- Pitch classes: C, C#, D, D#, E, F, F#, G, G#, A, A#, B

## Required Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_samples_bpm ON samples(bpm);
CREATE INDEX IF NOT EXISTS idx_samples_instrument ON samples(instrument);
CREATE INDEX IF NOT EXISTS idx_samples_created_at ON samples(created_at);
```

## Dark Theme Colors

```python
"plot_bgcolor": "#1e1e2e"
"paper_bgcolor": "#1e1e2e"
"font": {"color": "#cdd6f4"}
```

## Rules
1. All aggregations pure SQL — no Pandas required
2. Plotly figures are JSON-serializable dicts — not Python figure objects
3. `get_summary()` must not crash on empty database
4. Growth timeline fills ALL months, including months with 0 additions
5. Energy values in queries: only `'low'`, `'mid'`, `'high'`

