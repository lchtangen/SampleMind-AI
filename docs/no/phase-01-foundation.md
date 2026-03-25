# Fase 1 — Fundament og Prosjektstruktur

> Sett opp en moderne Python 3.13-prosjektstruktur med `uv`, `pyproject.toml` og en ryddig
> mappe-layout som skalerer gjennom alle 10 faser.

---

## Forutsetninger

- Git installert og konfigurert
- WSL2 (Windows Subsystem for Linux 2) på Windows, eller native terminal på macOS
- VS Code med WSL-utvidelsen (Remote – WSL) på Windows
- Ingen eksisterende Python-miljø kreves — `uv` håndterer alt

---

## Mål etter denne fasen

```
SampleMind-AI/
├── pyproject.toml          ← Erstatter requirements.txt
├── .python-version         ← Pinner Python 3.13
├── uv.lock                 ← Deterministisk avhengighetslås
├── src/
│   └── samplemind/         ← Riktig pakke-layout (src-layout)
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli/
│       ├── analyzer/
│       ├── data/
│       └── web/
├── tests/
│   └── conftest.py
├── scripts/
│   └── setup-dev.sh
└── app/                    ← Tauri desktop-app (uendret i denne fasen)
```

Du kan kjøre `samplemind --help` direkte etter `uv sync` uten å aktivere et virtuelt miljø manuelt.

---

## 1. Hvorfor bytte fra pip/venv til uv?

`uv` (fra Astral) er en Rust-basert pakkebehandler som erstatter `pip`, `pip-tools` og `venv` i ett
enkelt binærverktøy. Det er 10–100× raskere enn pip.

```
pip + venv (gammelt)          uv (nytt)
─────────────────────         ──────────────────────────────
python -m venv .venv          (automatisk)
source .venv/bin/activate     (ikke nødvendig)
pip install -r requirements   uv sync
pip install pakke             uv add pakke
pip freeze > requirements     (uv.lock håndteres auto)
```

Viktige fordeler:
- `uv.lock` er deterministisk — alle bidragsytere får eksakt samme versjoner
- Fjerner kun de pakkene du faktisk ba om ved `uv remove` (ingen orphans)
- Ett enkelt binærfilverktøy — ingen Python-installasjoner nødvendig for å sette opp miljøet

---

## 2. Installer uv

### WSL2 / Linux / macOS

```bash
$ curl -LsSf https://astral.sh/uv/install.sh | sh

# Legg til i PATH (legg til i ~/.bashrc eller ~/.zshrc):
$ export PATH="$HOME/.cargo/bin:$PATH"

# Bekreft installasjon:
$ uv --version
uv 0.5.x
```

### Windows (PowerShell, uten WSL2)

```powershell
$ powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **Anbefaling:** Bruk WSL2 for utvikling på Windows. Da er kommandoene identiske med macOS.

---

## 3. pyproject.toml — Prosjektets konfigurasjonssentrum

`pyproject.toml` erstatter `requirements.txt`, og samler all konfigurasjon (avhengigheter, linting,
testing) på ett sted. Dette er PEP 517/518/621-standarden for moderne Python-prosjekter.

```toml
# filename: pyproject.toml

[project]
name = "samplemind"
version = "0.1.0"
description = "AI-drevet sample-bibliotek og DAW companion for FL Studio"
authors = [{ name = "lchtangen" }]
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.13"

# ─── Kjøretidsavhengigheter (erstatter requirements.txt) ─────────────────────
dependencies = [
    # Audio-analyse
    "librosa==0.11.0",
    "numpy>=2.2",
    "scipy>=1.15",
    "soundfile>=0.13",
    "soxr>=0.5",

    # Machine learning
    "scikit-learn>=1.6",
    "numba>=0.61",

    # Webtjener
    "flask>=3.1",
    "jinja2>=3.1",

    # Database ORM (oppgradert fra rå sqlite3 i Fase 3)
    "sqlmodel>=0.0.21",

    # CLI (oppgradert fra argparse i Fase 4)
    "typer>=0.12",
    "rich>=13",

    # Diverse
    "requests>=2.32",
    "platformdirs>=4.3",
]

# ─── Valgfrie avhengigheter (installeres med: uv sync --extra dev) ────────────
[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov",
    "ruff>=0.4",
]

# ─── CLI-inngangspunkt ────────────────────────────────────────────────────────
# Etter `uv sync` kan du kjøre `samplemind` direkte i terminalen
[project.scripts]
samplemind = "samplemind.cli.app:app"

# ─── Byggkonfigurasjon ────────────────────────────────────────────────────────
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Fortell hatchling at kildekoden ligger i src/
[tool.hatch.build.targets.wheel]
packages = ["src/samplemind"]

# ─── pytest-konfigurasjon ─────────────────────────────────────────────────────
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
# Marker: kjør bare raske tester med: pytest -m "not slow"
markers = ["slow: tidkrevende tester (velg ut med -m slow)"]

# ─── Ruff linting-konfigurasjon ───────────────────────────────────────────────
[tool.ruff]
src = ["src"]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]   # pycodestyle + pyflakes + isort + pyupgrade
```

---

## 4. Ny mappestruktur (src-layout)

### Hvorfor src-layout?

Med flat layout (`src/analyzer/`) kan Python importere direkte fra kildemappen, noe som skjuler
installasjonsfeil. Med `src/samplemind/` vil du få `ModuleNotFoundError` hvis pakken ikke er riktig
installert — det oppdager problemer tidlig.

```
# GAMMELT (flat layout — kan gi skjulte importfeil)
SampleMind-AI/
└── src/
    ├── analyzer/
    │   └── audio_analysis.py
    ├── cli/
    └── main.py

# NYTT (src-layout — standard for distribuerbare pakker)
SampleMind-AI/
└── src/
    └── samplemind/           ← Alt samlet i én pakke
        ├── __init__.py
        ├── __main__.py       ← Muliggjør: python -m samplemind
        ├── cli/
        │   ├── __init__.py
        │   ├── app.py        ← Typer CLI (Fase 4)
        │   └── commands/
        ├── analyzer/
        │   ├── __init__.py
        │   ├── audio_analysis.py
        │   └── classifier.py
        ├── data/
        │   ├── __init__.py
        │   └── database.py   → models.py + repository.py (Fase 3)
        ├── web/
        │   ├── __init__.py
        │   └── app.py
        ├── integrations/     ← FL Studio (Fase 7)
        ├── packs/            ← Sample-pakker (Fase 9)
        └── sidecar/          ← Plugin-server (Fase 8)
```

---

## 5. Pakkens __init__.py og __main__.py

```python
# filename: src/samplemind/__init__.py

# Versjonsnummer — brukes av CLI og Tauri for å vise versjon
__version__ = "0.1.0"
```

```python
# filename: src/samplemind/__main__.py

# Gjør det mulig å kjøre: python -m samplemind [kommando]
# Dette er nyttig i Tauri-integrering der vi kaller Python som subprocess
from samplemind.cli.app import app

if __name__ == "__main__":
    app()
```

---

## 6. .python-version — Pin Python-versjon

```
# filename: .python-version
3.13
```

`uv` leser denne filen automatisk og bruker Python 3.13 for alle operasjoner i prosjektet.

---

## 7. uv-kommandoer du bruker daglig

```bash
# Første gangs oppsett (installer alle avhengigheter)
$ uv sync --extra dev

# Legg til en ny pakke (oppdaterer pyproject.toml og uv.lock)
$ uv add pakkenavn

# Legg til en dev-avhengighet
$ uv add --dev pakkenavn

# Fjern en pakke
$ uv remove pakkenavn

# Kjør en kommando i prosjektets miljø (uten å aktivere manuelt)
$ uv run python -m samplemind analyze ~/Music/samples/

# Kjør tester
$ uv run pytest

# Kjør linting
$ uv run ruff check src/
```

---

## 8. VS Code-oppsett for WSL2

Legg til / oppdater `.vscode/settings.json`:

```json
// filename: .vscode/settings.json
{
    // ── Python ──────────────────────────────────────────────────────────
    // Pek VS Code til uv sitt virtuelle miljø
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.analysis.extraPaths": ["${workspaceFolder}/src"],

    // ── Ruff linting (erstatter pylint/flake8) ──────────────────────────
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },

    // ── Rust (for Tauri-utvikling) ───────────────────────────────────────
    "rust-analyzer.linkedProjects": ["app/src-tauri/Cargo.toml"],

    // ── WSL2-spesifikt: bruk LF linjeskift ──────────────────────────────
    "files.eol": "\n",

    // ── Fil-ekskludering (ikke vis i filutforsker) ───────────────────────
    "files.exclude": {
        "**/__pycache__": true,
        "**/.venv": true,
        "**/node_modules": true,
        "**/target": true
    }
}
```

---

## 9. Bootstrap-skript for nye bidragsytere

```bash
#!/usr/bin/env bash
# filename: scripts/setup-dev.sh
# Kjør: bash scripts/setup-dev.sh
# Setter opp hele utviklingsmiljøet fra bunnen av.

set -e  # Avslutt ved feil

echo "=== SampleMind AI — Utviklingsmiljø-oppsett ==="

# ── 1. Sjekk at uv er installert ──────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
    echo "Installerer uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "uv versjon: $(uv --version)"

# ── 2. Installer Python + avhengigheter ───────────────────────────────────────
echo "Installerer Python 3.13 og avhengigheter..."
uv sync --extra dev

# ── 3. Bekreft installasjon ───────────────────────────────────────────────────
echo "Bekrefter installasjon..."
uv run python -c "import samplemind; print(f'samplemind {samplemind.__version__} OK')"
uv run python -c "import librosa; print(f'librosa {librosa.__version__} OK')"

# ── 4. Kjør tester ────────────────────────────────────────────────────────────
echo "Kjører tester..."
uv run pytest tests/ -x --tb=short

echo ""
echo "=== Oppsett fullført! ==="
echo "Kjør: uv run samplemind --help"
```

---

## 10. WSL2-spesifikke hensyn

### Filsystemytelse

WSL2 har to filsystemer:
- `/home/bruker/` (Linux ext4) — **rask**, bruk dette for kildekoden
- `/mnt/c/` (Windows NTFS, montert) — **treg** for Python/Git

```bash
# ANBEFALT: Jobb i Linux-filsystemet
$ cd ~/dev/projects/SampleMind-AI

# UNNGÅ: Jobb ikke i Windows-mappen (tregt!)
# cd /mnt/c/Users/BrukernAvn/Projects/SampleMind-AI
```

### Linjeskift

Git er konfigurert til å bruke LF (`\n`) — macOS-kompatibelt:

```bash
# Sett globalt for WSL2:
$ git config --global core.autocrlf false
$ git config --global core.eol lf
```

### macOS-utvikling fra WSL2

Du utvikler på WSL2 (Linux), men produktet skal kjøre på macOS. Det betyr:
- Koden (Python, Rust) er plattformuavhengig — fungerer på begge
- Tauri-bygging for macOS **krever** en macOS-maskin eller GitHub Actions med `macos-latest`
- Filstier: bruk alltid `pathlib.Path` i Python, aldri hardkodede skråstreker

```python
# Riktig — fungerer på alle plattformer
from pathlib import Path
db_path = Path.home() / ".samplemind" / "library.db"

# Feil — krasjer på Windows
db_path = os.path.expanduser("~") + "/.samplemind/library.db"
```

---

## 11. Migrering fra eksisterende oppsett

Steg-for-steg fra det gamle `requirements.txt`-oppsettet:

```bash
# Steg 1: Opprett pyproject.toml (bruk innholdet fra seksjon 3 over)

# Steg 2: Slett det gamle virtuelle miljøet
$ rm -rf .venv/

# Steg 3: Opprett .python-version
$ echo "3.13" > .python-version

# Steg 4: Installer med uv
$ uv sync --extra dev

# Steg 5: Bekreft at gamle CLI-kommandoer fortsatt fungerer
$ uv run python src/main.py --help

# Steg 6: Flytt kildekoden til src/samplemind/ (gjøres gradvis i Fase 2-4)
# src/analyzer/     → src/samplemind/analyzer/
# src/cli/          → src/samplemind/cli/
# src/data/         → src/samplemind/data/
# src/web/          → src/samplemind/web/
# src/main.py       → src/samplemind/cli/app.py (Fase 4)
```

---

## Migrasjonsnotater

- `requirements.txt` beholdes midlertidig under migrasjon, men slettes når `pyproject.toml` er komplett
- Alle importstier (`from analyzer.audio_analysis import`) oppdateres til `from samplemind.analyzer.audio_analysis import` i Fase 2–4
- `src/main.py` erstattes av `src/samplemind/cli/app.py` (Typer) i Fase 4

---

## Testsjekkliste

```bash
# Bekreft at uv er installert og fungerer
$ uv --version

# Bekreft Python 3.13
$ uv run python --version
Python 3.13.x

# Bekreft at samplemind-pakken importeres korrekt
$ uv run python -c "import samplemind; print(samplemind.__version__)"
0.1.0

# Bekreft at alle avhengigheter er installert
$ uv run python -c "import librosa, flask, sqlmodel, typer; print('Alle OK')"

# Kjør tester (ingen ennå, men sjekk at pytest fungerer)
$ uv run pytest tests/ -v
```

---

## Feilsøking

**Feil: `uv: command not found` etter installasjon**
```bash
# Legg til uv i PATH manuelt:
$ export PATH="$HOME/.local/bin:$PATH"
# Legg til i ~/.bashrc for permanent effekt
```

**Feil: `ModuleNotFoundError: No module named 'samplemind'`**
```bash
# Installer pakken i redigerbart modus:
$ uv pip install -e .
# Eller synkroniser på nytt:
$ uv sync
```

**Feil: Python 3.13 ikke tilgjengelig**
```bash
# uv kan installere Python for deg:
$ uv python install 3.13
$ uv sync
```

**Feil: Treg ytelse i WSL2**
```bash
# Bekreft at du arbeider i Linux-filsystemet, ikke /mnt/c/:
$ pwd
/home/dittbrukernavn/dev/projects/SampleMind-AI  # ← Riktig
# /mnt/c/Users/...  ← Feil, flytt prosjektet
```
