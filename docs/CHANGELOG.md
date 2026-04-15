# Changelog

All notable changes to the NDQS Platform are documented here.

## [Unreleased]

### Stage 1: Minimal Working Application (Scaffolding)

#### Added
- **Backend scaffold** — FastAPI project structure with domain packages (`auth`, `courses`, `quests`, `evaluation`), health endpoint, CORS, custom exception handler
- **Frontend scaffold** — Next.js 15 App Router with Tailwind 4, shadcn/ui, dark theme, Geist Sans + JetBrains Mono fonts, CSP headers
- **Docker Compose** — backend + frontend + PostgreSQL 16 + Redis 7 with healthchecks and `depends_on` conditions
- **Database setup** — SQLAlchemy async engine (asyncpg), Alembic migrations, `users` table with role enum (student/admin)
- **Auth backend** — GitHub OAuth login flow, JWT access tokens (15min) + refresh tokens (7d) with rotation, logout endpoint, `get_current_user` middleware supporting JWT and API Key auth
- **Auth frontend** — NextAuth.js v5 config with GitHub provider, login page
- **API Key system** — generate, list (masked), revoke endpoints; keys hashed with SHA-256 and prefixed `ndqs_`
- **Frontend-backend integration** — Next.js proxy to FastAPI, shared types, `api-client.ts` wrapper, OpenAPI Swagger UI at `/docs`
- **Structured logging** — structlog with JSON output, correlation_id middleware per request
- **Rate limiting** — slowapi-based rate limiting on auth endpoints: 10 login attempts/IP/5min, 3 API key generations/user/hour
- **Error hardening** — custom `RequestValidationError` handler: production returns sanitized field+message errors; development returns full Pydantic details

#### Security
- Input validation with Pydantic schemas on all auth endpoints
- Secrets managed via `.env` + pydantic `BaseSettings` with production validation
- Restrictive CORS allowlist (localhost:3000 dev, production domain)
- JWT short-lived access tokens (15min), refresh rotation (7d), API keys hashed
- Security access tests: 401 for missing/invalid/expired tokens
- CSRF protection via Origin header check middleware, SameSite cookies
- Security headers: CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Referrer-Policy
- Rate limiting on auth endpoints (429 on abuse)
- Error messages hardened for production (no stack traces, no DB schema leaks)

### Stage 2: Courses & Enrollment

#### Added
- **Course models** — `courses` and `enrollments` tables (Alembic migration 002)
- **Admin CRUD** — `POST/PUT /api/admin/courses` (admin-only, Pydantic validation)
- **Course catalog** — `GET /api/courses` (published only), `GET /api/courses/{id}`
- **Enrollment** — `POST /api/courses/{id}/enroll` (duplicate + published check, rate limited)
- **Starter Pack** — `GET /api/courses/{id}/starter-pack` (dynamic ZIP: CLAUDE.md, .env.example, README)
- **Frontend: Missions catalog** — `/missions` with dark modern SaaS cards, skeleton loaders
- **Frontend: Course detail** — `/missions/[courseId]` with enroll button + starter pack download
- **Frontend: Admin CRUD** — `/admin/courses` with course creation form
- **Seed script** — `scripts/seed_dev.py` with demo admin, student, 2 courses (Skynet Breaker, Pandemic Shield)

#### Security
- Admin role authorization middleware (`require_admin`)
- Pydantic input validation (title max 255, description max 5000)
- Rate limiting on enrollment (10/h) and starter-pack (5/min)
- Security tests: student → 403 on admin endpoints, no-auth → 401
