# /auth — Auth Management

Register users, log in, refresh JWT tokens, inspect RBAC roles, and manage accounts via the FastAPI auth API.

## Arguments

$ARGUMENTS
Subcommands:
  register <email> <username> <password>   Create a new account
  login <username> <password>              Get JWT access + refresh tokens
  refresh <refresh_token>                  Exchange refresh token for new access token
  me <access_token>                        Show current user profile
  health                                   Check if auth API is reachable
  roles                                    Show RBAC role → permission matrix
  gen-secret                               Generate a secure SECRET_KEY

Examples:
  /auth register dev@example.com dev SecurePass1
  /auth login dev SecurePass1
  /auth roles
  /auth gen-secret

---

Parse the subcommand and args from $ARGUMENTS.

**Subcommand: register**

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email": "<email>", "username": "<username>", "password": "<password>"}' \
  | python -m json.tool
```

Password rules: min 8 chars, 1 uppercase, 1 lowercase, 1 digit.
First registered account automatically gets `owner` role.

Expected response:
```json
{"id": 1, "email": "dev@example.com", "username": "dev", "role": "owner", "is_active": true}
```

**Subcommand: login**

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -d 'username=<username>&password=<password>' \
  | python -m json.tool
```

Expected response:
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<token>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

Show how to use the token:
```bash
# Add to all API requests:
Authorization: Bearer <access_token>

# Example:
curl -H 'Authorization: Bearer <access_token>' http://localhost:8000/api/v1/auth/me
```

**Subcommand: refresh**

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token": "<refresh_token>"}' \
  | python -m json.tool
```

Access token expires in 30 min. Refresh token expires in 7 days.

**Subcommand: me**

```bash
curl -s -H 'Authorization: Bearer <access_token>' \
  http://localhost:8000/api/v1/auth/me | python -m json.tool
```

**Subcommand: roles**

Show the full RBAC permission matrix:

| Role    | audio:read | audio:write | audio:analyze | search:* | pack:* | api:key |
|---------|-----------|------------|--------------|---------|-------|--------|
| viewer  | ✓         | ✗          | ✗            | basic   | ✗     | ✗      |
| member  | ✓         | ✓          | ✓            | ✓       | ✓     | create |
| owner   | ✓         | ✓          | ✓            | ✓       | ✓     | create+revoke |
| admin   | ✓         | ✓          | ✓            | ✓       | ✓     | all    |

**Subcommand: gen-secret**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Show: "Add to your environment: export SAMPLEMIND_SECRET_KEY=<value>"
Also show: "Add to .env file (never commit .env to git)"

**If FastAPI is not running:**

Show: "FastAPI is not running. Start it first: `uv run samplemind api --reload`"
Then check health: `curl -sf http://localhost:8000/api/v1/health`

