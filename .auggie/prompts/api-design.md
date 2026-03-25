# Prompt: API Design for SampleMind

Use this when designing new FastAPI endpoints or Flask routes.

---

## How to invoke

Ask Auggie: `"Add a new endpoint for <feature>"`
Or: `"Design the API for <capability>"`

---

## FastAPI endpoint template

```python
# src/samplemind/api/routes/<module>.py
from fastapi import APIRouter, Depends, HTTPException, status
from samplemind.core.auth import get_current_active_user
from samplemind.core.auth.rbac import Permission, RBACService, UserRole
from samplemind.core.models.user import User

router = APIRouter(prefix="/<resource>", tags=["<Tag>"])

@router.get("/", response_model=list[<ResponseSchema>])
async def list_<resource>(current_user: User = Depends(get_current_active_user)):
    """List all <resource>."""
    RBACService.has_permission(UserRole(current_user.role), Permission.AUDIO_READ) or ...
    # implementation

@router.post("/", response_model=<ResponseSchema>, status_code=status.HTTP_201_CREATED)
async def create_<resource>(body: <CreateSchema>, current_user: User = Depends(get_current_active_user)):
    """Create a new <resource>."""
    # implementation
```

## Design checklist for new endpoints

### Naming and HTTP verbs
- [ ] GET for reads (idempotent)
- [ ] POST for creates (returns 201)
- [ ] PUT for full updates
- [ ] PATCH for partial updates
- [ ] DELETE for deletes (returns 204 or 200)
- [ ] Plural nouns for collections: /samples, /users
- [ ] Nested: /samples/{id}/tags

### Auth
- [ ] Protected with `Depends(get_current_active_user)`
- [ ] RBAC permission checked (which Permission enum value?)
- [ ] Public health/status endpoints don't require auth

### Response schemas
- [ ] Use SamplePublic / UserPublic (never expose hashed_password)
- [ ] Return list[Schema] for collections
- [ ] Include pagination for large collections (skip/limit params)

### Error handling
- [ ] 404 → HTTPException(status_code=404, detail="<Resource> not found")
- [ ] 409 → duplicate conflict (e.g. email already exists)
- [ ] 422 → Pydantic validation (automatic)
- [ ] 401 → unauthenticated (automatic from get_current_active_user)
- [ ] 403 → insufficient permissions

### IPC contract
- [ ] JSON responses are machine-readable (stdout from CLI equivalent)
- [ ] CORS origins configured in create_app() for Tauri + Flask origins

### Registration
- [ ] Add router to api/main.py → create_app() with app.include_router()

## Flask route template

```python
# src/samplemind/web/app.py
@app.route("/api/<resource>", methods=["GET"])
def api_<resource>():
    """JSON endpoint for HTMX or browser fetch."""
    # Parse query params
    query = request.args.get("q", "")
    results = SampleRepository.search(query)
    return jsonify([s.model_dump() for s in results])
```

## Service ports reference
- Flask web UI: 5000 (or 5174 in Tauri dev mode)
- FastAPI REST: 8000
- Tauri Vite HMR: 1420

