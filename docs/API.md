# API Reference — NDQS Platform

Base URL: `http://localhost:8000`

Interactive docs (Swagger UI): `http://localhost:8000/docs`

## Authentication

All protected endpoints require one of:
- **JWT Bearer token**: `Authorization: Bearer <access_token>`
- **API Key**: `X-API-Key: ndqs_<key>`

---

## Health

### `GET /api/health`
Returns service status. No auth required.

**Response** `200`
```json
{"status": "ok", "service": "ndqs-backend"}
```

---

## Auth — OAuth

### `GET /api/auth/github/login`
Redirects to GitHub OAuth authorization page.

**Rate limit**: 10 requests per IP per 5 minutes.

**Response** `302` → Redirect to `https://github.com/login/oauth/authorize`

### `GET /api/auth/github/callback?code={code}`
OAuth callback. Exchanges authorization code for user token.

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | yes | GitHub authorization code (min 1 char) |

**Response** `200`
```json
{"message": "OAuth callback received", "code": "..."}
```

---

## Auth — JWT

### `GET /api/auth/me`
Returns current user info. Requires JWT or API Key auth.

**Response** `200`
```json
{"user_id": "uuid", "role": "student", "email": "user@example.com"}
```

**Errors**: `401` — missing or invalid token

### `POST /api/auth/refresh`
Refreshes an expired access token using a valid refresh token. Returns new token pair (rotation — old refresh token is invalidated).

**Headers**: `Authorization: Bearer <refresh_token>`

**Response** `200`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors**: `401` — missing or invalid refresh token

### `POST /api/auth/logout`
Logs out the current user. Requires JWT or API Key auth.

**Response** `200`
```json
{"message": "Logged out successfully"}
```

---

## Auth — API Keys

### `POST /api/auth/api-key/generate`
Generates a new API key for the authenticated user. The raw key is returned **once** — store it securely.

**Rate limit**: 3 requests per user per hour.

**Auth**: Required (JWT)

**Body**
```json
{"name": "My CLI Key"}
```

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | 1–255 chars, non-blank |

**Response** `201`
```json
{
  "id": "uuid",
  "name": "My CLI Key",
  "key": "ndqs_abc123...",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Errors**: `401` — not authenticated, `422` — validation error, `429` — rate limited

### `GET /api/auth/api-key/list`
Lists all API keys for the authenticated user. Keys are masked (only prefix shown).

**Auth**: Required (JWT)

**Response** `200`
```json
[
  {"id": "uuid", "name": "My CLI Key", "key_prefix": "ndqs_abc1...", "created_at": "..."}
]
```

### `DELETE /api/auth/api-key/revoke/{key_id}`
Revokes an API key by ID.

**Auth**: Required (JWT)

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `key_id` | UUID | yes | API key ID to revoke |

**Response** `200`
```json
{"message": "API key revoked"}
```

**Errors**: `401` — not authenticated, `404` — key not found, `422` — invalid UUID

---

## Error Responses

### Validation Error `422`
**Production**: sanitized field + message
```json
{"detail": [{"field": "name", "message": "Field required"}]}
```

**Development**: full Pydantic details (loc, msg, type, ctx)

### Rate Limited `429`
```json
{"error": "Rate limit exceeded: 10 per 5 minute"}
```

### Internal Error `500`
**Production**: `{"detail": "Internal server error"}` with `X-Correlation-ID` header

**Development**: includes `detail` (error message) and `traceback`
