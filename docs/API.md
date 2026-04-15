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

## Courses

### `GET /api/courses`
List all published courses.

**Auth**: Required (JWT or API Key)

**Response** `200`: Array of course objects with `id`, `title`, `narrative_title`, `description`, `persona_name`, `cover_image_url`, `is_published`, `created_at`.

### `GET /api/courses/{course_id}`
Get course details including `global_context`, `persona_prompt`, `updated_at`.

**Auth**: Required (JWT or API Key)

**Errors**: `404` — course not found

### `POST /api/admin/courses`
Create a new course. **Admin only.**

**Auth**: Required (JWT, role=admin)

**Body**

| Field | Type | Constraints |
|-------|------|-------------|
| `title` | string | 1–255 chars, required, non-blank |
| `narrative_title` | string | max 255, optional |
| `description` | string | max 5000, optional |
| `persona_name` | string | max 100, optional |
| `persona_prompt` | string | max 10000, optional |
| `global_context` | string | max 10000, optional |
| `cover_image_url` | string | max 500, optional |
| `model_id` | string | max 100, optional |
| `is_published` | boolean | default false |

**Response** `201`: `{"id": "uuid", "title": "...", "is_published": false}`

**Errors**: `403` — not admin, `422` — validation error

### `PUT /api/admin/courses/{course_id}`
Update a course. **Admin only.** Partial update (only send fields to change).

**Auth**: Required (JWT, role=admin)

**Errors**: `403` — not admin, `404` — not found

---

## Enrollment

### `POST /api/courses/{course_id}/enroll`
Enroll the current user in a course.

**Auth**: Required (JWT or API Key)

**Rate limit**: 10 per user per hour

**Response** `201`: `{"user_id": "uuid", "course_id": "uuid", "status": "enrolled"}`

**Errors**: `400` — course not published, `404` — not found, `409` — already enrolled, `429` — rate limited

---

## Starter Pack

### `GET /api/courses/{course_id}/starter-pack`
Download a ZIP file with `CLAUDE.md`, `.env.example`, and `README.md` configured for the course.

**Auth**: Required (JWT or API Key)

**Rate limit**: 5 per user per minute

**Response**: `200` — `application/zip` file download

**Errors**: `404` — course not found, `429` — rate limited

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
