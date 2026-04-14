# STACK_GUIDELINES — NDQS Platform

Rekomendacje dot. standardu kodowania, linterów, testów, security i performance na bazie TECH_STACK.md.

---

## Must-have na start

### Backend (FastAPI / Python)

- **Python 3.12+** — f-strings, match/case, performance improvements
- **Ruff** jako linter + formatter (zastępuje flake8, black, isort w jednym narzędziu)
  - Config w `pyproject.toml`
  - Line length: 100
  - Rules: `["E", "F", "W", "I", "N", "UP", "S", "B", "A", "C4", "DTZ", "T20", "ICN", "PIE", "PT", "RSE", "RET", "SLF", "SIM", "TID", "TCH", "ARG", "ERA", "PL", "TRY", "FLY", "PERF", "RUF"]`
- **Type hints** na wszystkich publicznych interfejsach (funcje, metody, schemas)
- **Pydantic v2** — BaseModel dla wszystkich schemas, BaseSettings dla config
- **Async everywhere** — async def na routerach, serwisach, DB session (AsyncSession)
- **Dependency Injection** — FastAPI Depends() dla DB session, current_user, rate limiter
- **Strukturalne logowanie** — `structlog` z JSON output, correlation_id per request
- **pytest + pytest-asyncio** — testy od Stage 1, minimum: happy path + auth + validation
- **httpx.AsyncClient** — do testowania FastAPI endpoints (TestClient)
- **.env + pydantic BaseSettings** — zero hardcoded secrets
- **pre-commit hooks** — ruff check + ruff format + pytest (fast subset)

### Frontend (Next.js / TypeScript)

- **TypeScript strict mode** — `"strict": true` w tsconfig.json
- **Biome** jako linter + formatter (zastępuje ESLint + Prettier, szybszy)
  - Lub ESLint + Prettier jeśli Biome nie wspiera czegoś (fallback)
- **Path aliases** — `@/components`, `@/lib`, `@/types` w tsconfig
- **Server Components by default** — `"use client"` tylko gdy trzeba (interaktywność, hooks)
- **Zod** dla runtime validation (form inputs, API responses)
- **React Hook Form** + Zod resolver dla formularzy
- **Vitest** — unit testy komponentów i utility functions
- **Playwright** — e2e testy krytycznych flow (login, enrollment, quest submit)

### Wspólne

- **Git conventional commits** — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- **Branch strategy** — `main` (produkcja), `dev` (development), `feat/xxx` (feature branches)
- **Docker Compose** dla lokalnego dev environment (backend + frontend + postgres + redis)
- **.gitignore** — `.env`, `node_modules/`, `__pycache__/`, `.next/`, `dist/`, `*.db`
- **Monorepo structure** — `frontend/` i `backend/` w jednym repo

---

## Dobrze dodać później

### Backend
- **Celery / ARQ** — task queue dla LLM ewaluacji (async background jobs). Na start synchroniczne await na LLM response wystarczy.
- **Sentry** — error tracking w produkcji. Na MVP print/log errors.
- **Alembic autogenerate** — automatyczne generowanie migracji z modeli SQLAlchemy. Na start ręczne migracje.
- **OpenTelemetry** — distributed tracing. Na MVP structlog z correlation_id wystarczy.
- **API versioning** (`/api/v1/`) — na MVP nie potrzebne, dodamy przy breaking changes.

### Frontend
- **Storybook** — izolowany development komponentów UI. Na start nie krytyczne.
- **React Query / TanStack Query** — data fetching + cache. Na MVP `fetch` + SWR lub natywne Server Components wystarczą.
- **i18n** — internacjonalizacja. MVP po polsku, i18n dodamy gdy będą kursy w EN.
- **PWA** — offline support. Post-MVP.
- **Analytics (PostHog)** — event tracking, funnel analysis. Na MVP basic server-side metrics.

### Infrastruktura
- **CI/CD pipeline** (GitHub Actions) — auto test + deploy. Na MVP ręczny deploy.
- **Staging environment** — na MVP: local + prod.
- **Database backups** — automatyczne. Na MVP: ręczne pg_dump.
- **CDN (Cloudflare)** — na MVP: Caddy z cache headers wystarczy.
- **S3/MinIO** — file storage. Na MVP: cover images jako URL, brak file upload.

---

## Rozstrzygnięte decyzje

| Decyzja | Wybór | Uzasadnienie |
|---------|-------|-------------|
| **Real-time (Comms Log)** | Polling (co 15-30s) w MVP | Prostota. WebSocket/SSE post-MVP. Comms Log odświeża się po submit i przy load strony. |
| **Quest unlock model** | Tylko artefakty | Jeden mechanizm zamiast dwóch (artefakty + parent questy). Quest wymaga artefaktów → prostsze, bardziej narracyjne. Tabela `quest_dependencies` usunięta. |
| **Quality score** | Hybrid (LLM + countery) | Przy PASS: LLM ocenia 4 wymiary. Zawsze: attempts, hints_used, time_taken. Radar chart łączy oba. |
| **Evaluation types** | 4 typy, implicit pipeline | `text_answer`, `url_check`, `quiz`, `command_output`. Brak osobnego "composite" — każdy typ ma implicit pipeline: validate → deterministic → LLM. |
| **Frontend data fetching** | Server Components default | `"use client"` + fetch/SWR tylko gdy trzeba interaktywności. Server Components pokrywają większość potrzeb (listy kursów, quest details). |

---

## Otwarte decyzje

| Decyzja | Opcje | Kiedy rozstrzygnąć |
|---------|-------|-------------------|
| **Hosting backendu** | Railway vs Render vs VPS (Hetzner) vs Coolify | Przed Phase 5 (Deployment) |
| **Hosting PostgreSQL** | Self-hosted (Docker) vs Supabase vs Neon | Przed Phase 5 |
| **File upload storage** | S3 vs Cloudflare R2 vs MinIO vs local | Post-MVP (file_upload evaluation type jest OUT) |
| **Background jobs** | Celery vs ARQ vs FastAPI BackgroundTasks | Gdy LLM ewaluacja stanie się bottleneckiem |
| **Monetyzacja** | Stripe vs Paddle vs LemonSqueezy | Nie w MVP |
| **Email** | Resend vs SendGrid vs Postmark | Gdy dodamy magic links lub notyfikacje |
