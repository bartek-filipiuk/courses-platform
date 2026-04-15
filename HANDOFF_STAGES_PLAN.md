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
- [x] T8: Rate limiter infrastructure — setup slowapi z Redis backend, dekorator `@rate_limit`, konfiguracja per-endpoint limitów via env/config (test → kod → verify)
- [x] T9: Seed script — `scripts/seed_dev.py`: demo admin user, 2 demo kursy (beginner/advanced), 5-6 demo questów per kurs, demo artefakty. Uruchamiany ręcznie lub via `docker compose exec backend python scripts/seed_dev.py` (test → kod → verify)

### Security (MANDATORY):
- [x] S1: Autoryzacja admin — middleware `require_admin` sprawdzający role='admin' na endpointach admin. User z role='student' nie może tworzyć kursów (Baseline #1)
- [x] S2: Walidacja input — Pydantic na course CRUD (title max 255, description max 5000, sanityzacja HTML) (Baseline #2)
- [x] S3: Rate limiting — max 10 enrollments per user per godzinę, max 5 starter-pack downloads per minutę (Baseline #8)
- [x] S4: Test security: próba POST /api/admin/courses z tokenem studenta → 403. Próba enrollment bez auth → 401. (Baseline #1)

### Docs (MANDATORY):
- [x] Update docs/CHANGELOG.md
- [x] Update docs/API.md (courses, enrollment, starter-pack endpoints)
- [x] Update docs/README.md (jeśli zmiana struktury)

### Stage Completion (MANDATORY):
- [x] Self-check: zakres stage zgodny z PRD (US-2, US-3, US-4, US-14 pokryte)
- [x] Self-check: brak hardcoded secrets w kodzie
- [x] Self-check: testy zielone (funkcjonalne + security)
- [x] Zaktualizuj HANDOFF: WSZYSTKIE checkboxy tego stage → [x]

---

## Stage 3: Quest Engine (FSM + Artefakty)
**Cel:** Serce platformy — questy, maszyna stanów, artefakty (jedyny mechanizm unlock).
**User Stories:** US-5 (Quest Map), US-6 (Briefing), US-9 (Artefakty/Inventory), US-15 (CRUD questów), US-16 (Artefakty admin), US-18 (podgląd quest mapy)

### Taski:
- [x] T1: Model danych — migracja: tabele `quests` (z `required_artifact_ids UUID[]`), `quest_states`, `artifact_definitions` (template per quest, 1:1), `user_artifacts` (instancja per user, z `signature` HMAC). BEZ tabeli `quest_dependencies` — unlock wyłącznie przez artefakty. (test → kod → verify)
- [x] T2: Quest FSM — state_machine.py: przejścia LOCKED→AVAILABLE→IN_PROGRESS→EVALUATING→COMPLETED/FAILED_ATTEMPT. Logika unlock: quest jest AVAILABLE gdy user ma WSZYSTKIE artefakty z `required_artifact_ids`. Pierwszy quest kursu (bez required_artifacts) → AVAILABLE od razu po enrollment. (test → kod → verify)
- [x] T3: Quest API — `GET /api/quests/{id}/briefing`, `GET /api/quests/{id}/status`, `GET /api/courses/{id}/quests` (lista questów z ich stanami per user) (test → kod → verify)
- [x] T4: Artifact system — po COMPLETED: mint artefaktu (HMAC SHA256 signature z user_id + artifact_id + secret), zapis do user_artifacts. Po mint: sprawdzenie "które questy mają ten artefakt w required_artifact_ids?" → jeśli user ma WSZYSTKIE required → quest → AVAILABLE. (test → kod → verify)
- [x] T5: Admin CRUD questów — `POST /api/admin/quests`, `PUT /api/admin/quests/{id}`, pola: briefing, evaluation_type, evaluation_criteria, failure_states, required_artifacts, reward_artifact (test → kod → verify)
- [x] T6: Frontend: Quest Map — React Flow z custom nodes (stany: LOCKED/AVAILABLE/IN_PROGRESS/COMPLETED/FAILED_ATTEMPT), animated edges, minimap, zoom/pan (test → kod → verify)
- [x] T7: Frontend: Quest Detail Panel — slide-in z prawej: briefing (terminal style), objectives, submissions history, status (test → kod → verify)
- [x] T8: Frontend: Inventory — panel artefaktów kursanta, lista z nazwą fabularną i questem źródłowym (test → kod → verify)
- [x] T9: Frontend: Admin Quest editor — formularz z zakładkami (Fabuła, Techniczne, Kryteria, Zależności) + read-only React Flow preview mapy (test → kod → verify)

### Security (MANDATORY):
- [x] S1: Quest access control — kursant widzi briefing tylko dla AVAILABLE/IN_PROGRESS/COMPLETED questów. LOCKED = 403 (Baseline #1)
- [x] S2: Walidacja quest CRUD — Pydantic: briefing max 10000 znaków, failure_states jako validowany JSONB, evaluation_criteria sanityzowane (Baseline #2)
- [x] S3: Anti-tamper na artefaktach — artefakty generowane server-side z signed hash, user nie może podrobić artefaktu (PRD: threat model)
- [x] S4: Test security: próba GET /api/quests/{locked_quest}/briefing → 403 (Baseline #1)

### Docs (MANDATORY):
- [x] Update docs/CHANGELOG.md
- [x] Update docs/API.md (quest endpoints, artifact endpoints)
- [x] Update docs/README.md (Quest Map architecture)

### Stage Completion (MANDATORY):
- [x] Self-check: zakres stage zgodny z PRD (US-5, US-6, US-9, US-15, US-16, US-18 pokryte)
- [x] Self-check: brak hardcoded secrets w kodzie
- [x] Self-check: testy zielone (funkcjonalne + security)
- [x] Zaktualizuj HANDOFF: WSZYSTKIE checkboxy tego stage → [x]

---

## Stage 4: Silnik Ewaluacyjny
**Cel:** Pipeline ewaluacji odpowiedzi kursanta — walidacja, weryfikacja (deterministyczna + LLM Judge), Game Master feedback.
**User Stories:** US-7 (Submit), US-8 (Ewaluacja i feedback), US-10 (Hint), US-17 (Game Master config)

### Taski:
- [x] T0: OpenRouter integration setup — API key w .env, httpx AsyncClient wrapper (`app/evaluation/openrouter_client.py`), test connectivity, fallback model config per kurs, structured JSON response format (test → kod → verify)
- [x] T1: Model danych — migracja: tabela `submissions` (z `quality_scores JSONB`), `comms_log` (z `message_type` enum: briefing/evaluation/hint/system) (test → kod → verify)
- [x] T2: Submit endpoint — `POST /api/quests/{id}/submit`, payload walidowany dynamicznie per quest evaluation_type (text_answer, url_check, quiz, command_output). Pydantic discriminated union. (test → kod → verify)
- [x] T3: Evaluation pipeline — orchestrator.py: sanityzacja → deterministic checks (jeśli dotyczy) → LLM Judge (jeśli dotyczy) → result (pass/fail + narrative response). Quiz = deterministic only, text_answer = LLM only, url_check/command_output = deterministic + LLM. (test → kod → verify)
- [x] T4: Deterministic evaluator — quiz (key matching, case-insensitive), url_check (httpx GET/POST → status/body check, timeout 10s), command_output (regex/pattern matching z evaluation_criteria) (test → kod → verify)
- [x] T5: LLM Judge (OpenRouter) — llm_service.py: budowanie promptu z quest criteria + failure states + student answer + deterministic results → structured JSON output. Pydantic walidacja response. Retry 3x z exponential backoff. Timeout 30s. Fallback message. (test → kod → verify)
- [x] T6: Game Master response — po ewaluacji: zapis do submissions (z quality_scores), zapis do comms_log, aktualizacja quest_state (COMPLETED → mint artifact, FAILED_ATTEMPT → feedback), return narrative response (test → kod → verify)
- [x] T7: Hint endpoint — `POST /api/quests/{id}/hint`, LLM generuje pytanie sokratyczne, sprawdzenie limitu hintów, dekrementacja completeness score (-1 per hint, min 1), zapis do comms_log (test → kod → verify)
- [x] T8: Admin: Game Master config — formularz persona (name, prompt, tone, model_id via OpenRouter), preview response z sample submission (test → kod → verify)
- [x] T9: Frontend: Submit UI — formularz submisji per quest type (text area, URL input, quiz radio buttons, command output paste). Loading state z animacją podczas ewaluacji LLM. (test → kod → verify)
- [x] T10: Frontend: Feedback display — narrative response od Game Mastera w terminal-style, pass/fail indicator, quality radar chart (jeśli pass) (test → kod → verify)

### Security (MANDATORY):
- [x] S1: Prompt injection protection — sanityzacja odpowiedzi kursanta przed wstrzyknięciem do LLM prompt. (PRD: threat model)
- [x] S2: Rate limiting na submit — max 5 submisji per quest per godzinę per user (Baseline #8)
- [x] S3: Rate limiting na hint — max 3 hinty per quest, max 10 hint requestów per godzinę (Baseline #8)
- [x] S4: XSS prevention — escape LLM response przed renderowaniem w UI. CSP headers. (Baseline #4)
- [x] S5: Input size limits — text_answer max 5000 znaków, URL max 500 znaków, command_output max 10000 znaków (Baseline #2)
- [x] S6: Test security: prompt injection testy z konkretnymi payloadami (PRD: threat model)
- [x] S7: Error exposure hardening — validation errors nie ujawniają DB schema. LLM timeout → fallback. (PRD: threat model)
- [x] S8: Evaluation replay protection — identyczny payload w 30min → cached result (Redis). (PRD: threat model)

### Docs (MANDATORY):
- [x] Update docs/CHANGELOG.md
- [x] Update docs/API.md (submit, hint, evaluation endpoints)
- [x] Update docs/README.md (Evaluation pipeline architecture)

### Stage Completion (MANDATORY):
- [x] Self-check: zakres stage zgodny z PRD (US-7, US-8, US-10, US-17 pokryte)
- [x] Self-check: brak hardcoded secrets w kodzie
- [x] Self-check: testy zielone (funkcjonalne + security)
- [x] Zaktualizuj HANDOFF: WSZYSTKIE checkboxy tego stage → [x]

---

## Stage 5: Comms Log, Statystyki i Metryki
**Cel:** Historia komunikacji, profil kursanta ze statystykami, basic analytics dla admina.
**User Stories:** US-11 (Comms Log), US-13 (Profil i statystyki), US-19 (Metryki kursu)

### Taski:
- [x] T1: Comms Log API — `GET /api/courses/{id}/comms-log` (paginowane max 100/page, filtry: quest_id, message_type, date_start, date_end), polling-friendly (test → kod → verify)
- [x] T2: Statistics API — `GET /api/users/me/stats` (test → kod → verify)
- [x] T3: Admin Analytics API — `GET /api/admin/analytics/{course_id}` (test → kod → verify)
- [x] T4: Frontend: Comms Log — `/comms` widok terminalowy (test → kod → verify)
- [x] T5: Frontend: Profil i statystyki — `/profile` z dashboardem (test → kod → verify)
- [x] T6: Frontend: Admin Analytics — `/admin/analytics` z wykresami (test → kod → verify)

### Security (MANDATORY):
- [x] S1: Data isolation — kursant widzi TYLKO swoje dane (Baseline #1)
- [x] S2: Pagination limits — max 100 records per page (Baseline #8)
- [x] S3: Test security: data isolation test (Baseline #1)
- [x] S4: Security event logging (Baseline #9)

### Docs (MANDATORY):
- [x] Update docs/CHANGELOG.md
- [x] Update docs/API.md
- [x] Update docs/README.md

### Stage Completion (MANDATORY):
- [x] Self-check: zakres stage zgodny z PRD (US-11, US-13, US-19 pokryte)
- [x] Self-check: brak hardcoded secrets w kodzie
- [x] Self-check: testy zielone (funkcjonalne + security)
- [x] Zaktualizuj HANDOFF: WSZYSTKIE checkboxy tego stage → [x]

---

## Stage 6: UX Polish i Landing Page
**Cel:** Dopracowanie wizualne, landing page, responsywność, micro-interactions, skeleton loaders, error states.
**User Stories:** Powiązane z Look & Feel z PRD

### Taski:
- [x] T1: Landing page — publiczna strona `/` z hero section, CTA, Framer Motion (test → kod → verify)
- [x] T2: Glassmorphism i karty — backdrop-blur, subtle borders, hover glow (test → kod → verify)
- [x] T3: Page transitions — Framer Motion AnimatePresence (test → kod → verify)
- [x] T4: Skeleton loaders (test → kod → verify)
- [x] T5: Error states — 404, 500, 403, toast notifications (sonner) (test → kod → verify)
- [x] T6: Responsywność — mobile sidebar, responsive grids (test → kod → verify)
- [x] T7: Quest node animations — glow, transitions, particle effects (test → kod → verify)
- [x] T8: Dark mode consistency — WCAG AA, focus states (test → kod → verify)

### Security (MANDATORY):
- [x] S1: CSP audit na stronach z dynamic content (Baseline #6)
- [x] S2: Accessibility + security — WCAG AA (Baseline #6)
- [x] S3: Test security: scan nagłówków (Baseline #6)

### Docs (MANDATORY):
- [x] Update docs/CHANGELOG.md
- [x] Update docs/README.md

### Stage Completion (MANDATORY):
- [x] Self-check: Look & Feel z PRD pokryte
- [x] Self-check: brak hardcoded secrets
- [x] Self-check: testy zielone
- [x] Zaktualizuj HANDOFF: WSZYSTKIE checkboxy → [x]

---

## Stage 7: Dopracowanie i Finalizacja
**Cel:** Smoke testy, security review, dokumentacja końcowa, deployment prep.
**User Stories:** Warstwa jakości i production-readiness.

### Taski:
- [ ] T1: Smoke testy e2e — Playwright (test → kod → verify)
- [ ] T2: Security audit — OWASP Top 10, secrets scan (test → kod → verify)
- [ ] T3: Code review i refactor (test → kod → verify)
- [ ] T4: Performance audit — Lighthouse, API load test, DB queries (test → kod → verify)
- [ ] T5: Dokumentacja finalna — SECURITY.md, ARCHITECTURE.md (test → kod → verify)
- [ ] T6: Deployment prep — Dockerfile, docker-compose.prod.yml, Caddyfile (test → kod → verify)
- [ ] T7: Health checks i monitoring (test → kod → verify)
- [ ] T8: docs/RUNBOOK.md (test → kod → verify)

### Security (MANDATORY):
- [ ] S1: Pełny security scan (PRD: threat model)
- [ ] S2: Penetration test (Baseline #1-9)
- [ ] S3: Secrets scan (Baseline #5)
- [ ] S4: CORS final check (Baseline #6)
- [ ] S5: Smoke test security (Baseline #1, #2, #8)

### Docs (MANDATORY):
- [ ] Create docs/SECURITY.md
- [ ] Create docs/ARCHITECTURE.md
- [ ] Create docs/PERFORMANCE.md
- [ ] Create docs/RUNBOOK.md
- [ ] Final update docs/CHANGELOG.md, API.md, README.md

### Stage Completion (MANDATORY):
- [ ] Self-check: WSZYSTKIE US z PRD pokryte
- [ ] Self-check: brak hardcoded secrets
- [ ] Self-check: testy zielone (funkcjonalne + security + e2e)
- [ ] Self-check: docs aktualne
- [ ] Zaktualizuj HANDOFF: WSZYSTKIE checkboxy → [x]
