# Developer Guide

## Project Structure
- `src/`: Main Python source code
- `frontend/`: Web and Electron apps
- `docs/`: Documentation
- `tests/`: Unit, integration, and e2e tests

## Local Development
```bash
git clone https://github.com/samplemind/samplemind-ai-v6.git
cd samplemind-ai-v6
python3 -m venv .venv
source .venv/bin/activate
make setup
make dev
```

## Docker Development
```bash
docker-compose up -d
```

## Running Tests
```bash
pytest tests/
```

## Code Style
- Python: [Black](https://black.readthedocs.io/), [Ruff](https://docs.astral.sh/ruff/)
- JS/TS: [Prettier](https://prettier.io/), [ESLint](https://eslint.org/)

## Adding API Endpoints
- Edit `src/samplemind/interfaces/api/ollama_api.py`
- Add Pydantic models for requests/responses
- Use FastAPI decorators
- Test with Swagger UI

## Contributing
See [CONTRIBUTING.md](../../CONTRIBUTING.md) 