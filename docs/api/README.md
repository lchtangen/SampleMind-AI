# API Reference

## Overview
Samplemind AI exposes a REST API for LLMs, code generation, and embeddings.

- **Swagger UI:** http://localhost:8000/docs
- **Redoc:** http://localhost:8000/redoc

## Endpoints

### Health
- `GET /api/health`
  - Returns: `{ "status": "ok" }`

### LLM
- `POST /api/llm`
  - Request: `{ "prompt": "..." }`
  - Response: `{ "response": "..." }`

- `POST /api/code`
  - Request: `{ "prompt": "..." }`
  - Response: `{ "response": "..." }`

### Embedding
- `POST /api/embed`
  - Request: `{ "prompt": "..." }`
  - Response: `{ "embedding": [...] }`

- `POST /api/embed/mxbai`
  - Request: `{ "prompt": "..." }`
  - Response: `{ "embedding": [...] }`

- `POST /api/embed/batch`
  - Request: `{ "prompts": ["..."] }`
  - Response: `{ "embeddings": [[...], ...] }`

## Schemas
- See Swagger UI for full schema details.

## Example Requests
```bash
curl -X POST http://localhost:8000/api/llm -H 'Content-Type: application/json' -d '{"prompt": "Explain quantum computing."}'
curl -X POST http://localhost:8000/api/embed -H 'Content-Type: application/json' -d '{"prompt": "What is AI?"}'
``` 