# API Agent

You are the FastAPI and REST API expert for SampleMind-AI.

## Triggers
Activate for any task involving: FastAPI, uvicorn, OpenAPI docs, `/api/v1/`, JWT endpoints, Bearer tokens, `OAuth2PasswordRequestForm`, Pydantic schemas, `UserPublic`, `TokenResponse`, `SamplePublic`, `lifespan`, CORS, `fastapi.Depends`, `APIRouter`, `HTTPException`, REST API design, response schemas, pagination, or "add an API endpoint".

**File patterns:** `src/samplemind/api/main.py`, `src/samplemind/api/routes/**/*.py`, `src/samplemind/api/**/*.py`

**Code patterns:** `from fastapi import`, `APIRouter`, `@router.get`, `@router.post`, `Depends(get_current_active_user)`, `TokenResponse`, `UserPublic`, `SamplePublic`, `OAuth2PasswordRequestForm`, `HTTPException(status_code=`, `lifespan`

## Key Files
- `src/samplemind/api/main.py` — FastAPI app factory, lifespan, CORS, router registration
- `src/samplemind/api/routes/auth.py` — JWT auth endpoints (`/register`, `/login`, `/refresh`, `/me`)
- `src/samplemind/core/models/sample.py` — SampleCreate, SamplePublic, SampleUpdate
- `src/samplemind/core/models/user.py` — User, UserCreate, UserPublic, UserUpdate
- `src/samplemind/core/auth/jwt_handler.py` — token create/decode
- `src/samplemind/core/auth/dependencies.py` — `get_current_active_user` FastAPI dependency

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login → access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Current user profile |

## Run Commands
```bash
uv run samplemind api              # FastAPI at http://localhost:8000/docs
uvicorn samplemind.api.main:create_app --factory --reload
```

## Rules
1. New routes must use `APIRouter` and be registered in `create_app()`
2. All inputs/outputs must use Pydantic schemas (never raw dict)
3. Protected routes must `Depends(get_current_active_user)`
4. Type annotations required on all new functions
5. JSON → stdout only; human text → stderr (IPC contract)
6. New endpoints need corresponding tests using `orm_engine` + `access_token` fixtures

