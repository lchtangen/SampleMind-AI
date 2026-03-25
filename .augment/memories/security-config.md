# Memory: Security Configuration

JWT + RBAC auth system in `src/samplemind/core/auth/`.

## JWT Configuration

| Setting | Value |
|---------|-------|
| Algorithm | HS256 |
| Access token TTL | 30 minutes (1800 s) |
| Refresh token TTL | 7 days |
| Secret key env var | `SAMPLEMIND_SECRET_KEY` |
| Default (insecure) | `"change-me-before-deployment..."` |

⚠ **Never hardcode the secret key.** Always set `SAMPLEMIND_SECRET_KEY` in env.

## Token Response Schema

```json
{
  "access_token": "<JWT string>",
  "refresh_token": "<opaque string>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Use in Authorization header: `Authorization: Bearer <access_token>`

## RBAC Roles

| Role | Permissions |
|------|-------------|
| `viewer` | `audio:read`, `search:basic` |
| `member` | all audio ops, search, packs, api key create |
| `owner` | member + api key revoke (default for new accounts) |
| `admin` | all permissions |

## Password Rules

- Minimum length: 8 characters
- Must contain: uppercase + lowercase + digit

## Auth Routes (FastAPI — port 8000)

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get token pair |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Current user profile |
| GET | `/api/v1/health` | Health check |

## Key Source Files

```
src/samplemind/core/auth/jwt_handler.py   — create_access_token(), decode_token()
src/samplemind/core/auth/rbac.py          — RBACService, Permission, UserRole
src/samplemind/core/auth/dependencies.py  — get_current_active_user (FastAPI Depends)
src/samplemind/api/routes/auth.py         — /register /login /refresh /me
src/samplemind/core/models/user.py        — User, UserCreate, UserRole SQLModel
```

## Test Fixtures (from tests/conftest.py)

```python
# orm_engine  — in-memory SQLite with StaticPool
# test_user   — User row with email=test@example.com, password="testpassword123"
# access_token — valid JWT bearer token string for test_user
# Usage: {"Authorization": f"Bearer {access_token}"}
```

## Security Notes

- Tokens are stateless — logout is client-side only (delete the token)
- No token revocation list (planned for Phase 10)
- OAuth2 providers (Google, GitHub) require `GOOGLE_CLIENT_ID` etc. env vars
- Tauri WebView must include `Authorization` header for API calls

