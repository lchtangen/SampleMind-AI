# Fase 3 — Database og Datalag

> Oppgrader det rå `sqlite3`-laget i `database.py` til **SQLModel** + SQLAlchemy 2.0 med
> Alembic-migrasjoner, type-sikre modeller og et Repository-mønster.

---

## Forutsetninger

- Fase 1 fullført (uv + pyproject.toml)
- `sqlmodel` og `alembic` lagt til i `pyproject.toml`
- Grunnleggende SQL-kunnskap er nyttig

---

## Mål etter denne fasen

- `src/samplemind/models.py` med `Sample` SQLModel-klasse
- `src/samplemind/repository.py` med `SampleRepository`-klasse
- Alembic satt opp for skjema-migrasjoner
- In-memory SQLite i pytest for isolerte tester
- Eksisterende `database.py` kan slettes

---

## 1. Hvorfor SQLModel?

SQLModel er bygget på toppen av SQLAlchemy 2.0 og Pydantic. Det lar deg definere
databasemodeller og valideringsmodeller i én og samme klasse:

```
Raw sqlite3 (gammelt)          SQLModel (nytt)
─────────────────────          ────────────────────────────────
Ingen typer — alt er str/None  Typer: Optional[float], str, ...
SQL-strenger manuelt           select(Sample).where(...)
Ingen validering               Pydantic validerer automatisk
_migrate() hack                Alembic autogenererer migrasjoner
row["bpm"] (sqlite3.Row)       sample.bpm (attributt)
```

Hierarki:
```
SQLModel
  ├── arver fra SQLAlchemy (database-operasjoner)
  └── arver fra Pydantic (validering og serialisering)
```

---

## 2. Sample-modellen

```python
# filename: src/samplemind/models.py

from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Sample(SQLModel, table=True):
    """
    Representerer én sample i biblioteket.

    table=True: SQLModel oppretter en database-tabell for denne klassen.
    Uten table=True brukes klassen kun for validering (Pydantic-modus).
    """

    # Primærnøkkel — auto-inkrementert av SQLite
    id: Optional[int] = Field(default=None, primary_key=True)

    # Filinfo — path er unik (samme fil kan ikke importeres to ganger)
    filename: str = Field(index=True)                    # Indeksert for rask søk
    path: str = Field(unique=True)                       # Unik constraint

    # Auto-detekterte felt (fra analyzer)
    bpm: Optional[float] = Field(default=None)           # None = ikke analysert ennå
    key: Optional[str] = Field(default=None)             # "C maj", "F# min", osv.
    mood: Optional[str] = Field(default=None)            # "dark", "chill", osv.
    energy: Optional[str] = Field(default=None)          # "low", "mid", "high"
    instrument: Optional[str] = Field(default=None)      # "kick", "snare", osv.

    # Manuelt taggede felt (fra bruker)
    genre: Optional[str] = Field(default=None)           # "trap", "lofi", osv.
    tags: Optional[str] = Field(default=None)            # Kommaseparerte fri-tags

    # Tidsstempel — settes automatisk ved innsetting
    imported_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class SampleCreate(SQLModel):
    """
    Pydantic-modell for å opprette en ny sample (uten id og imported_at).
    Brukes i API-kall og CLI for å validere input før lagring.
    """
    filename: str
    path: str
    bpm: Optional[float] = None
    key: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[str] = None
    instrument: Optional[str] = None


class SampleUpdate(SQLModel):
    """
    Pydantic-modell for å oppdatere tags (alle felt valgfrie).
    Brukes av tagger-kommandoen og web-API.
    """
    genre: Optional[str] = None
    mood: Optional[str] = None
    energy: Optional[str] = None
    tags: Optional[str] = None
```

---

## 3. Database-tilkobling og engine

```python
# filename: src/samplemind/data/db.py

from pathlib import Path
from sqlmodel import create_engine, SQLModel, Session
import platformdirs


def _get_db_path() -> Path:
    """
    Finn riktig database-sti basert på plattform.

    macOS:   ~/Library/Application Support/samplemind/library.db
    Linux:   ~/.local/share/samplemind/library.db
    Windows: C:\\Users\\Bruker\\AppData\\Local\\samplemind\\library.db

    platformdirs håndterer alt dette automatisk etter XDG-standardene.
    """
    data_dir = Path(platformdirs.user_data_dir("samplemind", "samplemind"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "library.db"


# Globalt engine-objekt — opprettes én gang ved import
# connect_args={"check_same_thread": False} tillater bruk fra Flask-tråder
engine = create_engine(
    f"sqlite:///{_get_db_path()}",
    connect_args={"check_same_thread": False},
    echo=False,  # Sett til True for SQL-debug-logging
)


def init_db():
    """
    Opprett alle tabeller hvis de ikke finnes.
    Kall denne ved app-oppstart (Flask og CLI).
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """
    Kontekstbehandler for database-sesjoner.

    Bruk:
        with get_session() as session:
            sample = session.get(Sample, 1)
    """
    return Session(engine)
```

---

## 4. Repository-mønsteret

Repository-mønsteret pakker inn alle database-operasjoner i én klasse.
Dette gjør det enkelt å bytte ut databasen i tester (f.eks. til in-memory SQLite).

```python
# filename: src/samplemind/data/repository.py

from typing import Optional
from sqlmodel import Session, select
from samplemind.models import Sample, SampleCreate, SampleUpdate
from samplemind.data.db import engine, get_session


class SampleRepository:
    """
    All databasetilgang for samples går gjennom denne klassen.
    Ingen SQL-strenger utenfor dette filen.
    """

    def __init__(self, session: Optional[Session] = None):
        # Tillat injeksjon av en test-session (in-memory SQLite)
        self._session = session

    def _get_session(self) -> Session:
        return self._session or get_session()

    # ── Opprett / Upsert ──────────────────────────────────────────────────────

    def upsert(self, data: SampleCreate) -> Sample:
        """
        Sett inn en ny sample, eller oppdater auto-detekterte felt hvis stien
        allerede finnes. Manuelt taggede felt (genre, tags) berøres ikke.

        Erstatter: database.py::save_sample() med rå INSERT ... ON CONFLICT
        """
        with self._get_session() as session:
            # Sjekk om stien allerede eksisterer
            existing = session.exec(
                select(Sample).where(Sample.path == data.path)
            ).first()

            if existing:
                # Oppdater kun auto-detekterte felt — behold manuelle tags
                existing.bpm = data.bpm
                existing.key = data.key
                existing.mood = data.mood
                existing.energy = data.energy
                existing.instrument = data.instrument
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                # Sett inn ny sample
                sample = Sample.model_validate(data)
                session.add(sample)
                session.commit()
                session.refresh(sample)
                return sample

    # ── Oppdater tags ─────────────────────────────────────────────────────────

    def tag(self, path: str, update: SampleUpdate) -> Optional[Sample]:
        """
        Oppdater manuelle tags for en sample.
        Erstatter: database.py::tag_sample()
        """
        with self._get_session() as session:
            sample = session.exec(
                select(Sample).where(Sample.path == path)
            ).first()

            if not sample:
                return None

            # Oppdater kun felt som eksplisitt er gitt (ikke None)
            update_data = update.model_dump(exclude_none=True)
            for field, value in update_data.items():
                setattr(sample, field, value)

            session.add(sample)
            session.commit()
            session.refresh(sample)
            return sample

    # ── Søk ───────────────────────────────────────────────────────────────────

    def search(
        self,
        query: Optional[str] = None,
        bpm_min: Optional[float] = None,
        bpm_max: Optional[float] = None,
        key: Optional[str] = None,
        genre: Optional[str] = None,
        energy: Optional[str] = None,
        instrument: Optional[str] = None,
    ) -> list[Sample]:
        """
        Søk med kombinerte filtre. Alle filtre er valgfrie.
        Erstatter: database.py::search_samples() med rå SQL-streng.
        """
        with self._get_session() as session:
            stmt = select(Sample)

            # Fritekst-søk i filnavn og tags
            if query:
                stmt = stmt.where(
                    Sample.filename.contains(query) | Sample.tags.contains(query)
                )

            # Numeriske filter
            if bpm_min is not None:
                stmt = stmt.where(Sample.bpm >= bpm_min)
            if bpm_max is not None:
                stmt = stmt.where(Sample.bpm <= bpm_max)

            # Tekst-filtre (LIKE-søk for fleksibilitet)
            if key:
                stmt = stmt.where(Sample.key.contains(key))
            if genre:
                stmt = stmt.where(Sample.genre.contains(genre))
            if energy:
                stmt = stmt.where(Sample.energy == energy)
            if instrument:
                stmt = stmt.where(Sample.instrument.contains(instrument))

            stmt = stmt.order_by(Sample.imported_at.desc())
            return session.exec(stmt).all()

    def get_by_name(self, name: str) -> Optional[Sample]:
        """Finn sample ved delvis filnavn-match. Erstatter: get_sample_by_name()."""
        with self._get_session() as session:
            return session.exec(
                select(Sample).where(Sample.filename.contains(name)).limit(1)
            ).first()

    def count(self) -> int:
        """Antall samples i biblioteket."""
        with self._get_session() as session:
            return len(session.exec(select(Sample)).all())

    def get_all(self) -> list[Sample]:
        """Hent alle samples — brukt av export-funksjonalitet."""
        return self.search()
```

---

## 5. Side om side — gammelt vs nytt

| Operasjon | Gammelt (`database.py`) | Nytt (`repository.py`) |
|-----------|------------------------|----------------------|
| Lagre sample | `conn.execute("INSERT INTO samples ...")` | `repo.upsert(SampleCreate(...))` |
| Oppdater tags | `f"UPDATE samples SET {', '.join(fields)}"` | `repo.tag(path, SampleUpdate(...))` |
| Søk | `sql += " AND bpm >= ?"` streng-bygging | `stmt = stmt.where(Sample.bpm >= bpm_min)` |
| Finn etter navn | `"SELECT * FROM samples WHERE filename LIKE ?"` | `repo.get_by_name("kick")` |
| Antall | `"SELECT COUNT(*) FROM samples"` | `repo.count()` |
| Type-sikkerhet | Ingen — alt er `sqlite3.Row` | Full — `sample.bpm: Optional[float]` |
| Autocompletion | Ingen i IDE | Fungerer med `sample.` i VS Code |

---

## 6. Alembic — skjema-migrasjoner

Alembic holder styr på endringer i databaseskjemaet over tid, i stedet for den nåværende
`_migrate()`-hacken som kan svikte ved komplekse endringer.

### Oppsett

```bash
# Installer Alembic (legg til i pyproject.toml under dependencies)
$ uv add alembic

# Initialiser Alembic i prosjektet
$ uv run alembic init alembic
```

```ini
# filename: alembic.ini (oppdater sqlalchemy.url)
[alembic]
script_location = alembic

# Pek til SQLite-databasen (samme sti som i db.py)
# %(here)s = mappen der alembic.ini befinner seg
sqlalchemy.url = sqlite:///%(here)s/../data/dev.db
```

```python
# filename: alembic/env.py (oppdater target_metadata)

from samplemind.models import Sample      # Importer alle modeller
from sqlmodel import SQLModel

# Fortell Alembic hvilke tabeller som skal holdes oppdatert
target_metadata = SQLModel.metadata
```

### Første migrasjon

```bash
# Generer automatisk migrasjonsfil fra modell-definisjonene
$ uv run alembic revision --autogenerate -m "initial_schema"

# Kjør migrasjonen (oppretter tabellen)
$ uv run alembic upgrade head

# Se historikk
$ uv run alembic history
```

Generert migrasjonsfil (eksempel):

```python
# filename: alembic/versions/0001_initial_schema.py

"""initial_schema

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        "sample",                              # SQLModel bruker klassenavn i lowercase
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("filename", sa.String, nullable=False, index=True),
        sa.Column("path", sa.String, nullable=False, unique=True),
        sa.Column("bpm", sa.Float, nullable=True),
        sa.Column("key", sa.String, nullable=True),
        sa.Column("mood", sa.String, nullable=True),
        sa.Column("energy", sa.String, nullable=True),
        sa.Column("instrument", sa.String, nullable=True),
        sa.Column("genre", sa.String, nullable=True),
        sa.Column("tags", sa.String, nullable=True),
        sa.Column("imported_at", sa.DateTime, nullable=True),
    )

def downgrade():
    op.drop_table("sample")
```

---

## 7. Testing med in-memory SQLite

```python
# filename: tests/test_repository.py

import pytest
from sqlmodel import create_engine, SQLModel, Session
from samplemind.models import Sample, SampleCreate, SampleUpdate
from samplemind.data.repository import SampleRepository


@pytest.fixture
def in_memory_session():
    """
    Lager en isolert in-memory SQLite-database for hver test.
    Ingen data lekker mellom tester.
    """
    # sqlite:// (uten filsti) = in-memory database
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session  # Lever session til testen


@pytest.fixture
def repo(in_memory_session):
    """SampleRepository koblet til in-memory testdatabase."""
    return SampleRepository(session=in_memory_session)


class TestUpsert:
    def test_insert_new_sample(self, repo):
        """Innsetting av ny sample skal lykkes og returnere Sample-objekt."""
        data = SampleCreate(filename="kick.wav", path="/samples/kick.wav", bpm=128.0)
        sample = repo.upsert(data)

        assert sample.id is not None
        assert sample.filename == "kick.wav"
        assert sample.bpm == 128.0

    def test_upsert_same_path_updates_bpm(self, repo):
        """Re-import av samme sti skal oppdatere BPM, ikke lage duplikat."""
        repo.upsert(SampleCreate(filename="kick.wav", path="/samples/kick.wav", bpm=128.0))
        repo.upsert(SampleCreate(filename="kick.wav", path="/samples/kick.wav", bpm=140.0))

        # Skal fortsatt bare være én sample
        assert repo.count() == 1
        # BPM skal være oppdatert
        sample = repo.get_by_name("kick")
        assert sample.bpm == 140.0


class TestTag:
    def test_tag_updates_genre(self, repo):
        """Tagging skal oppdatere genre uten å endre andre felt."""
        repo.upsert(SampleCreate(filename="bass.wav", path="/s/bass.wav", mood="dark"))

        sample = repo.get_by_name("bass")
        repo.tag(sample.path, SampleUpdate(genre="trap"))

        updated = repo.get_by_name("bass")
        assert updated.genre == "trap"
        assert updated.mood == "dark"   # Uendret


class TestSearch:
    def test_search_by_energy(self, repo):
        """Søk etter energi-filter skal returnere kun matchende samples."""
        repo.upsert(SampleCreate(filename="kick.wav", path="/s/kick.wav", energy="high"))
        repo.upsert(SampleCreate(filename="pad.wav", path="/s/pad.wav", energy="low"))

        results = repo.search(energy="high")
        assert len(results) == 1
        assert results[0].filename == "kick.wav"

    def test_search_bpm_range(self, repo):
        """BPM-range-filter skal returnere samples innenfor området."""
        repo.upsert(SampleCreate(filename="a.wav", path="/s/a.wav", bpm=120.0))
        repo.upsert(SampleCreate(filename="b.wav", path="/s/b.wav", bpm=140.0))
        repo.upsert(SampleCreate(filename="c.wav", path="/s/c.wav", bpm=160.0))

        results = repo.search(bpm_min=130.0, bpm_max=150.0)
        assert len(results) == 1
        assert results[0].filename == "b.wav"
```

---

## 8. DB-sti per plattform

```python
# filename: src/samplemind/data/db.py

# platformdirs gir plattformkorrekte stier automatisk:
# macOS:   ~/Library/Application Support/samplemind/library.db
# Linux:   ~/.local/share/samplemind/library.db
# Windows: C:\Users\Bruker\AppData\Local\samplemind\samplemind\library.db

import platformdirs
data_dir = Path(platformdirs.user_data_dir("samplemind", "samplemind"))
```

---

## Migrasjonsnotater

- `src/data/database.py` kan slettes etter at `repository.py` er implementert og testet
- Eksisterende `~/.samplemind/library.db` kan beholdes — Alembic kan migrere den
- Alle importstier som brukte `from data.database import ...` oppdateres til
  `from samplemind.data.repository import SampleRepository`

---

## Testsjekkliste

```bash
# Kjør repository-tester
$ uv run pytest tests/test_repository.py -v

# Bekreft at Alembic kan koble til
$ uv run alembic current

# Kjør alle migrasjoner
$ uv run alembic upgrade head

# Sjekk at tabellen eksisterer
$ python -c "
from samplemind.data.db import engine
from sqlalchemy import inspect
print(inspect(engine).get_table_names())
"
```

---

## Feilsøking

**Feil: `Table 'sample' already exists`**
```bash
# Alembic prøver å opprette en tabell som allerede finnes
# Marker eksisterende migrasjon som kjørt uten å kjøre den:
$ uv run alembic stamp head
```

**Feil: `ImportError: cannot import name 'Sample'`**
```bash
# Sjekk at models.py ligger i riktig mappe:
$ ls src/samplemind/models.py
# og at pyproject.toml peker til src/
```

**Feil: Mister data ved re-import**
```
SampleCreate har ikke genre/tags-felt — disse endres aldri av upsert().
Sjekk at du bruker SampleUpdate for manuell tagging, ikke SampleCreate.
```
