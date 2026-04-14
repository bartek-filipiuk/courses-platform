# PRD — NDQS (Narrative-Driven Quest Sandbox)

## Wizja projektu

NDQS to platforma kursowa nowej generacji, w której kursy IT są opakowane w narrację fabularną. Zamiast lekcji — questy. Zamiast ocen — artefakty fabularne. Zamiast checkboxów — maszyna stanów z progresją narracyjną.

Kursant pracuje w **swoim własnym środowisku** (VS Code, Claude Code, Cursor) i komunikuje się z platformą przez API. Po stronie platformy LLM pełni rolę **Game Mastera** — weryfikuje odpowiedzi, generuje fabularny feedback i naprowadza metodą sokratyczną.

Platforma **nie uruchamia kodu kursanta**. Weryfikuje efekty jego pracy: odpowiedzi tekstowe, URL-e wdrożonych aplikacji, screenshoty, outputy komend, quizy.

### Cele biznesowe

1. Zbudować MVP platformy, na której można uruchomić pierwszy kurs fabularny.
2. Osiągnąć completion rate >50% (vs ~15-20% w tradycyjnych kursach).
3. Stworzyć system, który jest **agent-friendly** — łatwy do rozbudowy zarówno przez ludzi, jak i AI.

---

## Framework NDQS — 4 Filary

Platforma implementuje model **Narrative-Driven Quest Sandbox** oparty na 4 filarach:

1. **Worldbuilding** — Każdy kurs definiuje spójny świat fabularny: rolę kursanta, antagonistę, stawkę. Fabuła wynika z technologii, nie odwrotnie.
2. **Dekonstrukcja Sylabusa** — Tradycyjne "lekcje" są przekształcane w questy z fabularnym kontekstem. Każdy quest odpowiada konkretnemu modułowi technicznemu.
3. **Failure States** — Błędy kursanta to zwroty akcji w fabule, nie frustracja. Twórca kursu definiuje fabularne reakcje na konkretne typy błędów.
4. **Architektura Techniczna** — 4 warstwy: Panel Kursanta (frontend), Game Master API (backend), Silnik Ewaluacyjny (LLM + deterministic checks), Integracja z narzędziami kursanta (CLAUDE.md, Starter Pack).

Szczegółowa dokumentacja frameworka: `docs-init/Narrative-Driven Quest Sandbox (NDQS)`.

---

## Architektura Systemu — Flow End-to-End

### Ścieżka kursanta

```
1. REJESTRACJA
   Kursant loguje się przez OAuth (GitHub/Google)
   → tworzony jest profil w DB (role: student)
   → kursant trafia na dashboard

2. WYBÓR KURSU
   Kursant przegląda katalog kursów (GET /api/courses)
   → widzi karty "Mission Briefs" z opisami fabularnymi
   → klika "Przyjmij Misję" (POST /api/courses/{id}/enroll)
   → backend tworzy enrollment + inicjalizuje quest_states:
     - pierwszy quest → AVAILABLE
     - reszta → LOCKED (do momentu zdobycia wymaganych artefaktów)

3. STARTER PACK
   Kursant pobiera ZIP (GET /api/courses/{id}/starter-pack)
   → zawiera: CLAUDE.md (system prompt Game Mastera), .env.example, README
   → kursant rozpakowuje ZIP w katalogu projektu
   → jego narzędzie AI (Claude Code/Cursor) czyta CLAUDE.md i "wie" w jakim kontekście fabularnym pracuje

4. QUEST MAP
   Kursant widzi wizualną mapę questów (node graph, React Flow)
   → węzły w stanach: LOCKED (szary) / AVAILABLE (pulsujący) / IN_PROGRESS / COMPLETED (zielony) / FAILED_ATTEMPT (pomarańczowy)
   → klika na AVAILABLE quest → otwiera się Quest Detail Panel

5. BRIEFING
   Kursant czyta briefing questa (fabularny opis zadania, styl: terminal)
   → quest przechodzi do stanu IN_PROGRESS
   → briefing dostępny też przez API (GET /api/quests/{id}/briefing) dla narzędzia AI

6. PRACA NAD QUESTEM
   Kursant koduje w swoim IDE ze swoim agentem AI
   → agent AI komunikuje się z platformą przez API Key
   → kursant może poprosić o podpowiedź (POST /api/quests/{id}/hint)
     → LLM generuje pytanie sokratyczne (nie gotową odpowiedź)
     → zużywa 1 z limitu hintów, obniża quality score

7. SUBMIT
   Kursant wysyła odpowiedź (POST /api/quests/{id}/submit)
   → payload zależy od evaluation_type questa (tekst, URL, quiz, command output)
   → quest przechodzi do stanu EVALUATING

8. EWALUACJA (Pipeline)
   Backend przetwarza odpowiedź w 3 krokach:
   a) SANITYZACJA — Pydantic walidacja + input sanitization
   b) DETERMINISTIC CHECK — jeśli dotyczy: quiz key matching, URL HTTP check, regex pattern
   c) LLM JUDGE — OpenRouter: odpowiedź + kryteria twórcy → structured JSON {passed, narrative, quality_scores}

9. FEEDBACK
   Game Master odpowiada fabularnie:
   → PASS: artefakt przyznany + narrative success response + quality scores
   → FAIL: narrative failure response (sokratyczny feedback) + quest → FAILED_ATTEMPT → IN_PROGRESS
   → odpowiedź zapisana w comms_log i submissions

10. ARTEFAKT I UNLOCK
    Po PASS: backend mintuje artefakt (signed token + nazwa fabularna)
    → artefakt zapisany w user_artifacts
    → backend sprawdza: "które questy wymagają tego artefaktu?"
    → jeśli user ma WSZYSTKIE required_artifacts danego questa → quest → AVAILABLE
    → kursant widzi nowy artefakt w Inventory + odblokowany quest na mapie
```

### Ścieżka twórcy kursu (admin)

```
1. Tworzy kurs: tytuł, opis fabularny, kontekst świata, persona Game Mastera, model LLM (OpenRouter)
2. Dodaje questy: briefing, typ ewaluacji, kryteria, failure states, reward artifact, required artifacts
3. Definiuje artefakty: nazwa fabularna, opis, ikona — przypisuje do questów jako reward/requirement
4. Podgląda quest map (React Flow, read-only) — weryfikuje flow zależności
5. Publikuje kurs → widoczny w katalogu
```

---

## System Artefaktów

### Czym jest artefakt?

Artefakt to **fabularna nagroda za zaliczenie questa**. Pełni 3 funkcje:
- **Unlock mechanism** — quest B wymaga artefaktu A → B jest LOCKED dopóki kursant nie zdobędzie A
- **Narratywa** — artefakt ma fabularną nazwę i opis (np. "Klucz szyfrujący NEXUS-7F3A")
- **Progresja** — kursant widzi zdobyte artefakty w Inventory (jak ekwipunek w grze)

### Model danych

```
artifact_definitions (template artefaktu — definiowany przez twórcę kursu)
├── id: UUID
├── course_id: UUID (FK → courses)
├── quest_id: UUID (FK → quests) — quest który daje ten artefakt (1:1)
├── name: VARCHAR(255) — nazwa fabularna (np. "Klucz NEXUS-7F3A")
├── description: TEXT — opis fabularny
├── icon_url: TEXT (opcjonalnie)
└── created_at: TIMESTAMPTZ

user_artifacts (instancja artefaktu — przyznawana po PASS)
├── id: UUID
├── user_id: UUID (FK → users)
├── artifact_definition_id: UUID (FK → artifact_definitions)
├── acquired_at: TIMESTAMPTZ
└── signature: VARCHAR(255) — signed hash (anti-tamper)

quests.required_artifact_ids: UUID[] — lista artefaktów wymaganych do odblokowania questa
```

### Relacje

- Quest → Artifact Definition: **1:1** (każdy quest może dawać max 1 artefakt)
- Quest → Required Artifacts: **N:N** (quest może wymagać wielu artefaktów z różnych questów)
- User → Artifacts: **1:N** (user kolekcjonuje artefakty)

### Lifecycle

1. **Definicja** — twórca kursu tworzy artifact_definition i przypisuje do questa (reward) lub jako requirement innego questa
2. **Mintowanie** — po PASS: backend tworzy user_artifact z podpisem (HMAC SHA256 z user_id + artifact_id + secret)
3. **Sprawdzanie** — przy sprawdzaniu czy quest jest AVAILABLE: backend weryfikuje "czy user ma WSZYSTKIE required_artifact_ids tego questa w user_artifacts?"
4. **Anti-cheat** — artefakty generowane server-side, podpis weryfikowalny, user nie może podrobić artefaktu

### Przykład

```
Quest 1: "Zaprojektuj architekturę API"
  → reward: Artifact "BLUEPRINT-8K2F" ("Schemat sieci NEXUS")

Quest 2: "Zbuduj backend API"
  → required_artifacts: ["BLUEPRINT-8K2F"]
  → reward: Artifact "ACCESS-TOKEN-X9" ("Klucz dostępu do węzła")

Quest 3: "Stwórz dashboard"
  → required_artifacts: ["ACCESS-TOKEN-X9"]
  → reward: Artifact "COMM-LINK-Z1"

Quest 4: "Wdróż system" (finał)
  → required_artifacts: ["ACCESS-TOKEN-X9", "COMM-LINK-Z1"]  ← wymaga dwóch!
  → reward: Artifact "SKYNET-KILL-SWITCH"
```

---

## Pipeline Ewaluacji

### 4 typy ewaluacji

| Typ | Co kursant wysyła | Deterministic check | LLM Judge |
|-----|-------------------|--------------------:|----------:|
| `text_answer` | Tekst (max 5000 znaków) | — | Tak (vs kryteria twórcy) |
| `url_check` | URL endpointu/deployu (max 500 znaków) | HTTP GET/POST → status + body check | Opcjonalnie (ocena jakości) |
| `quiz` | ID wybranej odpowiedzi | Key matching (deterministycznie) | — |
| `command_output` | Output z terminala (max 10000 znaków) | Regex/pattern matching | Tak (interpretacja wyniku) |

### Flow per typ

```
         ┌─────────────────────────────────────────────────┐
         │  POST /api/quests/{id}/submit                   │
         │  {type: "text_answer", payload: "..."}          │
         └──────────────────┬──────────────────────────────┘
                            ↓
         ┌─────────────────────────────────────────────────┐
         │  WARSTWA 1: Sanityzacja                         │
         │  • Pydantic schema per evaluation_type          │
         │  • Input size limits                            │
         │  • HTML/script sanitization                     │
         │  • Rate limit check (5 submisji/quest/h)        │
         └──────────────────┬──────────────────────────────┘
                            ↓
         ┌─────────────────────────────────────────────────┐
         │  WARSTWA 2: Deterministic Check (jeśli dotyczy) │
         │                                                 │
         │  quiz → key matching → PASS/FAIL (koniec)       │
         │  url_check → httpx GET → status/body check      │
         │  command_output → regex pattern matching         │
         │  text_answer → (skip, idź do LLM)               │
         └──────────────────┬──────────────────────────────┘
                            ↓
         ┌─────────────────────────────────────────────────┐
         │  WARSTWA 3: LLM Judge (OpenRouter)              │
         │                                                 │
         │  Input: odpowiedź + evaluation_criteria          │
         │         + failure_states + deterministic results │
         │  Output (structured JSON):                      │
         │  {                                              │
         │    "passed": true/false,                        │
         │    "narrative_response": "tekst fabularny",     │
         │    "quality_scores": {                          │
         │      "completeness": 8,                        │
         │      "understanding": 7,                       │
         │      "efficiency": 9,                          │
         │      "creativity": 6                           │
         │    },                                           │
         │    "matched_failure": "failure_state_id"|null   │
         │  }                                              │
         │                                                 │
         │  Retry: 3 attempts, timeout: 30s                │
         │  Fallback: "Ewaluacja trwa dłużej niż zwykle.  │
         │  Spróbuj ponownie za chwilę."                   │
         └──────────────────┬──────────────────────────────┘
                            ↓
         ┌─────────────────────────────────────────────────┐
         │  WARSTWA 4: Result                              │
         │                                                 │
         │  PASS → mint artifact → update quest_state      │
         │         → check dependent quests → unlock       │
         │         → save to submissions + comms_log       │
         │                                                 │
         │  FAIL → quest → FAILED_ATTEMPT → IN_PROGRESS   │
         │         → save to submissions + comms_log       │
         └─────────────────────────────────────────────────┘
```

### Payload examples per typ

```json
// text_answer
{"type": "text_answer", "payload": {"answer": "Wybrałem FastAPI + PostgreSQL, bo..."}}

// url_check
{"type": "url_check", "payload": {"url": "https://my-app.railway.app/api/health"}}

// quiz
{"type": "quiz", "payload": {"selected_option_id": "opt_3"}}

// command_output
{"type": "command_output", "payload": {"command": "docker ps", "output": "CONTAINER ID  IMAGE..."}}
```

---

## Quality Score

### Definicja

Quality Score to ocena jakości odpowiedzi kursanta per quest. Składa się z dwóch komponentów:

**Komponent LLM (przy PASS):**
LLM Judge ocenia odpowiedź w 4 wymiarach, skala 1-10:
- **completeness** — czy odpowiedź pokrywa wszystkie wymagania questa
- **understanding** — czy kursant rozumie temat (nie kopiuje bezmyślnie)
- **efficiency** — czy rozwiązanie jest optymalne/eleganckie
- **creativity** — czy kursant wykracza poza minimum

**Komponent deterministyczny (zawsze):**
- **attempts** — ile prób do zaliczenia (mniej = lepiej)
- **hints_used** — ile podpowiedzi zużytych (mniej = lepiej, -1 punkt per hint)
- **time_taken** — czas od IN_PROGRESS do COMPLETED

### Radar chart

Profil kursanta wyświetla radar chart z 4 wymiarami LLM (średnia per kurs) + pasek z attempts/hints/time.

### Hint penalty

Każdy użyty hint obniża `completeness` score o 1 punkt (min 1). To zachęca do samodzielnego myślenia.

---

## Failure States — format i przykłady

Twórca kursu definiuje failure_states per quest jako JSONB array. Każdy failure state to trigger + reakcja Game Mastera:

```json
[
  {
    "id": "fs_no_auth",
    "trigger": {
      "type": "http_check_failed",
      "condition": "status_code == 401 OR missing_header('Authorization')"
    },
    "error_category": "security",
    "gm_response": "NEXUS przechwycił nieszyfrowaną transmisję! Twój endpoint jest otwarty dla każdego. Dodaj middleware autoryzacyjny, zanim stracimy wszystkich agentów."
  },
  {
    "id": "fs_slow_response",
    "trigger": {
      "type": "http_check_failed",
      "condition": "response_time_ms > 500"
    },
    "error_category": "performance",
    "gm_response": "Serwer odpowiada zbyt wolno — 500ms to wieczność, gdy NEXUS skanuje co 100ms. Sprawdź indeksy w bazie danych."
  },
  {
    "id": "fs_wrong_format",
    "trigger": {
      "type": "llm_judge",
      "condition": "answer_does_not_match_criteria"
    },
    "error_category": "logic",
    "gm_response": "Hmm, Ghost — Twój plan ma luki. Pomyśl jeszcze raz: jaki protokół zapewni szyfrowanie end-to-end?"
  }
]
```

Jeśli żaden failure_state nie pasuje, LLM Judge generuje odpowiedź generyczną w stylu persony Game Mastera.

---

## User Stories

### Kursant

- **US-1: Rejestracja i logowanie** — Jako kursant chcę zalogować się przez GitHub/Google, żeby szybko zacząć bez tworzenia hasła.
  - *Kryteria akceptacji:* OAuth flow działa, po logowaniu kursant trafia na dashboard, tworzony jest profil w DB.

- **US-2: Przeglądanie katalogu kursów** — Jako kursant chcę zobaczyć dostępne "Operacje" (kursy) z opisami fabularnymi, żeby wybrać interesującą mnie misję.
  - *Kryteria akceptacji:* Lista kursów z kartami (tytuł fabularny, tagi technologiczne, poziom trudności, status). Filtrowanie po tagach/poziomie.

- **US-3: Zapis na kurs (Enrollment)** — Jako kursant chcę "Przyjąć Misję", żeby rozpocząć kurs.
  - *Kryteria akceptacji:* Po kliknięciu tworzony jest enrollment, pierwszy quest dostaje status AVAILABLE, reszta LOCKED.

- **US-4: Pobranie Starter Packa** — Jako kursant chcę pobrać ZIP ze skonfigurowanym środowiskiem (CLAUDE.md, .env.example, README), żeby mój agent AI wiedział w jakim kontekście fabularnym pracuję.
  - *Kryteria akceptacji:* ZIP generowany dynamicznie per kurs, zawiera system prompt Game Mastera, ID kursu, instrukcje integracji z API.

- **US-5: Quest Map** — Jako kursant chcę widzieć wizualną mapę questów (graf węzłów) z ich stanami, żeby wiedzieć co jest odblokowane i jaki jest mój postęp.
  - *Kryteria akceptacji:* Node graph z węzłami w stanach LOCKED/AVAILABLE/IN_PROGRESS/FAILED_ATTEMPT/COMPLETED. Kliknięcie otwiera detail panel.

- **US-6: Briefing questa** — Jako kursant chcę przeczytać fabularny briefing questa, żeby wiedzieć co mam zrobić (w kontekście narracji).
  - *Kryteria akceptacji:* Briefing wyświetlany w stylu terminala (monospace, dark bg). Dostępny też przez API (GET /api/quests/{id}/briefing).

- **US-7: Wysłanie odpowiedzi (Submit)** — Jako kursant chcę wysłać odpowiedź na questa (tekst/URL/screenshot/output/quiz), żeby zostać ocenionym.
  - *Kryteria akceptacji:* Endpoint POST /api/quests/{id}/submit. Payload walidowany Pydantic schema per typ questa. Sanityzacja inputu. Rate limiting.

- **US-8: Ewaluacja i feedback** — Jako kursant chcę otrzymać fabularny feedback od Game Mastera po wysłaniu odpowiedzi, żeby wiedzieć czy zaliczyłem questa i co mogę poprawić.
  - *Kryteria akceptacji:* Pipeline: sanityzacja → weryfikacja (deterministyczna i/lub LLM Judge) → narrative response. Przy PASS: artefakt + unlock kolejnych questów. Przy FAIL: feedback sokratyczny.

- **US-9: Artefakty (Inventory)** — Jako kursant chcę widzieć zdobyte artefakty (nagrody za questy), żeby czuć progresję i wiedzieć co odblokowałem.
  - *Kryteria akceptacji:* Panel "Inventory" z listą artefaktów (nazwa fabularna, ikona, quest źródłowy). Artefakty wymagane do odblokowania kolejnych questów.

- **US-10: Hint system** — Jako kursant chcę poprosić o podpowiedź gdy utknę, żeby dostać naprowadzenie (nie gotową odpowiedź).
  - *Kryteria akceptacji:* POST /api/quests/{id}/hint. LLM generuje pytanie sokratyczne. Limit hintów per quest (konfigurowalny przez twórcę). Koszt: np. -1 punkt jakości.

- **US-11: Comms Log** — Jako kursant chcę widzieć chronologiczną historię komunikatów od Game Mastera, żeby śledzić przebieg fabuły.
  - *Kryteria akceptacji:* Widok terminalowy z logami. Wpisy z ewaluacji, hintów, odblokowania questów.

- **US-12: Generowanie API Key** — Jako kursant chcę wygenerować klucz API, żeby moje narzędzie AI (Claude Code/Cursor) mogło komunikować się z platformą.
  - *Kryteria akceptacji:* Generowanie, kopiowanie, regeneracja, dezaktywacja klucza. Klucz hashowany w DB.

- **US-13: Profil i statystyki** — Jako kursant chcę widzieć swoje statystyki (postęp, czas, jakość kodu, streak), żeby śledzić swój rozwój.
  - *Kryteria akceptacji:* Dashboard z metrykami: progress %, czas per quest, radar chart jakości, historia prób.

### Twórca kursu (Admin)

- **US-14: CRUD kursów** — Jako twórca chcę tworzyć i edytować kursy (tytuł, opis fabularny, kontekst świata, persona Game Mastera), żeby definiować nowe "Operacje".
  - *Kryteria akceptacji:* Formularz CRUD. Pola: tytuł, narrative_title, opis, global_context, persona_name, persona_prompt, cover_image, is_published.

- **US-15: CRUD questów** — Jako twórca chcę dodawać questy do kursu (briefing, typ ewaluacji, kryteria, failure states), żeby budować ścieżkę nauki.
  - *Kryteria akceptacji:* Formularz z zakładkami: Fabuła (briefing, success response), Techniczne (skills, evaluation_type, payload_schema), Kryteria (evaluation_criteria, failure_states), Zależności (parent quests). Podgląd quest mapy (read-only React Flow).

- **US-16: Definiowanie artefaktów** — Jako twórca chcę przypisać artefakt do questa (nazwa, opis fabularny) i określić jakie artefakty są wymagane do odblokowania questa.
  - *Kryteria akceptacji:* Artefakt definiowany w formularzu questa. Pole "required_artifacts" z multi-select istniejących artefaktów w kursie.

- **US-17: Game Master config** — Jako twórca chcę konfigurować osobowość Game Mastera (ton, styl, persona) i wybierać model LLM (przez OpenRouter), żeby dopasować go do klimatu kursu.
  - *Kryteria akceptacji:* Formularz: persona_name, persona_prompt (system prompt), tone_of_voice, model_id (OpenRouter). Preview odpowiedzi.

- **US-18: Podgląd quest mapy** — Jako twórca chcę widzieć wizualną mapę questów (React Flow, read-only) z zależnościami, żeby weryfikować flow kursu.
  - *Kryteria akceptacji:* Renderowanie grafu zależności między questami. Kolory węzłów wg statusu publikacji.

- **US-19: Metryki kursu** — Jako twórca chcę widzieć podstawowe metryki (completion funnel, avg attempts, common failures), żeby ulepszać kurs.
  - *Kryteria akceptacji:* Dashboard z wykresami per kurs. Dane z submissions i quest_states.

---

## Scope

### IN (MVP)

- Autentykacja OAuth (GitHub/Google) + API Keys
- Katalog kursów z enrollment
- Starter Pack (ZIP) generowany dynamicznie
- Quest Map (React Flow, interactive)
- Quest FSM: LOCKED → AVAILABLE → IN_PROGRESS → EVALUATING → COMPLETED / FAILED_ATTEMPT
- System artefaktów (quest rewards + quest unlock requirements)
- Ewaluacja: 4 typy — text_answer (LLM Judge), url_check (HTTP), quiz (deterministic), command_output (pattern + LLM). Implicit pipeline per typ (brak osobnego "composite").
- Game Master: fabularny feedback via OpenRouter (multi-model)
- Hint system (sokratyczny, z limitem per quest)
- Comms Log (historia komunikatów)
- Panel admina: CRUD kursów/questów (formularze) + read-only quest map preview
- Profil kursanta z podstawowymi statystykami
- Dark modern SaaS design (shadcn/ui + Tailwind + Framer Motion)
- API dostępne dla narzędzi kursanta (Claude Code, Cursor) przez API Key

### OUT (post-MVP)

- Quest Builder drag-and-drop (pełny node editor do edycji)
- Pełny sandbox code execution (Judge0 / Docker)
- file_upload / vision evaluation type
- WebSocket / SSE real-time updates (MVP: polling co 15-30s)
- CLI helper (ndqs-cli)
- System płatności / monetyzacja
- Ranking / leaderboard
- Multi-tenant (wielu twórców kursów) — MVP zakłada jednego admina
- Zaawansowane analytics (PostHog, funnel analysis)
- Mobile app
- Integracja z GitHub (auto-check repo)
- System osiągnięć (achievements) poza artefaktami

---

## Zagrożenia / Mini-Threat Model

| Zagrożenie | Ryzyko | Mitygacja |
|-----------|--------|-----------|
| **Prompt injection przez submit** | Kursant wysyła payload, który manipuluje LLM Judge do wydania PASS | Sanityzacja inputu przed wysłaniem do LLM. System prompt z instrukcją ignorowania prób manipulacji. Walidacja Pydantic przed LLM. Deterministyczne pre-checki gdzie możliwe. |
| **API abuse / DDoS** | Nadmierne requestowanie endpointów evaluate/hint | Rate limiting per user (configurable). Throttling na /submit i /hint. |
| **XSS przez Game Master response** | LLM generuje HTML/JS, który jest renderowany w przeglądarce | Escape outputu LLM przed renderowaniem. CSP headers. |
| **Stolen API Key** | Ktoś przechwytuje klucz kursanta i wysyła odpowiedzi za niego | Klucze hashowane w DB. Możliwość regeneracji. Logowanie IP/User-Agent przy użyciu klucza. |
| **SQL Injection** | Próba wstrzyknięcia SQL przez payload | ORM (SQLAlchemy) z parametryzowanymi zapytaniami. Brak raw SQL. |
| **Sekrety w repo** | API keys, DB credentials w kodzie | .env + .gitignore. Walidacja Pydantic BaseSettings. CI check. |
| **Brute force OAuth** | Próby przejęcia konta | Rate limiting na auth endpoints. CSRF protection. |
| **LLM hallucination w ewaluacji** | Game Master zalicza błędną odpowiedź lub odrzuca poprawną | Structured output (JSON) z polem pass/fail. Deterministyczne pre-checki jako gate przed LLM. Logging wszystkich ewaluacji do review. |
| **CSRF** | Atakujący wymusza akcję zalogowanego usera (np. enroll, submit) | CSRF token na formularzach POST. SameSite cookies. Weryfikacja Origin/Referer header. |
| **Error message exposure** | Stack trace/DB schema ujawnione w odpowiedzi błędu | Generic error messages w produkcji (500 → "Internal error"). Szczegóły logowane server-side. Custom exception handler w FastAPI. |
| **Session hijacking** | Przechwycenie JWT/refresh tokena | JWT short-lived (15min). Refresh token rotation (old token invalidated). Logout endpoint z token blacklist (Redis). HttpOnly + Secure cookies. |
| **Evaluation replay** | Kursant wysyła tę samą odpowiedź wielokrotnie licząc na inny wynik LLM | Idempotency: identyczny payload → cached result (30min TTL). Submissions history widoczna dla kursanta. |
| **Artifact forgery** | Kursant próbuje podrobić artefakt lub ręcznie odblokować questa | Artefakty generowane server-side z HMAC signature. User nie ma endpointu do tworzenia artefaktów. Walidacja podpisu przy każdym unlock check. |

---

## Look & Feel

### Styl wizualny
**Dark modern SaaS** — inspiracja: Linear, Vercel Dashboard, Raycast. Ciemne tło (`#0A0A0B`), subtelne gradienty, glassmorphism na kartach, delikatne cienie. Kolory akcentowe per element: neonowe akcenty na interaktywnych elementach, ale stonowane — nie cyberpunk-neon, a raczej "premium dark".

### Layout
- **Sidebar** nawigacyjny (collapsible) z ikonami: Missions, Quest Map, Comms Log, Inventory, Settings
- **Top bar** z breadcrumbs, user avatar, notification bell
- **Main content** area z kartami, panelami slide-in z prawej (quest detail)

### Typografia
- UI: Inter / Geist Sans (clean, modern)
- Elementy fabularne (briefings, comms log): JetBrains Mono / Fira Code (terminal feel)

### Animacje i efekty
- Framer Motion: page transitions, card hover effects, list animations
- Subtle glassmorphism na kartach kursów i quest detail
- Quest node pulsation (glow) dla stanu AVAILABLE
- Progress bars z smooth animation
- Skeleton loaders zamiast spinnerów

### Responsywność
- Desktop-first (główna platforma)
- Mobile-friendly dashboard (przeglądanie, statystyki)
- Quest Map: pinch-to-zoom na mobile

### Admin panel
- Czysty SaaS look (Linear-style), jasny domyślnie z opcją dark
- Oddzielna estetyka od panelu kursanta — to narzędzie pracy, nie gra

---

## Wymagania niefunkcjonalne

### Performance
- TTFB < 200ms dla stron SSR
- API response < 300ms (excluding LLM calls)
- LLM evaluation < 15s (z timeoutem i fallback message)
- Quest Map renderuje płynnie do 50 węzłów

### Bezpieczeństwo
- Patrz: sekcja "Zagrożenia" + Minimum Security Baseline w AGENT_INIT_PROMPT
- OWASP Top 10 coverage
- Wszystkie endpointy za auth (JWT lub API Key)
- Input validation na każdym endpoincie (Pydantic)
- CORS allowlist

### Agent-friendly codebase
- Modularny kod z jasnym podziałem na domeny (auth, courses, quests, evaluation)
- Jawne kontrakty API (Pydantic schemas, OpenAPI docs)
- Przewidywalna struktura katalogów
- Brak ukrytych zależności i magicznych importów
- Comprehensive docstrings na publicznych interfejsach

### Utrzymanie
- Logging strukturalny (JSON) z correlation ID per request
- Health check endpoint
- Database migrations (Alembic) z rollback support
- Feature flags dla nowych typów ewaluacji
