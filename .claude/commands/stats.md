# /stats — Library Statistics

Show SampleMind library statistics: total sample count, breakdowns by instrument, energy,
mood, and musical key, BPM distribution, and top user-defined tags.

## Arguments

$ARGUMENTS
Optional:
  --json     Output raw JSON to stdout (machine-readable)
  --full     Include per-instrument BPM ranges and mood cross-tabs

Examples:
  /stats
  /stats --json
  /stats --full

---

Parse flags from $ARGUMENTS.

**Step 1 — Run stats command:**

```bash
uv run samplemind stats --json
```

If the `stats` command is not yet implemented, fall back to a direct DB query:

```python
uv run python -c "
from samplemind.data.orm import init_orm, get_session
from samplemind.data.repositories.sample_repository import SampleRepository
from sqlmodel import select, func
from samplemind.core.models.sample import Sample
import json

init_orm()
with get_session() as sess:
    total = sess.exec(select(func.count(Sample.id))).one()
    by_instrument = dict(sess.exec(
        select(Sample.instrument, func.count(Sample.id))
        .group_by(Sample.instrument)
    ).all())
    by_energy = dict(sess.exec(
        select(Sample.energy, func.count(Sample.id))
        .group_by(Sample.energy)
    ).all())
    by_mood = dict(sess.exec(
        select(Sample.mood, func.count(Sample.id))
        .group_by(Sample.mood)
    ).all())
    print(json.dumps({
        'total': total,
        'by_instrument': by_instrument,
        'by_energy': by_energy,
        'by_mood': by_mood,
    }, indent=2))
"
```

**Step 2 — Display results:**

If `--json` flag: print raw JSON to stdout and stop.

Otherwise render a summary table:

```
SampleMind Library Statistics
══════════════════════════════════════════════
Total samples:    247

By Instrument:
  kick     42   ████████████░░░░░░░  17%
  hihat    38   ███████████░░░░░░░░  15%
  bass     31   █████████░░░░░░░░░░  13%
  snare    28   ████████░░░░░░░░░░░  11%
  loop     26   ████████░░░░░░░░░░░  11%
  pad      24   ███████░░░░░░░░░░░░  10%
  lead     20   ██████░░░░░░░░░░░░░   8%
  sfx      18   █████░░░░░░░░░░░░░░   7%
  unknown  20   ██████░░░░░░░░░░░░░   8%

By Energy:
  high     98   ████████████████░░░  40%
  mid      89   ██████████████░░░░░  36%
  low      60   █████████░░░░░░░░░░  24%

By Mood:
  neutral      55   ██████████░░░░░░░░  22%
  aggressive   48   █████████░░░░░░░░░  19%
  dark         42   ████████░░░░░░░░░░  17%
  chill        38   ███████░░░░░░░░░░░  15%
  euphoric     35   ███████░░░░░░░░░░░  14%
  melancholic  29   █████░░░░░░░░░░░░░  12%
══════════════════════════════════════════════
```

If `--full` flag, also show BPM range per instrument:

```bash
uv run python -c "
from samplemind.data.orm import init_orm, get_session
from samplemind.core.models.sample import Sample
from sqlmodel import select, func
init_orm()
with get_session() as sess:
    rows = sess.exec(
        select(Sample.instrument, func.min(Sample.bpm), func.max(Sample.bpm), func.avg(Sample.bpm))
        .group_by(Sample.instrument)
        .where(Sample.bpm.is_not(None))
    ).all()
    for inst, mn, mx, avg in rows:
        print(f'  {inst:<10} BPM: {mn:.0f}–{mx:.0f}  (avg {avg:.0f})')
"
```
