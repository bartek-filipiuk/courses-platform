# HANDOFF_STAGES_PLAN — NDQS Platform

---

## Stage 1: Minimalna Działająca Aplikacja (Scaffolding)
**Cel:** Postawić szkielet projektu — backend i frontend gadające ze sobą, auth, baza danych, Docker, basic CI.
**User Stories:** US-1 (rejestracja/logowanie), US-12 (API Key)

### Taski:
- [x] T0: `.env.example` — plik z komentarzami: DATABASE_URL, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, JWT_SECRET_KEY, JWT_REFRESH_SECRET, OPENROUTER_API_KEY, REDIS_URL. Komentarz przy każdej zmiennej. (test → kod → verify)
- [x] T1: Scaffold backend FastAPI — struktura katalogów (app/auth, app/courses, app/quests, app/evaluation), main.py z CORS, health endpoint `/api/health`, custom exception handler (generic 500 w prod, stack trace w dev) (test → kod → verify)
- [x] T2: Scaffold frontend Next.js 15 — App Router, layout.tsx, Tailwind 4, shadcn/ui init, dark theme setup, Geist Sans + JetBrains Mono fonts, CSP headers w next.config (test → kod → verify)
- [x] T3: Docker Compose — backend + frontend + PostgreSQL + Redis. Healthchecks na PG (`pg_isready`) i Redis (`redis-cli ping`). `depends_on` z `condition: service_healthy`. Alembic migrations w backend entrypoint. (test → kod → verify)
- [x] T4: Database setup — SQLAlchemy async engine (asyncpg), Alembic init z async env.py, pierwsza migracja: tabela `users` z kolumną `role` (enum: 'student', 'admin', default 'student') (test → kod → verify)
- [x] T5: Auth backend — OAuth callback (GitHub), JWT creation (access 15min + refresh 7d), refresh token rotation (stary invalidated), `POST /api/auth/logout` (token blacklist w Redis, TTL = remaining JWT lifetime), middleware `get_current_user` (JWT lub API Key) (test → kod → verify)
- [x] T6: Auth frontend — NextAuth.js v5 config, GitHub provider, login page z przyciskiem "Zaloguj przez GitHub", animowany terminal onboarding (test → kod → verify)
- [x] T7: API Key system — model `api_keys` (z optional `expires_at`), endpoint `POST /api/auth/api-key/generate`, `DELETE /api/auth/api-key/revoke`, `GET /api/auth/api-key/list` (zamaskowane klucze), `GET /api/auth/me` (auth via JWT lub API Key) (test → kod → verify)
- [x] T8: Frontend-backend integration — proxy Next.js → FastAPI, shared types, api-client.ts wrapper, OpenAPI Swagger UI na /docs (test → kod → verify)
- [x] T9: Structlog setup — JSON logging, correlation_id middleware (per request UUID w logach), log level config via env var (test → kod → verify)

### Security (MANDATORY):
- [x] S1: Input validation — Pydantic schemas na auth endpoints, rejekcja malformed requests (Baseline #2)
- [x] S2: Sekrety w .env — DATABASE_URL, GITHUB_CLIENT_SECRET, JWT_SECRET_KEY, OPENROUTER_API_KEY w `.env`, BaseSettings walidacja (Baseline #5)
- [x] S3: CORS restrykcyjny — allowlist: localhost:3000 (dev), domena produkcyjna. FastAPI CORSMiddleware. (Baseline #6)
- [x] S4: Hasła/tokeny — JWT access token TTL 15min, refresh 7d z rotation. API keys hashowane bcrypt (passlib). (Baseline #7)
- [x] S5: Test security: próba dostępu do /api/auth/me bez tokena → 401. Próba z invalid API Key → 401. Próba z expired JWT → 401. (Baseline #1)
- [x] S6: CSRF protection — CSRF token na POST endpoints (fastapi-csrf-protect lub custom middleware). SameSite=Lax cookies. (Baseline #6)
- [x] S7: CSP + security headers — Content-Security-Policy, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Referrer-Policy: strict-origin. Od Stage 1 (nie czekamy do Stage 6). (Baseline #6)
- [x] S8: Rate limiting auth — max 10 login attempts per IP per 5min, max 3 API key generations per user per hour (slowapi + Redis). Test: 11 requests → 429. (Baseline #8)
- [x] S9: Error message hardening — custom exception handler: production → generic "Internal server error" (500), development → stack trace. Validation errors nie ujawniają DB schema. (PRD threat model)

### Docs (MANDATORY):
- [x] Update docs/CHANGELOG.md
- [x] Update docs/API.md (auth endpoints)
- [x] Update docs/README.md (Quick Start, struktura katalogów)

### Stage Completion (MANDATORY):
- [x] Self-check: zakres stage zgodny z PRD (US-1, US-12 pokryte)
- [x] Self-check: brak hardcoded secrets w kodzie
- [x] Self-check: testy zielone (funkcjonalne + security)
- [x] Zaktualizuj HANDOFF: WSZYSTKIE checkboxy tego stage → [x]

---

## Stage 2: Kursy i Enrollment
**Cel:** CRUD kursów, katalog kursów dla kursanta, enrollment flow, Starter Pack download.
**User Stories:** US-2 (katalog kursów), US-3 (enrollment), US-4 (Starter Pack), US-14 (CRUD kursów admin)

### Taski:
- [x] T1: Model danych — migracja: tabele `courses`, `enrollments` (test → kod → verify)
- [x] T2: Backend CRUD kursów — `POST /api/admin/courses`, `PUT /api/admin/courses/{id}`, `GET /api/courses`, `GET /api/courses/{id}` z auth admin (test → kod → verify)
- [x] T3: Enrollment endpoint — `POST /api/courses/{id}/enroll`, tworzenie wpisu w enrollments (test → kod → verify)
- [x] T4: Starter Pack generator — `GET /api/courses/{id}/starter-pack`, generowanie ZIP w locie (CLAUDE.md z system promptem, .env.example, README.md) (test → kod → verify)
- [x] T5: Frontend: Katalog kursów — strona `/missions` z kartami kursów (Mission Briefs), filtrowanie, dark modern design, Framer Motion animations (test → kod → verify)
- [x] T6: Frontend: Strona kursu — `/missions/[courseId]` z opisem, przyciskiem "Przyjmij Misję" (enroll), "Pobierz Starter Pack" (test → kod → verify)
- [x] T7: Frontend: Admin CRUD — `/admin/courses` lista + formularz tworzenia/edycji kursu (test → kod → verify)
- [ ] T8: Rate limiter infrastructure — setup slowapi z Redis backend, dekorator `@rate_limit`, konfiguracja per-endpoint limitów via env/config (test → kod → verify)
- [ ] T9: Seed script — `scripts/seed_dev.py`: demo admin user, 2 demo kursy (beginner/advanced), 5-6 demo questów per kurs, demo artefakty. Uruchamiany ręcznie lub via `docker compose exec backend python scripts/seed_dev.py` (test → kod → verify)

### Security (MANDATORY):
- [ ] S1: Autoryzacja admin — middleware `require_admin` sprawdzający role='admin' na endpointach admin. User z role='student' nie może tworzyć kursów (Baseline #1)
- [ ] S2: Walidacja input — Pydantic na course CRUD (title max 255, description max 5000, sanityzacja HTML) (Baseline #2)
- [ ] S3: Rate limiting — max 10 enrollments per user per godzinę, max 5 starter-pack downloads per minutę (Baseline #8)
- [ ] S4: Test security: próba POST /api/admin/courses z tokenem studenta → 403. Próba enrollment bez auth → 401. (Baseline #1)

### Docs (MANDATORY):
- [ ] Update docs/CHANGELOG.md
- [ ] Update docs/API.md (courses, enrollment, starter-pack endpoints)
- [ ] Update docs/README.md (jeśli zmiana struktury)

### Stage Completion (MANDATORY):
- [ ] Self-check: zakres stage zgodny z PRD (US-2, US-3, US-4, US-14 pokryte)
- [ ] Self-check: brak hardcoded secrets w kodzie
- [ ] Self-check: testy zielone (funkcjonalne + security)
- [ ] Zaktualizuj HANDOFF: WSZYSTKIE checkboxy tego stage → [x]

---

## Stage 2+ content unchanged — see full file in repo
