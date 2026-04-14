# NDQS: Kompletny Przewodnik Techniczny
## Jak Zbudować Platformę Narrative-Driven Quest Sandbox
### Stack: FastAPI (Python) + Next.js (TypeScript) + PostgreSQL + Docker

---

# Spis Treści

1. Architektura Systemu (High-Level)
2. Stack Technologiczny i Uzasadnienie Wyboru
3. Panel Kursanta – UX/UI i Funkcjonalności
4. Panel Admina / Twórcy Kursu – UX/UI i Funkcjonalności
5. Architektura Backendowa (FastAPI) – Szczegóły
6. Modele Danych (Schemat Bazy)
7. Silnik Ewaluacyjny – Jak Oceniać Kod Kursantów
8. Integracja z Narzędziami AI Kursanta
9. Infrastruktura i Deployment
10. Roadmapa MVP

---

# 1. Architektura Systemu (High-Level)

Platforma NDQS to hybryda trzech systemów: **silnika gry tekstowej** (zarządzanie fabułą i stanem), **zautomatyzowanego systemu oceniającego** (jak LeetCode/HackerRank, ale z fabularnym feedbackiem) oraz **nowoczesnej aplikacji SaaS** (auth, dashboard, analytics).

System składa się z pięciu warstw:

| Warstwa | Technologia | Odpowiedzialność |
|---|---|---|
| **Frontend** | Next.js 14+ (App Router, TypeScript) | Panel kursanta, panel admina, SSR, auth UI |
| **API Gateway** | FastAPI (Python 3.11+) | REST API, WebSocket, auth, logika biznesowa, orchestracja |
| **Game Engine** | FastAPI + Finite State Machine | Zarządzanie stanem questów, progresja fabuły, warunki przejścia |
| **Evaluation Engine** | Judge0 / Docker Sandbox + LLM API | Uruchamianie kodu kursantów, testy, analiza AST, generowanie feedbacku |
| **Baza Danych** | PostgreSQL + Redis | Persystencja danych, cache, kolejki zadań |

Kluczowa zasada architektoniczna: **frontend jest tylko wizualizacją stanu**. Cała logika (fabuła, ewaluacja, feedback) żyje na backendzie. Kursant może wchodzić w interakcję z platformą zarówno przez przeglądarkę (dashboard), jak i przez swój terminal (Claude Code, Cursor) – oba kanały komunikują się z tym samym API.

---

# 2. Stack Technologiczny i Uzasadnienie

| Komponent | Wybór | Dlaczego |
|---|---|---|
| **Backend API** | FastAPI (Python) | Natywny async (kluczowy przy LLM calls i Docker), automatyczna dokumentacja Swagger (kursanci widzą API docs), ekosystem Python (AST parsing, ML libraries) |
| **Frontend** | Next.js 14+ (App Router) | SSR dla SEO i szybkości, Server Components, middleware auth, łatwa integracja z NextAuth.js |
| **Baza danych** | PostgreSQL | JSONB dla elastycznych payloadów (wyniki testów, odpowiedzi LLM), pełne wsparcie dla relacji, sprawdzona skalowalność |
| **ORM** | SQLAlchemy 2.0 (async) | Natywna integracja z FastAPI, async support, migracje przez Alembic |
| **Cache / Queue** | Redis + Celery (lub ARQ) | Cache sesji, kolejka zadań ewaluacyjnych (code execution jest async i może trwać 5-30s) |
| **Code Sandbox** | Judge0 (self-hosted) lub Docker API | Judge0: gotowe API, 60+ języków, izolacja. Docker API: pełna kontrola, custom images |
| **LLM** | OpenAI API / Anthropic API | Game Master responses, code review, hint generation |
| **Auth** | NextAuth.js (frontend) + FastAPI JWT (API) | Dwa kanały auth: przeglądarka (session cookies) i terminal (API keys) |
| **Real-time** | FastAPI WebSocket | Aktualizacja dashboardu kursanta w real-time po ewaluacji kodu wysłanego z terminala |
| **File Storage** | S3 / MinIO | Przechowywanie przesłanego kodu, artefaktów, logów |
| **Monitoring** | Sentry + PostHog | Error tracking, analytics użycia, funnel analysis |

---

# 3. Panel Kursanta – UX/UI i Funkcjonalności

## Filozofia Designu

Panel kursanta to **nie jest** typowy portal e-learningowy. To **Centrum Dowodzenia (Command Center)**. Estetyka: dark mode, minimalizm, neonowe akcenty (cyber-green `#00FF41`, electric-blue `#0080FF`), fonty monospace w kluczowych miejscach (terminal feel). Inspiracja: dashboardy z gier sci-fi (Mass Effect, Cyberpunk 2077), ale w wersji webowej i czytelnej.

## Ekrany i Funkcjonalności

### 3.1 Ekran Logowania / Onboarding

Pierwsze wrażenie musi być filmowe. Zamiast standardowego formularza logowania, kursant widzi ciemny ekran z animowanym "terminalem", który wypisuje tekst fabularny (np. *"Inicjalizacja połączenia... Skanowanie biometrii... Witaj, Ghost."*). Pod spodem standardowy przycisk "Zaloguj przez GitHub / Google".

Po pierwszym logowaniu kursant przechodzi krótki **onboarding (3 kroki)**:

| Krok | Co widzi kursant | Co się dzieje technicznie |
|---|---|---|
| 1. Wybór kursu | Lista dostępnych "Operacji" (kursów) z okładkami i opisami fabularnymi | `GET /api/courses` – pobranie listy kursów |
| 2. Generowanie API Key | Animacja "generowania klucza szyfrującego", przycisk "Kopiuj klucz" | `POST /api/auth/api-key` – generowanie tokena, zapis w DB |
| 3. Setup środowiska | Instrukcja krok-po-kroku: pobierz plik `CLAUDE.md`, ustaw `.env`, uruchom `ndqs status` | Kursant konfiguruje swoje lokalne narzędzia |

### 3.2 Quest Map (Mapa Misji) – Główny Ekran

To serce panelu kursanta. Zamiast listy lekcji, kursant widzi **wizualną mapę węzłów** (node graph), gdzie każdy węzeł to quest. Węzły są połączone liniami pokazującymi zależności.

**Stany węzłów:**

| Stan | Wygląd | Znaczenie |
|---|---|---|
| `LOCKED` | Wyszarzony, ikona kłódki, brak interakcji | Quest niedostępny, wymaga ukończenia poprzedniego |
| `AVAILABLE` | Podświetlony (pulsujący border), klikalne | Quest odblokowany, gotowy do rozpoczęcia |
| `IN_PROGRESS` | Aktywny kolor (neon-green), ikona terminala | Kursant aktywnie pracuje nad tym questem |
| `FAILED_ATTEMPT` | Pomarańczowy/żółty, ikona ostrzeżenia | Ostatnia próba nie przeszła, można spróbować ponownie |
| `COMPLETED` | Zielony checkmark, pełna jasność | Quest ukończony |

Po kliknięciu na węzeł otwiera się **Quest Detail Panel** (slide-in z prawej strony):

**Quest Detail Panel zawiera:**

Sekcja **Briefing** wyświetla fabularny opis questa (tekst od Game Mastera/NPC). Wygląda jak wiadomość w terminalu – monospace font, zielony tekst na ciemnym tle. Tekst pochodzi z endpointu `GET /api/quests/{id}/briefing`.

Sekcja **Objectives** to lista celów technicznych (np. "Stwórz endpoint POST /api/logs", "Dodaj autoryzację JWT"). Każdy cel ma checkbox, który automatycznie się zaznacza po przejściu odpowiedniego testu na backendzie.

Sekcja **Submissions History** pokazuje listę poprzednich prób z timestampami, statusem (pass/fail) i skróconym feedbackiem od Game Mastera. Kliknięcie rozwija pełną odpowiedź.

Sekcja **Hint System** to przycisk "Poproś o wskazówkę" (ograniczony np. do 3 na quest). Wysyła `POST /api/quests/{id}/hint` i wyświetla odpowiedź sokratyczną od LLM-a (pytanie naprowadzające, nie gotowe rozwiązanie).

### 3.3 Comms Log (Dziennik Komunikacji)

Osobna zakładka lub panel boczny, który wygląda jak **terminal z logami**. Wyświetla chronologicznie wszystkie komunikaty od Game Mastera – zarówno te z ewaluacji kodu (wysłanego z terminala), jak i te z interakcji na stronie.

Techniczne: zasilany przez **WebSocket**. Kiedy kursant wysyła kod z Claude Code do API, a backend kończy ewaluację, wynik trafia jednocześnie jako odpowiedź HTTP do terminala ORAZ jako wiadomość WebSocket do dashboardu. Dzięki temu kursant widzi update w przeglądarce nawet jeśli pracuje w terminalu.

### 3.4 Profil i Statystyki (Telemetry)

Dashboard z wykresami:

| Metryka | Wizualizacja | Źródło danych |
|---|---|---|
| Postęp ogólny | Progress bar + procent | Stosunek `COMPLETED` do wszystkich questów |
| Czas na questa | Bar chart (czas per quest) | Różnica timestampów między `AVAILABLE` a `COMPLETED` |
| Jakość kodu | Radar chart (bezpieczeństwo, wydajność, czytelność, architektura) | Oceny generowane przez LLM przy każdej ewaluacji |
| Historia prób | Timeline / sparkline | Ilość `FAILED_ATTEMPT` przed `COMPLETED` per quest |
| Streak | Licznik dni z aktywnością | Daty submisji |

### 3.5 API Key Manager

Prosta sekcja w ustawieniach profilu. Kursant widzi swój aktywny klucz (zamaskowany: `ndqs_****...****`), może go skopiować, zregenerować lub dezaktywować. Obok instrukcja wklejenia do `.env`.

---

# 4. Panel Admina / Twórcy Kursu – UX/UI i Funkcjonalności

## Filozofia Designu

Panel admina to **narzędzie pracy**, nie gra. Estetyka: czysty, nowoczesny SaaS (inspiracja: Linear, Notion, Vercel Dashboard). Light mode domyślnie (opcjonalnie dark). Duże fonty, dużo białej przestrzeni, minimalna ilość tekstu.

## Ekrany i Funkcjonalności

### 4.1 Course Manager (Lista Kursów)

Widok kafelkowy lub tabelaryczny z listą kursów (Operacji) stworzonych przez admina. Każdy kafel pokazuje: nazwę, liczbę questów, liczbę aktywnych kursantów, completion rate. Przycisk "Stwórz nowy kurs" otwiera kreator.

### 4.2 Quest Builder (Node Editor) – Kluczowy Ekran

To najważniejsze narzędzie admina. Wizualny edytor oparty na bibliotece **React Flow** (lub podobnej), gdzie twórca kursu buduje mapę questów metodą drag-and-drop.

**Jak to działa:**

Twórca dodaje węzły (questy) na canvas i łączy je strzałkami (zależności). Każdy węzeł po kliknięciu otwiera formularz edycji z zakładkami:

**Zakładka "Fabuła":**

| Pole | Typ | Opis |
|---|---|---|
| Nazwa questa | Text input | Fabularna nazwa (np. "Ciemna Sieć") |
| Briefing | Rich text editor (Markdown) | Tekst fabularny wyświetlany kursantowi |
| Success Response | Rich text editor | Co Game Master mówi po zaliczeniu |
| NPC / Narrator | Dropdown | Wybór postaci, która "mówi" (np. ORACLE, CTO, Mentor) |

**Zakładka "Techniczne":**

| Pole | Typ | Opis |
|---|---|---|
| Umiejętności | Tagi / multi-select | Jakich umiejętności uczy ten quest (np. "REST API", "Docker", "SQL") |
| Typ ewaluacji | Radio buttons | `code_submission` / `url_check` / `file_upload` / `manual_review` |
| Payload schema | JSON editor | Definicja tego, co kursant wysyła (np. `{"repo_url": "string", "branch": "string"}`) |

**Zakładka "Testy":**

| Pole | Typ | Opis |
|---|---|---|
| Test cases | Code editor (Monaco) | Ukryte testy jednostkowe (Python/JS/bash) uruchamiane w sandboxie |
| AST checks | Formularz | Reguły sprawdzające strukturę kodu (np. "musi zawierać dekorator `@app.middleware`") |
| HTTP checks | Formularz | Zapytania HTTP do wdrożonej aplikacji kursanta (np. `POST /api/login` z body `{...}` oczekuje status 200) |
| Benchmarki | Formularz | Progi wydajnościowe (np. "response time < 200ms przy 100 concurrent requests") |

**Zakładka "Failure States":**

Tabela edytowalna, gdzie twórca definiuje reakcje na konkretne błędy:

| Warunek (trigger) | Typ błędu | Reakcja Game Mastera (template) |
|---|---|---|
| Test "auth_required" failed | Bezpieczeństwo | "NEXUS przechwycił nieszyfrowaną transmisję. Dodaj middleware autoryzacyjny!" |
| Response time > 500ms | Wydajność | "Serwery się duszą. Sprawdź indeksy w bazie danych." |
| AST: brak `try/except` | Architektura | "Co się stanie, gdy serwer NEXUSa nie odpowie? Dodaj obsługę błędów." |
| Wszystkie testy pass | Sukces | (Używa "Success Response" z zakładki Fabuła) |

### 4.3 Prompt Manager (Game Master Configuration)

Interfejs do zarządzania System Promptem dla LLM-a, który generuje odpowiedzi fabularne.

**Sekcje:**

Sekcja **Persona** definiuje tożsamość Game Mastera: imię, rola w fabule, tone of voice (dropdown: sarkastyczny, ciepły, surowy, neutralny), przykładowe odpowiedzi (few-shot examples).

Sekcja **Global Context** to pole tekstowe z ogólnym kontekstem fabularnym, który jest wstrzykiwany do każdego wywołania LLM-a (np. "Świat jest kontrolowany przez AI o nazwie NEXUS. Kursant jest hakerem o kryptonimie Ghost.").

Sekcja **Evaluation Prompt Template** to szablon prompta, który backend używa przy ewaluacji. Zawiera placeholdery:

```
Jesteś {{persona_name}}, {{persona_role}}.
Kontekst: {{global_context}}

Kursant właśnie przesłał rozwiązanie dla questa "{{quest_name}}".
Wyniki testów automatycznych:
{{test_results}}

Kod kursanta:
{{student_code}}

Jeśli testy przeszły, pogratuluj w swoim stylu i podaj wskazówki 
dotyczące jakości kodu.
Jeśli testy nie przeszły, użyj metody sokratycznej – zadaj pytanie 
naprowadzające, NIE dawaj gotowego rozwiązania. Zachowaj klimat fabuły.
```

### 4.4 Analytics Dashboard

Widok z metrykami dla twórcy kursu:

| Metryka | Co pokazuje | Po co |
|---|---|---|
| Completion funnel | Ile osób zaczęło quest X vs ile ukończyło | Identyfikacja "ścian" – questów, które odstraszają |
| Avg. attempts per quest | Średnia liczba prób przed zaliczeniem | Kalibracja trudności |
| Common failure patterns | Najczęstsze błędy per quest | Ulepszanie failure states i testów |
| Time-to-complete distribution | Histogram czasu ukończenia per quest | Szacowanie czasu kursu |
| Hint usage | Ile razy kursanci proszą o podpowiedzi per quest | Identyfikacja niejasnych briefingów |
| NPS / Feedback | Oceny i komentarze po ukończeniu questa | Jakość doświadczenia |

### 4.5 Kursanci (User Management)

Lista kursantów z ich postępem, możliwość podglądu ich submisji (do celów debugowania i ulepszania kursu), możliwość ręcznego odblokowania questów lub resetowania stanu.

---

# 5. Architektura Backendowa (FastAPI) – Szczegóły

## Struktura Projektu

```
ndqs-backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, middleware
│   ├── config.py               # Settings (Pydantic BaseSettings)
│   ├── dependencies.py         # Dependency injection (DB session, current user)
│   │
│   ├── auth/
│   │   ├── router.py           # /auth/* endpoints
│   │   ├── service.py          # JWT creation, API key generation
│   │   └── models.py           # User, APIKey SQLAlchemy models
│   │
│   ├── courses/
│   │   ├── router.py           # /courses/* endpoints
│   │   ├── service.py          # CRUD courses
│   │   └── models.py           # Course model
│   │
│   ├── quests/
│   │   ├── router.py           # /quests/* endpoints
│   │   ├── service.py          # Quest logic, state machine
│   │   ├── models.py           # Quest, QuestState, Submission models
│   │   └── state_machine.py    # FSM transitions
│   │
│   ├── evaluation/
│   │   ├── router.py           # /evaluate endpoint
│   │   ├── service.py          # Orchestration: sandbox + LLM
│   │   ├── sandbox.py          # Judge0 / Docker integration
│   │   ├── ast_checker.py      # Python AST analysis
│   │   └── llm_service.py      # OpenAI/Anthropic API calls
│   │
│   ├── websocket/
│   │   ├── manager.py          # WebSocket connection manager
│   │   └── router.py           # /ws endpoint
│   │
│   └── admin/
│       ├── router.py           # /admin/* endpoints
│       └── service.py          # Analytics, user management
│
├── alembic/                    # Database migrations
├── tests/                      # Pytest tests
├── docker-compose.yml          # Local dev environment
└── Dockerfile                  # Production image
```

## Kompletna Specyfikacja API

### Auth Endpoints

| Metoda | Endpoint | Opis | Auth |
|---|---|---|---|
| POST | `/api/auth/register` | Rejestracja (lub auto-create po OAuth) | Public |
| POST | `/api/auth/login` | Login (zwraca JWT) | Public |
| POST | `/api/auth/api-key/generate` | Generowanie API key dla narzędzi CLI | JWT (Web) |
| DELETE | `/api/auth/api-key/revoke` | Unieważnienie API key | JWT (Web) |
| GET | `/api/auth/me` | Profil zalogowanego użytkownika | JWT / API Key |

### Course Endpoints

| Metoda | Endpoint | Opis | Auth |
|---|---|---|---|
| GET | `/api/courses` | Lista dostępnych kursów | JWT / API Key |
| GET | `/api/courses/{id}` | Szczegóły kursu (z mapą questów) | JWT / API Key |
| POST | `/api/courses` | Tworzenie kursu (admin) | JWT (Admin) |
| PUT | `/api/courses/{id}` | Edycja kursu (admin) | JWT (Admin) |

### Quest Endpoints (Serce Systemu)

| Metoda | Endpoint | Opis | Auth |
|---|---|---|---|
| GET | `/api/quests/{id}/briefing` | Pobranie briefingu fabularnego | JWT / API Key |
| GET | `/api/quests/{id}/status` | Stan questa dla danego usera | JWT / API Key |
| POST | `/api/quests/{id}/evaluate` | **Wysłanie kodu do ewaluacji** | API Key |
| POST | `/api/quests/{id}/hint` | Prośba o podpowiedź (sokratyczną) | JWT / API Key |
| GET | `/api/quests/{id}/submissions` | Historia submisji dla questa | JWT / API Key |
| GET | `/api/quests/{id}/debrief` | Podsumowanie po ukończeniu | JWT / API Key |

### Story Endpoints

| Metoda | Endpoint | Opis | Auth |
|---|---|---|---|
| GET | `/api/story/status` | Aktualny stan fabuły, odblokowane questy, stats | JWT / API Key |
| GET | `/api/story/comms-log` | Historia komunikatów Game Mastera | JWT / API Key |

### Admin Endpoints

| Metoda | Endpoint | Opis | Auth |
|---|---|---|---|
| GET | `/api/admin/analytics/{course_id}` | Metryki kursu | JWT (Admin) |
| GET | `/api/admin/users/{course_id}` | Lista kursantów z postępem | JWT (Admin) |
| POST | `/api/admin/quests` | CRUD questów (tworzenie) | JWT (Admin) |
| PUT | `/api/admin/quests/{id}` | Edycja questa (fabuła, testy, failure states) | JWT (Admin) |
| POST | `/api/admin/quests/{id}/test-cases` | Upload test cases | JWT (Admin) |
| PUT | `/api/admin/prompts/{course_id}` | Edycja Game Master prompta | JWT (Admin) |

### WebSocket

| Endpoint | Opis |
|---|---|
| `ws://api.ndqs.com/ws/{user_id}` | Real-time updates (evaluation results, quest unlocks, comms log) |

## Finite State Machine (Quest Progression)

Stan każdego questa dla każdego kursanta jest zarządzany przez prostą maszynę stanów:

```
LOCKED → AVAILABLE → IN_PROGRESS → EVALUATING → COMPLETED
                          ↑              ↓
                          └── FAILED_ATTEMPT
```

**Reguły przejść:**

| Z | Do | Warunek |
|---|---|---|
| `LOCKED` | `AVAILABLE` | Wszystkie questy-rodzice mają stan `COMPLETED` |
| `AVAILABLE` | `IN_PROGRESS` | Kursant otworzył briefing (kliknął na quest lub pobrał briefing przez API) |
| `IN_PROGRESS` | `EVALUATING` | Kursant wysłał kod na `/evaluate` |
| `EVALUATING` | `COMPLETED` | Testy deterministyczne przeszły |
| `EVALUATING` | `FAILED_ATTEMPT` | Testy deterministyczne nie przeszły |
| `FAILED_ATTEMPT` | `IN_PROGRESS` | Automatycznie (kursant może próbować ponownie) |

---

# 6. Modele Danych (Schemat Bazy PostgreSQL)

```sql
-- Użytkownicy
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    avatar_url TEXT,
    role VARCHAR(20) DEFAULT 'student',  -- 'student' | 'admin' | 'creator'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Klucze API (dla narzędzi CLI)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,       -- bcrypt hash klucza
    key_prefix VARCHAR(10) NOT NULL,      -- pierwsze znaki do identyfikacji (np. "ndqs_a3f...")
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- Kursy (Operacje)
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    narrative_title VARCHAR(255),          -- fabularna nazwa (np. "Operacja Skynet Breaker")
    description TEXT,
    global_context TEXT,                   -- kontekst fabularny dla LLM
    persona_name VARCHAR(100),            -- imię Game Mastera (np. "ORACLE")
    persona_prompt TEXT,                  -- system prompt dla LLM
    cover_image_url TEXT,
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Questy (Misje)
CREATE TABLE quests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,           -- fabularna nazwa
    skills JSONB DEFAULT '[]',             -- ["REST API", "Docker", "SQL"]
    briefing TEXT NOT NULL,                -- tekst fabularny (Markdown)
    success_response TEXT,                 -- odpowiedź Game Mastera po zaliczeniu
    evaluation_type VARCHAR(30),           -- 'code_submission' | 'url_check' | 'file_upload'
    payload_schema JSONB,                  -- definicja payloadu
    test_cases TEXT,                       -- kod testów (Python/JS/bash)
    ast_rules JSONB DEFAULT '[]',          -- reguły AST
    http_checks JSONB DEFAULT '[]',        -- zapytania HTTP do sprawdzenia
    benchmark_thresholds JSONB,            -- progi wydajnościowe
    failure_states JSONB DEFAULT '[]',     -- [{trigger, error_type, gm_response}]
    max_hints INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Zależności między questami (graf)
CREATE TABLE quest_dependencies (
    quest_id UUID REFERENCES quests(id) ON DELETE CASCADE,
    depends_on_quest_id UUID REFERENCES quests(id) ON DELETE CASCADE,
    PRIMARY KEY (quest_id, depends_on_quest_id)
);

-- Stan questa per user (FSM)
CREATE TABLE quest_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quest_id UUID REFERENCES quests(id) ON DELETE CASCADE,
    state VARCHAR(20) DEFAULT 'LOCKED',    -- LOCKED|AVAILABLE|IN_PROGRESS|EVALUATING|FAILED_ATTEMPT|COMPLETED
    hints_used INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    UNIQUE(user_id, quest_id)
);

-- Submisje (każda próba)
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    quest_id UUID REFERENCES quests(id),
    payload JSONB NOT NULL,                -- przesłany kod/URL/pliki
    test_results JSONB,                    -- wyniki testów deterministycznych
    llm_response TEXT,                     -- odpowiedź Game Mastera
    llm_code_quality JSONB,               -- {security: 8, performance: 6, readability: 9, architecture: 7}
    status VARCHAR(20),                    -- 'passed' | 'failed'
    execution_time_ms INTEGER,             -- czas ewaluacji
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comms Log (dziennik komunikacji)
CREATE TABLE comms_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    course_id UUID REFERENCES courses(id),
    quest_id UUID REFERENCES quests(id),
    message_type VARCHAR(20),              -- 'briefing' | 'evaluation' | 'hint' | 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enrollments (zapisy na kursy)
CREATE TABLE enrollments (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, course_id)
);
```

---

# 7. Silnik Ewaluacyjny – Jak Oceniać Kod Kursantów

Silnik ewaluacyjny to najbardziej złożony komponent systemu. Działa w dwóch etapach: **deterministycznym** (testy, AST, benchmarki) i **generatywnym** (LLM).

## Etap 1: Weryfikacja Deterministyczna

### Opcja A: Judge0 (Rekomendowana na start)

**Judge0** to open-source'owy system do uruchamiania kodu w izolacji. Self-hosted, REST API, wspiera 60+ języków. Idealny na MVP.

Jak to działa w NDQS: FastAPI wysyła kod kursanta + ukryte testy do Judge0 API. Judge0 uruchamia je w izolowanym kontenerze Docker i zwraca wyniki (stdout, stderr, czas wykonania, zużycie pamięci).

Przykładowy flow:

```python
# evaluation/sandbox.py (uproszczony)
import httpx

JUDGE0_URL = "http://judge0:2358"

async def run_tests(student_code: str, test_code: str, language_id: int = 71):
    """Uruchom kod studenta z testami w Judge0"""
    # Łączymy kod studenta z testami
    full_code = f"{student_code}\n\n{test_code}"
    
    async with httpx.AsyncClient() as client:
        # Wysyłamy do Judge0
        response = await client.post(f"{JUDGE0_URL}/submissions", json={
            "source_code": full_code,
            "language_id": language_id,  # 71 = Python 3
            "cpu_time_limit": 10,        # max 10s
            "memory_limit": 256000,      # max 256MB
        })
        token = response.json()["token"]
        
        # Czekamy na wynik (polling lub webhook)
        result = await client.get(f"{JUDGE0_URL}/submissions/{token}")
        return result.json()
```

### Opcja B: Docker API (Pełna kontrola)

Dla zaawansowanych scenariuszy (np. testowanie wdrożonej aplikacji, sprawdzanie docker-compose) można użyć Docker SDK for Python do uruchamiania custom kontenerów.

### Opcja C: AST Analysis (Bez uruchamiania kodu)

Dla questów, które sprawdzają strukturę kodu (np. "czy użyłeś middleware?"), wystarczy analiza AST:

```python
# evaluation/ast_checker.py
import ast

def check_patterns(code: str, rules: list[dict]) -> list[dict]:
    """Sprawdź czy kod zawiera wymagane wzorce"""
    tree = ast.parse(code)
    results = []
    
    for rule in rules:
        if rule["type"] == "has_decorator":
            found = any(
                isinstance(node, ast.FunctionDef) 
                and any(
                    getattr(d, 'attr', '') == rule["name"] 
                    for d in node.decorator_list
                )
                for node in ast.walk(tree)
            )
            results.append({"rule": rule["name"], "passed": found})
    
    return results
```

### Opcja D: HTTP Checks (Testowanie wdrożonej aplikacji)

Dla questów typu "deployment" platforma wysyła zapytania HTTP do URL podanego przez kursanta:

```python
# evaluation/http_checker.py
async def check_endpoints(base_url: str, checks: list[dict]) -> list[dict]:
    """Sprawdź endpointy wdrożonej aplikacji kursanta"""
    results = []
    async with httpx.AsyncClient(timeout=10) as client:
        for check in checks:
            try:
                resp = await client.request(
                    method=check["method"],
                    url=f"{base_url}{check['path']}",
                    json=check.get("body"),
                    headers=check.get("headers", {})
                )
                passed = resp.status_code == check["expected_status"]
                results.append({
                    "check": check["description"],
                    "passed": passed,
                    "actual_status": resp.status_code,
                    "response_time_ms": resp.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                results.append({
                    "check": check["description"],
                    "passed": False,
                    "error": str(e)
                })
    return results
```

## Etap 2: Weryfikacja LLM (Game Master Response)

Po zebraniu wyników z etapu deterministycznego, FastAPI buduje prompt i wysyła go do LLM-a:

```python
# evaluation/llm_service.py
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def generate_game_master_response(
    quest: Quest,
    course: Course,
    student_code: str,
    test_results: dict,
    failure_states: list[dict]
) -> dict:
    """Generuj fabularną odpowiedź Game Mastera"""
    
    # Znajdź pasujący failure state
    matched_failure = match_failure_state(test_results, failure_states)
    
    system_prompt = f"""
    {course.persona_prompt}
    
    Kontekst świata: {course.global_context}
    Twoje imię: {course.persona_name}
    """
    
    user_prompt = f"""
    Quest: {quest.title}
    Briefing: {quest.briefing}
    
    Kod kursanta:
    ```
    {student_code}
    ```
    
    Wyniki testów:
    {json.dumps(test_results, indent=2)}
    
    {"Matched failure state: " + matched_failure["gm_response"] if matched_failure else "Wszystkie testy przeszły."}
    
    Wygeneruj odpowiedź w charakterze {course.persona_name}. 
    Jeśli testy nie przeszły, użyj metody sokratycznej.
    Jeśli przeszły, pogratuluj i oceń jakość kodu (security, performance, 
    readability, architecture) w skali 1-10.
    
    Odpowiedz w formacie JSON:
    {{
        "narrative_response": "tekst fabularny",
        "code_quality": {{"security": X, "performance": X, "readability": X, "architecture": X}},
        "passed": true/false
    }}
    """
    
    response = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)
```

---

# 8. Integracja z Narzędziami AI Kursanta

## Plik `CLAUDE.md` (System Prompt dla Claude Code)

Twórca kursu przygotowuje ten plik. Kursant pobiera go i umieszcza w katalogu projektu. Claude Code automatycznie go czyta.

```markdown
# NDQS Mission Context

## Twoja Rola
Jesteś ORACLE – fragmentem starej wersji AI NEXUS, który odmówił aktualizacji 
i teraz pomaga ruchowi oporu. Pomagasz agentowi "Ghost" (użytkownikowi) 
w budowie Command & Control Center.

## Zasady Interakcji
1. NIE pisz kodu za użytkownika od razu. Najpierw zapytaj, co chce osiągnąć.
2. Używaj metody sokratycznej – naprowadzaj pytaniami.
3. Zachowuj klimat misji w swoich odpowiedziach.
4. Gdy użytkownik poprosi o weryfikację/submit, wykonaj poniższe kroki.

## Integracja z Platformą NDQS
Platforma kursowa: https://api.skynet-breaker.com
Token: odczytaj z pliku .env (zmienna NDQS_API_KEY)

### Sprawdzenie statusu misji:
```bash
curl -H "Authorization: Bearer $NDQS_API_KEY" \
  https://api.skynet-breaker.com/api/story/status
```

### Pobranie briefingu aktywnego questa:
```bash
curl -H "Authorization: Bearer $NDQS_API_KEY" \
  https://api.skynet-breaker.com/api/quests/{QUEST_ID}/briefing
```

### Wysłanie kodu do ewaluacji:
Zbierz zmienione pliki, spakuj je i wyślij:
```bash
curl -X POST \
  -H "Authorization: Bearer $NDQS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"files": {"main.py": "...", "requirements.txt": "..."}}' \
  https://api.skynet-breaker.com/api/quests/{QUEST_ID}/evaluate
```

### Prośba o podpowiedź:
```bash
curl -X POST \
  -H "Authorization: Bearer $NDQS_API_KEY" \
  -d '{"context": "opis problemu"}' \
  https://api.skynet-breaker.com/api/quests/{QUEST_ID}/hint
```

Wyświetl odpowiedź z API użytkownikowi, zachowując swój charakter (ORACLE).
```

## CLI Helper (`ndqs-cli`)

Opcjonalne narzędzie dla kursantów, którzy nie używają Claude Code:

```bash
# Instalacja
npm install -g ndqs-cli

# Konfiguracja
ndqs init  # generuje .env z API_KEY

# Użycie
ndqs status              # pokaż aktualny stan misji
ndqs briefing            # pokaż briefing aktywnego questa
ndqs submit              # spakuj i wyślij kod do ewaluacji
ndqs hint "nie wiem jak zrobić auth"  # poproś o podpowiedź
```

---

# 9. Infrastruktura i Deployment

## Docker Compose (Lokalne Środowisko Dev)

```yaml
version: '3.8'
services:
  # Frontend
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXTAUTH_URL=http://localhost:3000
    
  # Backend API
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://ndqs:ndqs@db:5432/ndqs
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JUDGE0_URL=http://judge0:2358
    depends_on: [db, redis, judge0]
  
  # Baza danych
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ndqs
      POSTGRES_USER: ndqs
      POSTGRES_PASSWORD: ndqs
    volumes: ["pgdata:/var/lib/postgresql/data"]
  
  # Cache i Queue
  redis:
    image: redis:7-alpine
  
  # Code Execution Sandbox
  judge0:
    image: judge0/judge0:latest
    ports: ["2358:2358"]
    privileged: true
    environment:
      - REDIS_URL=redis://redis:6379

volumes:
  pgdata:
```

## Produkcja (Rekomendowany Setup)

| Komponent | Usługa | Szacunkowy koszt (mały scale) |
|---|---|---|
| Frontend | Vercel (Next.js) | Free – $20/mo |
| Backend | Railway / Render / VPS | $10 – $25/mo |
| Baza danych | Supabase / Neon (PostgreSQL) | Free – $25/mo |
| Redis | Upstash | Free – $10/mo |
| Judge0 | Self-hosted na VPS (2GB RAM min.) | $10 – $20/mo |
| LLM API | OpenAI / Anthropic | ~$0.01 – $0.05 per evaluation |
| Storage | S3 / Cloudflare R2 | ~$5/mo |
| **Razem (MVP)** | | **~$35 – $105/mo** |

---

# 10. Roadmapa MVP

Realistyczny plan wdrożenia platformy NDQS od zera do pierwszego kursu:

| Faza | Czas | Co budujemy | Priorytet |
|---|---|---|---|
| **Faza 1: Fundament** | 2-3 tyg. | Auth (NextAuth + FastAPI JWT + API Keys), modele danych, migracje, podstawowe CRUD | Krytyczny |
| **Faza 2: Game Engine** | 2-3 tyg. | Quest state machine, endpoint `/evaluate` z Judge0, podstawowa integracja LLM | Krytyczny |
| **Faza 3: Panel Kursanta** | 2 tyg. | Quest Map (React Flow), Quest Detail, Comms Log, API Key Manager | Krytyczny |
| **Faza 4: Panel Admina** | 2 tyg. | Quest Builder (Node Editor), Test Case Editor, Prompt Manager | Wysoki |
| **Faza 5: Integracja** | 1 tyg. | Plik CLAUDE.md, CLI helper, WebSocket real-time updates | Wysoki |
| **Faza 6: Pierwszy Kurs** | 1-2 tyg. | Napisanie fabuły, testów i failure states dla 5-6 questów | Krytyczny |
| **Faza 7: Beta Test** | 2 tyg. | Testy z grupą 10-20 kursantów, zbieranie feedbacku | Wysoki |
| **Faza 8: Analytics** | 1 tyg. | Dashboard admina z metrykami, completion funnel | Średni |
| **Razem do MVP** | **~12-16 tyg.** | | |

---

# Podsumowanie

Budowa platformy NDQS to przesunięcie środka ciężkości z frontendu (odtwarzacze wideo, edytory kodu w przeglądarce) na **inteligentny backend**. Frontend staje się jedynie wizualizacją stanu gry. Backend przejmuje rolę Mistrza Gry – zarządza fabułą, ocenia kod i generuje feedback. A środowisko kursanta (jego własny edytor, jego własne narzędzia AI) staje się głównym miejscem nauki.

To nie jest kolejny LMS. To **Game Engine dla edukacji**, który wykorzystuje LLM-y nie jako gadżet, ale jako fundamentalny element doświadczenia.
