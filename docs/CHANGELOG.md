# Changelog

## Stage 1 — Minimalna Dzialajaca Aplikacja (Scaffolding)

### Completed
- **T0:** `.env.example` with all required variables and documentation
- **T1:** Backend FastAPI scaffold — directory structure, CORS, `/api/health`, custom exception handler
- **T2:** Frontend Next.js 15 scaffold — App Router, Tailwind 4, dark theme, Geist/JetBrains Mono fonts, CSP headers
- **T3:** Docker Compose — backend + frontend + PostgreSQL + Redis with healthchecks and depends_on conditions
- **T4:** Database setup — SQLAlchemy async (asyncpg), Alembic async migrations, `users` table with role enum
- **T6:** Auth frontend — NextAuth.js v5, GitHub provider, login page with terminal theme
- **T7:** API Key system — generate, list (masked), revoke endpoints; SHA256 hashed storage
- **T8:** Frontend-backend integration — Next.js proxy, api-client.ts, shared TypeScript types
- **T9:** Structlog setup — JSON logging, correlation ID middleware, log level via env

### Security Completed
- **S1:** Pydantic input validation on all auth endpoints
- **S2:** Secrets in `.env` with BaseSettings production validation (32-char min)
- **S3:** CORS restricted to FRONTEND_URL allowlist
- **S4:** JWT TTL (15min access, 7d refresh) with rotation; API keys hashed
- **S5:** Security tests — 401 for missing/invalid/expired auth (8 test cases)
- **S6:** CSRF origin validation middleware
- **S7:** Security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
- **S9:** Error message hardening — generic 500 in production, no schema leaks

### In Progress / TODO
- **T5:** Auth backend — JWT/refresh/middleware works, but GitHub OAuth callback and logout Redis blacklist are stubs
- **S8:** Rate limiting — slowapi dependency installed but `app/rate_limit` module not created; tests fail

### Known Issues
- T2: shadcn/ui not initialized (dependency installed but `npx shadcn init` not run)
- T6: Login button text in English ("Sign in with GitHub") instead of Polish
- T6: No animated terminal onboarding (framer-motion installed but not used)
- S4: API keys use SHA256 instead of bcrypt (passlib installed but not integrated)
- Biome: `globals.css` Tailwind 4 `@theme` directive causes parse warning (Biome limitation)
