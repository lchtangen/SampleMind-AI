#!/usr/bin/env bash
set -e

echo "=== SampleMind AI — Utviklingsmiljo-oppsett ==="

if ! command -v uv >/dev/null 2>&1; then
    echo "Installerer uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "uv versjon: $(uv --version)"

echo "Installerer Python 3.13 og avhengigheter..."
uv sync --extra dev

echo "Bekrefter installasjon..."
uv run python -c "import samplemind; print(f'samplemind {samplemind.__version__} OK')"
uv run python -c "import librosa; print(f'librosa {librosa.__version__} OK')"

echo "Kjorer tester..."
set +e
uv run pytest tests/ -x --tb=short
code=$?
set -e
if [ "$code" -eq 5 ]; then
    echo "Ingen tester funnet enda (pytest exit code 5) - fortsetter."
elif [ "$code" -ne 0 ]; then
    exit "$code"
fi

echo ""
echo "=== Oppsett fullfort ==="
echo "Kjor: uv run samplemind --help"
