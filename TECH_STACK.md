# TECH_STACK — NDQS Platform

## Stack Overview

| Warstwa | Technologia | Wersja |
|---------|------------|--------|
| **Frontend** | Next.js (App Router, TypeScript) | 15+ |
| **UI Components** | shadcn/ui + Radix UI | latest |
| **Styling** | Tailwind CSS 4 | 4.x |
| **Animacje** | Framer Motion | 11+ |
| **Quest Map** | React Flow | 12+ |
| **Charting** | Recharts | 2.x |
| **Backend** | FastAPI (Python) | 0.115+ |
| **ORM** | SQLAlchemy 2.0 (async) | 2.0+ |
| **Migracje** | Alembic | 1.13+ |
| **Baza danych** | PostgreSQL | 16+ |
| **Cache** | Redis | 7+ |
| **Auth (frontend)** | NextAuth.js (Auth.js v5) | 5.x |
| **Auth (API)** | JWT (python-jose) + API Keys (bcrypt) | — |
| **Password/Key Hashing** | passlib[bcrypt] | 1.7+ |
| **LLM Gateway** | OpenRouter API | — |
| **Walidacja** | Pydantic v2 | 2.x |
| **Rate Limiting** | slowapi (Redis backend) | 0.1+ |
| **Logging** | structlog | 24+ |
| **Testy (backend)** | pytest + pytest-asyncio + httpx | — |
| **Testy (frontend)** | Vitest + Testing Library + Playwright | — |
| **Validation (frontend)** | Zod | 3.x |
| **Konteneryzacja** | Docker + Docker Compose | — |
| **Reverse Proxy** | Caddy | 2.x |

---

## Uzasadnienie wyborów

### Backend: FastAPI (Python)

**Dlaczego:**
- Natywny async — kluczowy przy LLM API calls (OpenRouter) które trwają 5-15s
- Automatyczna dokumentacja OpenAPI/Swagger — kursanci i ich narzędzia AI widzą API docs
- Pydantic v2 natywnie — walidacja payloadów per quest type bez dodatkowych zależności
- Ekosystem Python: httpx (HTTP checks), jinja2 (template prompts), bcrypt (API keys)
- Szybki development, łatwy onboarding

**Rozważone alternatywy:**
- *Express/NestJS (Node.js)* — jeden język na front i back, ale brak natywnego async tak eleganckiego jak FastAPI, mniej czytelne type-hinting
- *Django* — za ciężki na API-first platform, ORM mniej elastyczny przy async
- *Go (Fiber/Echo)* — wydajniejszy, ale wolniejszy development, mniejszy ekosystem LLM

### Frontend: Next.js 15 (App Router)

**Dlaczego:**
- Server Components — SSR dla SEO i szybkości (landing page, katalog kursów)
- App Router — layout nesting (dashboard layout, admin layout)
- Middleware — auth guard na chronione ścieżki
- Natywna integracja z Auth.js v5 (NextAuth)
- Ekosystem React — React Flow (quest map), Framer Motion (animacje)

**Rozważone alternatywy:**
- *Vite + React SPA* — szybszy dev server, ale brak SSR, gorszy SEO
- *Remix* — dobry DX, ale mniejszy ekosystem komponentów
- *Astro* — idealny dla statycznych stron, za mało dla dynamic dashboard

### Baza danych: PostgreSQL

**Dlaczego:**
- JSONB — elastyczne payloady (quest submissions, LLM responses, failure states, evaluation criteria)
- Pełne wsparcie dla UUID primary keys
- Relacje + pełnotekstowe wyszukiwanie
- Sprawdzona skalowalność
- Natywne wsparcie w SQLAlchemy async

**Rozważone alternatywy:**
- *SQLite* — za prosty dla multi-user platform z concurrent writes
- *MongoDB* — schema-less = chaos w dłuższej perspektywie, brak relacji
- *Supabase (hosted PG)* — rozważamy jako hosting option, nie jako alternatywę dla PG

### Cache: Redis

**Dlaczego:**
- Cache sesji i rate limiting
- Tymczasowe przechowywanie wyników ewaluacji (czekanie na LLM response)
- Pub/sub dla przyszłych WebSocket updates
- Lekki, szybki, battle-tested

### LLM: OpenRouter

**Dlaczego:**
- Jeden endpoint, wielu providerów (Claude, GPT, Gemini, Mistral, open-source)
- Twórca kursu wybiera model per Game Master — Claude dla code review, GPT-4.1-mini dla quizów
- Fallback na inny model jeśli primary jest down
- Unified billing
- Zero vendor lock-in

### Auth: OAuth (GitHub/Google) + JWT + API Keys

**Dlaczego:**
- **OAuth:** Grupa docelowa to developerzy. GitHub login = 1 klik, zero friction.
- **JWT:** Stateless auth dla API requests z przeglądarki. Short-lived (15min) + refresh token.
- **API Keys:** Long-lived tokeny dla narzędzi CLI (Claude Code, Cursor). Hashowane bcrypt w DB. Prefixed (`ndqs_`) dla łatwej identyfikacji.

Dwa kanały auth, bo kursant wchodzi w interakcję z platformą na dwa sposoby: przeglądarka (OAuth → JWT) i terminal (API Key).

**Real-time (MVP):** Comms Log odświeżany przez polling (co 15-30s). WebSocket/SSE planowane post-MVP — polling wystarczający dla MVP i nie wymaga dodatkowej infrastruktury.

### LLM Gateway: OpenRouter

**Dlaczego:**
- Jeden endpoint, wielu providerów (Claude, GPT, Gemini, Mistral, open-source)
- Twórca kursu wybiera model per Game Master — Claude dla code review, GPT-4.1-mini dla quizów
- Fallback na inny model jeśli primary jest down
- Unified billing, zero vendor lock-in

**Integracja techniczna:**
- Client: `httpx` (AsyncClient) — brak dedykowanej SDK, REST API jest prosty
- Structured output: response_format JSON z Pydantic walidacją
- Retry: 3 attempts z exponential backoff (1s, 2s, 4s)
- Timeout: 30s per request
- Fallback: jeśli primary model zwróci error, retry z fallback model (konfigurowalny per kurs)
- Koszt: ~$0.01-0.05 per ewaluacja (zależy od modelu i długości promptu)

**Rozważone alternatywy:**
- *OpenAI SDK bezpośrednio* — vendor lock-in, brak dostępu do Claude/Gemini
- *Anthropic SDK bezpośrednio* — vendor lock-in, brak dostępu do GPT
- *LiteLLM* — dobra abstrakcja ale dodatkowa zależność, OpenRouter daje to samo przez REST

### Dodatkowe biblioteki backend

| Biblioteka | Użycie |
|-----------|--------|
| `httpx` | Async HTTP client — komunikacja z OpenRouter, HTTP checks (url_check evaluation) |
| `slowapi` | Rate limiting per endpoint, Redis backend, dekorator FastAPI |
| `passlib[bcrypt]` | Hashowanie API keys (bcrypt) |
| `structlog` | Structured JSON logging z correlation ID per request |
| `python-jose[cryptography]` | JWT encoding/decoding |
| `zipfile` (stdlib) | Generowanie Starter Pack ZIP w locie |
| `hmac` + `hashlib` (stdlib) | Signing artefaktów (anti-tamper) |

---

## Frontend Styling

### Framework CSS: Tailwind CSS 4

**Uzasadnienie (powiązanie z Look & Feel z PRD):**
PRD definiuje "Dark modern SaaS" z subtelnymi efektami. Tailwind 4 daje:
- Native CSS variables — łatwy dark/light mode i theming
- Utility-first — szybkie prototypowanie, spójny design system
- Doskonała integracja z shadcn/ui

### Component Library: shadcn/ui + Radix UI

**Uzasadnienie:**
- Unstyled (Radix) + customizable (shadcn) = pełna kontrola nad wyglądem
- Dostępność (accessibility) out-of-the-box
- Copy-paste model — komponenty są w repo, nie w node_modules. Pełna kontrola.
- Dark mode natywnie
- Zgodne z estetyką Linear/Vercel (PRD reference)

### Animacje: Framer Motion

**Uzasadnienie:**
PRD wymaga: page transitions, card hover effects, skeleton loaders, quest node pulsation. Framer Motion:
- Deklaratywne animacje (animate, exit, layout)
- AnimatePresence dla mount/unmount transitions
- Gesture support (drag, hover, tap)
- Integracja z React Flow (animated edges, node transitions)

### Quest Map: React Flow

**Uzasadnienie:**
Quest Map to serce UX kursanta. React Flow:
- Node graph z custom nodes (quest states: LOCKED, AVAILABLE, COMPLETED)
- Zoom, pan, minimap
- Animated edges
- Lightweight, performant do 50+ nodes
- Łatwy do użycia jako read-only preview w admin panel

### Fonty

| Użycie | Font | Dlaczego |
|--------|------|---------|
| UI (headings, body) | Geist Sans | Font Vercel — clean, modern, doskonała czytelność. Spójny z estetyką "dark modern SaaS" |
| Kod / terminal / fabuła | JetBrains Mono | Ligatures, doskonała czytelność kodu, terminal feel dla briefingów Game Mastera |

### Dodatkowe biblioteki frontend

| Biblioteka | Użycie |
|-----------|--------|
| Recharts | Radar chart (quality scores), bar chart (analytics), progress visualization |
| Zod | Runtime validation — form inputs, API response schemas |
| React Hook Form | Formularze (quest submit, admin CRUD) z Zod resolver |
| sonner | Toast notifications (success/error/info) |

### Paleta kolorów (orientacyjna)

| Rola | Kolor | Użycie |
|------|-------|--------|
| Background | `#0A0A0B` | Główne tło |
| Surface | `#141416` | Karty, panele |
| Surface elevated | `#1C1C1F` | Hover states, dropdowns |
| Border | `#2A2A2E` | Obramowania |
| Text primary | `#FAFAFA` | Główny tekst |
| Text secondary | `#A1A1AA` | Opisy, meta |
| Accent primary | `#6366F1` | Indigo — główny akcent (buttons, links) |
| Accent success | `#22C55E` | Quest completed, pass |
| Accent warning | `#F59E0B` | Failed attempt, hints |
| Accent danger | `#EF4444` | Errors, locked |
| Accent info | `#3B82F6` | In progress, available |

### Cover Images (kursy)

**MVP:** Admin podaje URL obrazka (np. z Unsplash, Cloudinary, własny hosting). Pole `cover_image_url` w formularzu kursu.
**Post-MVP:** Upload do S3/Cloudflare R2 z resize/optimization.
