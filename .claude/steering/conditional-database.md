---
type: conditional
pattern: src/samplemind/data/**
---

## Database Rules — Active When Editing DB Files

### Always use the repository layer — never raw sqlite3

```python
# CORRECT
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.data.orm import init_orm, get_session

init_orm()  # idempotent — safe to call multiple times
sample = SampleRepository.upsert(SampleCreate(filename="kick.wav", path="/abs/path"))
results = SampleRepository.search(query="dark", energy="high", instrument="kick")
```

```python
# WRONG — never in CLI/web/API code
import sqlite3
conn = sqlite3.connect("library.db")
```

### Schema changes always need a migration

```bash
# After changing any SQLModel field or adding a column:
uv run alembic revision --autogenerate -m "add genre column to samples"
uv run alembic upgrade head
uv run alembic check  # CI catches drift — run this too
```

### WAL mode is automatic — do not set manually

`data/orm.py` applies `PRAGMA journal_mode=WAL`, `cache_size`, `synchronous`, `mmap_size`
via a SQLAlchemy event listener on every new connection. Never set these in application code.

### Session pattern

```python
# get_session() is a context manager — always use with:
from samplemind.data.orm import get_session
with get_session() as sess:
    result = sess.exec(select(Sample).where(Sample.id == sample_id)).first()
```

### Legacy `data/database.py` — do not import in new code

Still imported by a few legacy call sites (init_db). When you encounter it, note it but
do not add new imports from it. Phase 5 cleanup removes remaining call sites.
