# Skill: auth

Manage user authentication: register accounts, obtain JWT tokens, refresh tokens,
and inspect RBAC roles. Requires FastAPI server running on port 8000.

## When to use

Use this skill when the user asks to:
- Register a new user account
- Log in and get a JWT bearer token
- Refresh an expired access token
- Check current user profile / roles
- Understand RBAC permission levels
- Debug auth errors (401, 403, token expired)

## Commands

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email": "user@example.com", "password": "SecurePass1"}'
```

### Login (get token pair)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d 'username=user@example.com&password=SecurePass1'
```

### Refresh access token

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token": "<refresh_token>"}'
```

### Get current user

```bash
curl -H 'Authorization: Bearer <access_token>' \
  http://localhost:8000/api/v1/auth/me
```

### Health check

```bash
curl http://localhost:8000/api/v1/health
```

## Token Response

```json
{
  "access_token": "<JWT>",
  "refresh_token": "<opaque>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## RBAC Roles

| Role | Description |
|------|-------------|
| `viewer` | Read-only (shared library) |
| `member` | Standard user — full audio ops |
| `owner` | Default for new accounts — member + key revoke |
| `admin` | All permissions |

## JWT Config

- Algorithm: HS256
- Access token: 30 min
- Refresh token: 7 days
- Secret: `SAMPLEMIND_SECRET_KEY` env var — **never hardcode**

## Password Rules

- Minimum 8 characters
- Must contain uppercase, lowercase, and digit

## Common errors

| Error | Fix |
|-------|-----|
| 401 Unauthorized | Token expired — use `/auth/refresh` |
| 403 Forbidden | Role insufficient for the operation |
| 422 Unprocessable | Password too weak or missing fields |
| Connection refused | Start FastAPI: `uv run samplemind api` |

## Key source files

- `src/samplemind/core/auth/jwt_handler.py` — token creation/validation
- `src/samplemind/core/auth/rbac.py` — RBACService, UserRole, Permission
- `src/samplemind/api/routes/auth.py` — route handlers
- `src/samplemind/core/models/user.py` — User, UserCreate SQLModel

## Related skills

- `serve` — start the FastAPI server first
- `health-check` — verify FastAPI is responding

