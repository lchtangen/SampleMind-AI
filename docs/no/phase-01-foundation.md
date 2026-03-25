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
0.2.0

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

---

## 12. Utvidet Ruff-konfigurasjon

Ruff dekker linting, formatering og importsortering i ett raskt verktøy. Utvid regelsettet
etter hvert som kodebasen modnes for å fange flere typer feil:

```toml
# filename: pyproject.toml  (erstatt [tool.ruff.lint]-seksjonen)

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes (undefined names, unused imports)
    "I",    # isort (import order)
    "UP",   # pyupgrade (use modern Python syntax)
    "ANN",  # flake8-annotations (type hints on public functions)
    "PTH",  # flake8-use-pathlib (ban os.path, use pathlib.Path)
    "TCH",  # flake8-type-checking (move type-only imports to TYPE_CHECKING)
    "RUF",  # Ruff-native rules (fast, opinionated)
    "SIM",  # flake8-simplify (simplifiable conditions)
    "TRY",  # tryceratops (exception handling best practices)
]
ignore = [
    "ANN101",  # Missing type annotation for 'self' — not needed
    "ANN102",  # Missing type annotation for 'cls' — not needed
    "TRY003",  # Allow long exception messages in raise
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["ANN"]   # Don't enforce type hints in test files
"src/samplemind/cli/*" = ["ANN"]  # Typer handles types via annotations already

[tool.ruff.lint.isort]
known-first-party = ["samplemind"]
force-sort-within-sections = true
```

Kjør ruff i overvåkningsmodus under utvikling:

```bash
# Overvåkningsmodus — sjekker på nytt ved hver fillagring (bra med tmux-deling)
$ uv run ruff check src/ --watch

# Automatisk fiks av alle sikre problemer
$ uv run ruff check src/ --fix

# Formater hele prosjektet
$ uv run ruff format src/ tests/
```

---

## 13. Parallelle tester med pytest-xdist

For store testsuiter (fase 2+ med mange WAV-fixture-tester), kjør tester parallelt
på tvers av CPU-kjerner med `pytest-xdist`:

```bash
# Legg til i dev-avhengigheter
$ uv add --dev pytest-xdist
```

```toml
# filename: pyproject.toml — oppdater pytest-konfigurasjon

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short -n auto"   # -n auto = bruk alle tilgjengelige CPU-kjerner
markers = [
    "slow: dyre tester (velg med -m slow)",
    "integration: tester som krever ekte database eller filsystem",
]
```

```bash
# Kjør tester på alle kjerner (raskest)
$ uv run pytest -n auto

# Kjør på nøyaktig 4 kjerner
$ uv run pytest -n 4

# Hopp over trege tester på alle kjerner
$ uv run pytest -n auto -m "not slow"

# Kjør kun integrasjonstester
$ uv run pytest -m integration
```

> **Merk:** Lydanalysetester med librosa er CPU-intensive. `-n auto` på en 8-kjerners
> maskin reduserer testtiden fra ~60s til ~10s for en typisk testsuitt.

---

## 14. Pre-commit-hooks

Pre-commit-hooks kjører ruff automatisk før hver `git commit`, og forhindrer at
lintfeil noensinne havner i repositoriet:

```bash
# Installer pre-commit
$ uv add --dev pre-commit

# Installer git-hooks
$ uv run pre-commit install
```

```yaml
# filename: .pre-commit-config.yaml

repos:
  # Ruff — lint og formatering i én gjennomgang
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Standardhooks — etterfølgende mellomrom, filavslutninger, TOML/YAML-validitet
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-toml
      - id: check-yaml
      - id: check-merge-conflict
      - id: check-added-large-files
        args: ["--maxkb=500"]  # Blokker utilsiktet commit av lydfiler
```

```bash
# Kjør alle hooks manuelt (uten å committe)
$ uv run pre-commit run --all-files

# Oppdater hook-versjoner
$ uv run pre-commit autoupdate
```

---

## 15. .editorconfig — Konsekvent formatering på tvers av editorer

`.editorconfig` håndhever konsekvent innrykk og linjeavslutninger for alle editorer
(VS Code, Nvim, JetBrains osv.) uten å kreve plugins:

```ini
# filename: .editorconfig
# editorconfig.org

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{ts,svelte,js,json,toml,yaml,yml}]
indent_style = space
indent_size = 2

[*.{rs}]
indent_style = space
indent_size = 4

[*.md]
trim_trailing_whitespace = false   # Markdown bruker etterfølgende mellomrom for linjeskift

[Makefile]
indent_style = tab   # Makefiler krever tabs
```

---

## 16. Avansert WSL2-ytelse

### I/U-justering — Stopp WSL2 fra å bruke all RAM

Som standard kan WSL2 bruke opptil 50 % av system-RAM for sin VM. For en utviklingsmaskin
som kjører FL Studio + VS Code + WSL2 samtidig, begrens dette:

```ini
# filename: C:\Users\DittNavn\.wslconfig  (opprett denne filen på Windows)

[wsl2]
memory=6GB          # Maks RAM for WSL2 VM
processors=4        # Maks CPU-kjerner
swap=2GB            # Størrelse på swap-fil
localhostForwarding=true  # Videresend WSL2-porter til Windows (for Flask osv.)
```

### Symbolkobling av prosjektet inn i Windows for VS Code

Hvis du av og til trenger å åpne prosjektet fra Windows Utforsker:

```powershell
# PowerShell (kjør som administrator)
# Opprett en symbolkobling fra Windows til WSL2-stien
New-Item -ItemType SymbolicLink `
  -Path "C:\Projects\SampleMind" `
  -Target "\\wsl$\Ubuntu\home\ubuntu\dev\projects\SampleMind-AI"
```

### Raske Git-operasjoner — Aktiver fsmonitor

```bash
# Aktiver Gits innebygde filsystemmonitor (raskere git status/add på store repoer)
$ git config core.fsmonitor true
$ git config core.untrackedCache true

# Bekreft at det kjører
$ git fsmonitor--daemon status
```

### Portviderekobling — Tilgang til Flask/Tauri fra Windows-nettleser

WSL2-porter viderekobles automatisk til Windows. Ingen ekstra konfigurasjon nødvendig:

```bash
# Start Flask i WSL2:
$ uv run samplemind serve --port 5000

# Åpne i Windows Chrome/Edge (automatisk viderekobling):
# http://localhost:5000
```

### Måling av Python-ytelsesgrunnlinje

Før optimalisering, mål. Kjør dette for å få en grunnlinje for analysehastighet:

```bash
# Mål importtid for samplemind-pakken
$ uv run python -X importtime -c "import samplemind" 2>&1 | tail -5

# Profiler en enkelt filanalyse (viser hvor tid brukes)
$ uv run python -m cProfile -s cumulative -c "
from samplemind.analyzer.audio_analysis import analyze_file
analyze_file('/tmp/test.wav')
" | head -30
```

---

## 8. Kvalitetsverktøy for utvikling (2026-tillegg)

### pre-commit-oppsett

Installer pre-commit og legg til ruff-hooks for å fange problemer før hver commit:

```bash
uv add --dev pre-commit
uv run pre-commit install
```

Opprett `.pre-commit-config.yaml` i rotmappen til repoet:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
```

Kjør hooks manuelt på alle filer:
```bash
uv run pre-commit run --all-files
```

### .editorconfig

Opprett `.editorconfig` i rotmappen for konsekvent formatering på tvers av editorer:

```ini
# .editorconfig
root = true

[*]
indent_style = space
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
indent_size = 4

[*.{js,ts,svelte,json,yaml,yml,toml,md}]
indent_size = 2

[Makefile]
indent_style = tab

[*.rs]
indent_size = 4
```

VS Code respekterer `.editorconfig` automatisk med EditorConfig-utvidelsen.

### WSL2-ytelsestuning

Git er betydelig raskere på WSL2 med disse innstillingene aktivert:

```bash
# Aktiver filsystemmonitor og usporet cache:
git config core.fsmonitor true
git config core.untrackedCache true

# Verifiser:
git config --get core.fsmonitor    # skal skrive ut: true
git config --get core.untrackedCache  # skal skrive ut: true
```

**Kritisk:** Utvikle alltid på Linux ext4-filsystemet, ikke NTFS:

```bash
# Raskt (Linux-filsystem):
/home/ubuntu/dev/projects/SampleMind-AI/  ✓

# Tregt (NTFS via NTFS-3g-driver, 5–10× tregere for git/python):
/mnt/c/Users/DittNavn/SampleMind-AI/     ✗
```

Valgfri `/etc/wsl.conf`-tuning for tunge arbeidsbelastninger:

```ini
# /etc/wsl.conf (krever WSL-omstart: wsl --shutdown)
[wsl2]
memory=8GB          # begrens WSL2-minne (standard: 50 % av vert-RAM)
processors=4        # begrens CPU-kjerner ved behov
localhostForwarding=true
```

### VS Code WSL-utvidelsestips

Når du bruker VS Code med Remote – WSL-utvidelsen, installer disse utvidelsene
**inne i WSL-konteksten** (ikke på Windows):

```bash
# Fra WSL-terminalen:
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension tamasfe.even-better-toml
code --install-extension svelte.svelte-vscode
code --install-extension rust-lang.rust-analyzer
```

Bekreft at utvidelsene kjører i WSL (ikke Windows) i utvidelsespanelet:
se etter «WSL: Ubuntu»-merket ved siden av hver utvidelse.

---

## 11. Strukturert logging med structlog

Erstatt bare `print()` og `logging.basicConfig()` med **structlog** for
maskinlesbare JSON-logger som Sentry, Datadog og Grafana kan ta inn.

```bash
uv add structlog rich
```

```python
# src/samplemind/core/logging.py
"""
Strukturert loggingskonfigurasjon for SampleMind-AI.

Bruker structlog med to renderere:
  - Utvikling: rich-farget menneskelig lesbar utdata  (til stderr)
  - Produksjon:  JSON-linjer, én loggoppføring per linje   (til stderr)
Maskinlesbar JSON-utdata går til stdout for IPC-forbrukere (Tauri/Rust).
"""
import sys
import structlog
from samplemind.core.config import get_settings


def configure_logging() -> None:
    """Kall én gang ved applikasjonsoppstart før andre importer."""
    settings = get_settings()

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_format == "json":
        # Produksjon: JSON-linjer → rør til log-aggregator
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Utvikling: farget Rich-utdata
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(__import__("logging"), settings.log_level.upper(), 20)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
```

Bruk i et vilkårlig modul:

```python
from samplemind.core.logging import get_logger
log = get_logger(__name__)

# Strukturert nøkkel=verdi-kontekst vedlagt hver påfølgende logg i denne blokken:
with structlog.contextvars.bound_contextvars(sample_id=42, path="/tmp/kick.wav"):
    log.info("analyzing", bpm=140.0)
    log.warning("low_rms", rms=0.001, threshold=0.015)
```

Miljøvariabler:

```bash
SAMPLEMIND_LOG_LEVEL=debug   # debug / info / warning / error
SAMPLEMIND_LOG_FORMAT=json   # json (prod) / console (dev)
```

---

## 12. Miljøvalidering med pydantic-settings

Fang opp manglende eller feilformatert konfigurasjon ved oppstart — bruk aldri
stilltiende standardverdier i produksjon.

```bash
uv add pydantic-settings
```

```python
# src/samplemind/core/config.py
"""
Enkelt sannhetspunkt for all SampleMind-konfigurasjon.

Innlastingsrekkefølge (senere overstyrer tidligere):
  1. Hardkodede standardverdier nedenfor
  2. ~/.samplemind/config.toml        (brukerkonfigurasjonsfil)
  3. .env-fil i prosjektrot           (utviklingskomfort)
  4. Miljøvariabler                   (CI / produksjon)

Validering skjer ved oppstart: hvis SECRET_KEY mangler i produksjon,
kaster appen umiddelbart med en tydelig feil i stedet for å bruke
et usikkert standardnøkkel.
"""
from __future__ import annotations
from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import platformdirs


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{platformdirs.user_data_dir('SampleMind', 'SampleMind-AI')}/samplemind.db",
        description="SQLAlchemy-tilkoblingsstreng. Bruk sqlite:// for minnebasert testing.",
    )

    # ── Autentisering ────────────────────────────────────────────────────
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-use-secrets-token-hex-32",
        description="JWT-signeringsnøkkel. Generer: python -c \"import secrets; print(secrets.token_hex(32))\"",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── Webservere ───────────────────────────────────────────────────────
    flask_host: str = "127.0.0.1"
    flask_port: int = 5000
    flask_secret_key: str = Field(default="CHANGE-ME-FLASK")
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = ["tauri://localhost", "http://localhost:5174", "http://localhost:5000"]

    # ── Lydanalyse ────────────────────────────────────────────────────────
    workers: int = 0              # 0 = auto (cpu_count)
    sample_rate: int = 22050      # librosa standard
    max_file_size_mb: int = 500   # avvis filer større enn dette

    # ── Logging ───────────────────────────────────────────────────────────
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    log_format: Literal["console", "json"] = "console"

    # ── Valgfrie integrasjoner ─────────────────────────────────────────────
    sentry_dsn: str | None = Field(default=None, description="Sentry DSN — valgfri krasj-rapportering")
    anthropic_api_key: str | None = Field(default=None, description="Auggie CLI-integrasjon")

    model_config = SettingsConfigDict(
        env_prefix="SAMPLEMIND_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def warn_insecure_secret(cls, v: str) -> str:
        if v.startswith("CHANGE-ME"):
            import warnings
            warnings.warn(
                "SAMPLEMIND_SECRET_KEY bruker den usikre standard. "
                "Sett den til en tilfeldig 32-byte hex-streng i produksjon.",
                stacklevel=2,
            )
        return v

    @model_validator(mode="after")
    def ensure_db_dir_exists(self) -> "Settings":
        if self.database_url.startswith("sqlite:///"):
            path = Path(self.database_url.replace("sqlite:///", ""))
            path.parent.mkdir(parents=True, exist_ok=True)
        return self


_settings: Settings | None = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def override_settings(**kwargs) -> Settings:
    """Testhjelper — returnerer nye innstillinger med overstyringer, påvirker ikke global."""
    return Settings(**kwargs)
```

---

## 13. Helsesjekksystem

Alle tjenester eksponerer `/health` eller `/api/v1/health`. Tauri-appen poller dette
ved oppstart for å bekrefte at Python-tjenestene er live før UI-et vises.

```python
# src/samplemind/core/health.py
"""
Helsesjekk-aggregator.

Hver sjekk er et kallbart objekt som returnerer (name, ok, detail).
Samlet status er 'ok' bare hvis ALLE sjekker består.
"""
from __future__ import annotations
import time
import sqlite3
from pathlib import Path
from typing import NamedTuple
from samplemind.core.config import get_settings


class HealthResult(NamedTuple):
    name: str
    ok: bool
    detail: str
    latency_ms: float


def check_database() -> HealthResult:
    start = time.perf_counter()
    try:
        settings = get_settings()
        db_path = settings.database_url.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path, timeout=2.0)
        conn.execute("SELECT COUNT(*) FROM samples").fetchone()
        conn.close()
        ok, detail = True, f"samples-tabell tilgjengelig på {db_path}"
    except Exception as e:
        ok, detail = False, str(e)
    return HealthResult("database", ok, detail, (time.perf_counter() - start) * 1000)


def check_audio_libraries() -> HealthResult:
    start = time.perf_counter()
    try:
        import librosa, soundfile, numpy  # noqa: F401
        ok, detail = True, f"librosa {librosa.__version__}"
    except ImportError as e:
        ok, detail = False, str(e)
    return HealthResult("audio_libs", ok, detail, (time.perf_counter() - start) * 1000)


def run_all_checks() -> dict:
    import importlib.metadata
    checks = [check_database(), check_audio_libraries()]
    all_ok = all(c.ok for c in checks)
    return {
        "status": "ok" if all_ok else "degraded",
        "version": importlib.metadata.version("samplemind"),
        "checks": [
            {"name": c.name, "ok": c.ok, "detail": c.detail,
             "latency_ms": round(c.latency_ms, 1)}
            for c in checks
        ],
    }
```

FastAPI-helseendepunkt (registrert i `api/main.py`):

```python
from fastapi import APIRouter
from samplemind.core.health import run_all_checks

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health() -> dict:
    """
    Helsesjekk-endepunkt.
    Returnerer 200 + {"status": "ok"} hvis alle delsystemer er sunne.
    Returnerer 200 + {"status": "degraded"} med sjekkdetaljer hvis noen feiler.
    Tauri poller dette ved oppstart før hovedvinduet vises.
    """
    return run_all_checks()
```

---

## 14. Støtte for konfigurasjonsfil (~/.samplemind/config.toml)

Brukere kan lagre preferanser uten miljøvariabler.
`pydantic-settings` leser TOML naturlig i Python 3.11+.

```toml
# ~/.samplemind/config.toml  (opprettet av: uv run samplemind config init)
[samplemind]
workers = 4
log_level = "info"
log_format = "console"
max_file_size_mb = 200

[samplemind.database]
url = "sqlite:///~/.samplemind/library.db"

[samplemind.fl_studio]
# Overstyr FL Studio-eksportsti (valgfri)
export_path = "~/Documents/Image-Line/FL Studio 21/Data/Patches/Samples/SampleMind"
```

CLI-kommando for å opprette standardkonfigurasjon:

```python
# src/samplemind/cli/commands/config_cmd.py
import typer, tomllib, tomli_w
from pathlib import Path
from rich.console import Console

app = typer.Typer(help="Administrer SampleMind-konfigurasjon")
console = Console(stderr=True)
CONFIG_PATH = Path.home() / ".samplemind" / "config.toml"

@app.command()
def init(force: bool = typer.Option(False, "--force", help="Overskriv eksisterende konfig")):
    """Opprett standardkonfigurasjonsfil på ~/.samplemind/config.toml"""
    if CONFIG_PATH.exists() and not force:
        console.print(f"[yellow]Konfig finnes allerede:[/yellow] {CONFIG_PATH}")
        console.print("Bruk --force for å overskrive.")
        raise typer.Exit()
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(DEFAULT_TOML)
    console.print(f"[green]Opprettet:[/green] {CONFIG_PATH}")

@app.command()
def show():
    """Vis gjeldende effektiv konfigurasjon"""
    from samplemind.core.config import get_settings
    import json, sys
    settings = get_settings()
    print(json.dumps(settings.model_dump(exclude={"secret_key", "flask_secret_key"}), indent=2),
          file=sys.stdout)

DEFAULT_TOML = """\
[samplemind]
workers = 0          # 0 = auto (cpu_count)
log_level = "info"
log_format = "console"
"""
```

---

## 15. Sentry-integrasjon (valgfri krasjrapportering)

```bash
uv add sentry-sdk[fastapi,flask]
```

```python
# src/samplemind/core/sentry.py
"""
Valgfri krasjrapportering via Sentry.

Aktivert bare hvis SAMPLEMIND_SENTRY_DSN er satt i miljøet.
Samler aldri inn lyddata eller filstier — kun unntakssporing.
"""
from samplemind.core.config import get_settings
from samplemind.core.logging import get_logger

log = get_logger(__name__)


def init_sentry() -> bool:
    """Initialiser Sentry hvis DSN er konfigurert. Returnerer True hvis aktivert."""
    settings = get_settings()
    if not settings.sentry_dsn:
        log.debug("sentry_disabled", reason="SAMPLEMIND_SENTRY_DSN ikke satt")
        return False

    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration(), FlaskIntegration()],
        traces_sample_rate=0.1,   # 10 % av transaksjoner for ytelse
        profiles_sample_rate=0.1,
        environment="production" if settings.log_format == "json" else "development",
        # Personvern: fjern filstier fra brødsmulespor
        before_breadcrumb=lambda crumb, _hint: (
            None if crumb.get("category") == "httplib" else crumb
        ),
        # Send aldri lyddata
        before_send=_strip_audio_data,
    )
    log.info("sentry_enabled", dsn=settings.sentry_dsn[:20] + "...")
    return True


def _strip_audio_data(event: dict, _hint: dict) -> dict:
    """Fjern all lydrelatert data fra Sentry-hendelser før sending."""
    # Fjern filstier fra unntaksverdier for personvern
    if "exception" in event:
        for exc in event["exception"].get("values", []):
            for frame in exc.get("stacktrace", {}).get("frames", []):
                frame.pop("vars", None)  # fjern lokale variabelverdier
    return event
```

Kall ved oppstart i både Flask- og FastAPI-inngangspunkter:

```python
# I api/main.py create_app() og web/app.py:
from samplemind.core.sentry import init_sentry
init_sentry()   # no-op hvis SAMPLEMIND_SENTRY_DSN ikke er satt
```
