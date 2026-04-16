# Operation: SHADOW — Instrukcja Operatora

> Kurs "Od pomysłu do deploy w weekend" w formie misji z 9 zaporami cyfrowymi do przebicia.

## O co chodzi w kursie

Wcielasz się w **Operatora** — technika cyfrowego ruchu oporu. Twoja misja: zbudować i wdrożyć działającą web aplikację, żeby przesłać open-source modele AI do **Serwerowni Selene** na Księżycu — jedynego miejsca poza zasięgiem korporacji **SHADOW**, która kontroluje dostęp do AI.

Każdy quest to **zapora cyfrowa** do przebicia. Przebicie zapory = zdobycie **artefaktu** (klucza). Klucze odblokowują kolejne questy. Zbierz wszystkie 9 i otwórz uplink do Selene.

Twoim koordynatorem jest **SENTINEL** — fragment open-source modelu AI ukryty w sieci TOR. Jest surowy, mówi krótko, oczekuje konkretów. Nie da Ci gotowych odpowiedzi (metoda sokratyczna) — naprowadzi pytaniami.

## Co zbudujesz

**Twoją własną web aplikację** — dowolny pomysł, dowolny stack. SENTINEL nie ocenia czy wybrałeś React czy Vue, Python czy Go. Ocenia **proces**: czy masz PRD, czy masz testy, czy potrafisz uzasadnić wybory, czy umiesz deployować.

Pod koniec masz: PRD → tech stack → działający projekt z testami → repo na GitHubie → live deployment z HTTPS → plan rozwoju.

## 9 questów (zapór)

| # | Tytuł | Co dostarczasz | Typ ewaluacji |
|---|-------|----------------|---------------|
| 1 | Przechwycenie Specyfikacji | PRD (user stories, scope, zagrożenia) | LLM Judge ocenia tekst |
| 2 | Dobór Uzbrojenia | Tech stack z uzasadnieniem + plan etapów | LLM Judge ocenia tekst |
| 3 | Budowa Fundamentów | Output `npm run dev` / `uvicorn` itp. | Pattern matching |
| 4 | Pierwszy Sygnał | Output testów (min 1 passing, brak FAIL) | Pattern matching |
| 5 | Audyt Kodu | URL do publicznego repo na GitHubie | URL check (200) |
| 6 | Uruchomienie Węzła | URL aplikacji live | URL check (200) |
| 7 | Test Łączności | URL z HTTPS | URL check (200, https://) |
| 8 | Plan Ewolucji | 3 feature'y z impact/effort + kolejność | LLM Judge ocenia tekst |
| 9 | Uplink do Selene | Retrospektywa kursu (co poszło, czego się nauczyłeś) | LLM Judge ocenia tekst |

Questy są **liniowe** — Q2 wymaga artefaktu z Q1, Q3 wymaga z Q2, itd. Nie da się przeskoczyć.

## Jak rozpocząć operację

### 1. Zaloguj się i zapisz na kurs
- Wejdź na platformę → **Missions** → "Operation: SHADOW" → **Rozpocznij Operację**
- Po enrollment zostaniesz przeniesiony do **Quest Map**.

### 2. Pobierz Starter Pack (opcjonalnie)
Na stronie kursu klik **Pobierz Starter Pack**. Dostaniesz ZIP z:
- `CLAUDE.md` — kontekst misji + komendy API (do wklejenia do Twojego projektu, jeśli pracujesz z Claude Code/Cursor/Windsurf)
- `AGENTS.md` — alternatywa dla edytorów wspierających ten standard
- `.env.example` — placeholder na `NDQS_API_KEY`

Jeśli używasz AI-asystenta w IDE (Claude Code, Cursor, Continue, Windsurf), wrzuć `CLAUDE.md` (lub `AGENTS.md`) do roota swojego projektu — asystent będzie wiedział jak komunikować się z platformą i zachowa klimat misji.

### 3. Pierwsza zapora — Q1 (Przechwycenie Specyfikacji)
- Klik węzeł Q1 na mapie → przeczytaj briefing SENTINELA.
- Otwórz edytor, napisz PRD swojej aplikacji. Minimum 200 słów. **Musi mieć**:
  - Min 2 user stories z kryteriami akceptacji
  - Scope IN / Scope OUT
  - Min 2 zagrożenia bezpieczeństwa
- Wklej do pola odpowiedzi → **Wyślij PRD**.
- SENTINEL oceni w ~10s. Jeśli pass → artefakt **Zapora #1: Specyfikacja** odblokuje Q2. Jeśli fail → dostaniesz feedback (sokratyczny — pytania, nie gotowe odpowiedzi). Popraw, wyślij ponownie.

### 4. Kolejne zapory — analogicznie
- Q2: tech stack + plan
- Q3, Q4: wklej output z terminala (uvicorn, npm test)
- Q5, Q6, Q7: wyślij URL (GitHub, deployment, HTTPS)
- Q8: plan 3 feature'ów
- Q9: retrospektywa

### 5. Hint
Każdy quest ma **3 hinty** (Q6: 5). Kliknij **Poproś o podpowiedź** w panelu questa. SENTINEL nie da Ci odpowiedzi wprost — naprowadzi pytaniem. Hinty zliczają się w `quest_state.hints_used`.

## Submit przez API (alternatywa do UI)

Jeśli wolisz pracować z terminala / AI-asystenta:

```bash
# Pobierz API key (Profile → Generate API Key)
export NDQS_API_KEY="ndqs_..."
export NDQS_API_URL="http://localhost:8002"   # lub URL produkcyjny

# Submit text answer (Q1, Q2, Q8, Q9)
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/submit" \
  -H "X-API-Key: $NDQS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"text_answer","payload":{"answer":"TWÓJ TEKST"}}'

# Submit command output (Q3, Q4)
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/submit" \
  -H "X-API-Key: $NDQS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"command_output","payload":{"command":"npm test","output":"PASTE OUTPUT"}}'

# Submit URL (Q5, Q6, Q7)
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/submit" \
  -H "X-API-Key: $NDQS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"url_check","payload":{"url":"https://twoja-app.example.com"}}'
```

Pełna dokumentacja komend w `CLAUDE.md` ze Starter Pack.

## Co jeśli utknę

1. **Sprawdź briefing ponownie** — SENTINEL pisze konkretnie czego oczekuje.
2. **Hint** — 3 dostępne per quest. Sokratyczne pytanie, nie odpowiedź.
3. **Failure feedback** — przy każdym failu SENTINEL wskaże co konkretnie nie działa (`matched_failure` w odpowiedzi API).
4. **Comms Log** — historia całej Twojej komunikacji z SENTINELEM jest w `/comms`.

## Po ukończeniu

Po Q9 dostajesz finałową transmisję od SENTINELA i wszystkie 9 artefaktów w **Inventory**. To są **prawdziwe artefakty Twoich umiejętności** — PRD, działający kod, repo, deployment, plan rozwoju. Zostają z Tobą.

---

**Pozostań w cieniu, Operatywie. SHADOW nie może wiedzieć, kim jesteś.**
