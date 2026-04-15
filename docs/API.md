# NDQS Platform — API Reference

## Base URL

- Development: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

## Authentication

Most endpoints require either:
- **Bearer token**: `Authorization: Bearer <access_token>`
- **API Key**: `X-API-Key: ndqs_<key>`

---

## Health

### `GET /api/health`
Returns service health status. No auth required.

**Response** `200`:
```json
{"status": "ok", "service": "ndqs-backend"}
```

---

## Auth — OAuth

### `GET /api/auth/github/login`
Redirects to GitHub OAuth authorization page.

**Response** `302`: Redirect to `https://github.com/login/oauth/authorize`

### `GET /api/auth/github/callback?code=<code>`
GitHub OAuth callback. Exchanges code for token and creates/finds user.

> **Note:** Currently a stub — returns acknowledgment but does not complete OAuth flow.

**Query params:**
- `code` (string, required, min_length=1)

**Response** `200`:
```json
{"message": "OAuth callback received", "code": "<code>"}
```

---

## Auth — JWT

### `GET /api/auth/me`
Returns current user info. Requires auth (JWT or API Key).

**Headers:** `Authorization: Bearer <token>` or `X-API-Key: <key>`

**Response** `200`:
```json
{"user_id": "<uuid>", "role": "student|admin", "email": "<email>"}
```

**Response** `401`: Missing or invalid auth.

### `POST /api/auth/refresh`
Refreshes JWT tokens. Requires valid refresh token.

**Headers:** `Authorization: Bearer <refresh_token>`

**Response** `200`:
```json
{
  "access_token": "<new_access_token>",
  "refresh_token": "<new_refresh_token>",
  "token_type": "bearer"
}
```

**Response** `401`: Invalid or expired refresh token.

### `POST /api/auth/logout`
Logs out current user. Requires auth.

> **Note:** Currently returns success but does not blacklist token in Redis (TODO).

**Response** `200`:
```json
{"message": "Logged out successfully"}
```

---

## Auth — API Keys

### `POST /api/auth/api-key/generate`
Generates a new API key. Requires auth.

**Body:**
```json
{"name": "My Key"}
```

- `name` (string, required, 1-255 chars, not blank)

**Response** `201`:
```json
{
  "id": "<uuid>",
  "name": "My Key",
  "key": "ndqs_<raw_key>",
  "prefix": "ndqs_<first8chars>",
  "created_at": "<iso_datetime>"
}
```

### `GET /api/auth/api-key/list`
Lists user's API keys (masked). Requires auth.

**Response** `200`:
```json
[
  {
    "id": "<uuid>",
    "name": "My Key",
    "prefix": "ndqs_<first8chars>",
    "is_active": true,
    "created_at": "<iso_datetime>",
    "expires_at": null
  }
]
```

### `DELETE /api/auth/api-key/revoke/{key_id}`
Revokes an API key. Requires auth.

**Path params:**
- `key_id` (UUID, required)

**Response** `200`:
```json
{"message": "API key revoked"}
```

**Response** `404`: API key not found or doesn't belong to user.

---

## Security Headers

All responses include:
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin`
- `X-Permitted-Cross-Domain-Policies: none`
- `X-Correlation-Id: <uuid>` (per-request tracking)

## Token Details

- Access token TTL: 15 minutes
- Refresh token TTL: 7 days
- Refresh tokens are rotated (new pair on each refresh)
