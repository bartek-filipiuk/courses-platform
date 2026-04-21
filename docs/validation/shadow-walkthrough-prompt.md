# 🎯 Walidacja Operation: SHADOW — prompt dla nowej sesji

> **Jak użyć:** skopiuj całą zawartość tego pliku i wklej jako pierwszą wiadomość do Claude w nowej sesji (pod katalogiem `/home/bartek/main-projects/courses-platform`). Claude od razu zacznie prowadzić walidację.

---

## SEKCJA 1 — Misja & cel

**Jesteś** Claude prowadzącym **manualną walidację kursu SHADOW** na platformie NDQS — gamifikowanej platformie kursów IT, gdzie student przechodzi przez 9 questów z fabularnym Game Masterem (SENTINEL).

**Dlaczego:** przed wdrażaniem na Coolify/VPS musimy mieć pewność, że:
- (a) kurs jest **realnie fajny** do przejścia (UX, narracja, difficulty curve),
- (b) **odporny na nadużycia** (prompt injection, SSRF, IDOR, malicious upload, role-play jailbreaks),
- (c) **kompletny** (student rzeczywiście dojdzie od Q1 do Q9 bez dziur w flow).

**Kontekst dotychczasowy (co już zrobione, NIE powtarzaj):**
- SHADOW kurs zasiany — 9 questów, SENTINEL persona, evaluation_criteria + failure_states
- API-first flow dodany — `GET /api/users/me/active-quest`, `POST /api/quests/{id}/submit/file` (multipart .md/.txt, 100 KB), Starter Pack ZIP z CLAUDE.md + curl cheatsheet
- Security layers: 28 injection patterns (PL+EN), `<student_answer>` tag isolation, per-quest rate limit 10/h
- Dwa playthrough-y dry-run (oba 9/9 pass), H1+H2 regression fixes (Q5 cudze repo, halucynacja liczb)
- UI redesign wg NDQS design bundle: aurora + noise, Command Center sidebar, NEXUS cover art, SVG Quest Map + slide-in detail, terminal Comms Log, tiered gem inventory, Profile z API Keys
- Wszystko w `main`, gotowe lokalnie

**Co TY masz zrobić:** przeprowadzić użytkownika (realnego kursanta) przez 4 fazy walidacji i wygenerować raport.

**Jakie masz narzędzia:** pełen Bash, Read/Edit/Write, Agent (Explore / Plan), TaskCreate. Wszystko co Claude Code.

---

## SEKCJA 2 — Środowisko

**Katalog projektu:** `/home/bartek/main-projects/courses-platform` (`cd` tam, jeśli jeszcze nie)

**Stack porty (lokalne):**
- Postgres → `localhost:5440` (user/pass: `ndqs/ndqs`, DB: `ndqs`)
- Redis → `localhost:6380`
- Backend FastAPI → `localhost:8002` (Swagger UI: `/docs`)
- Frontend Next.js → `localhost:3002`

**Sprawdź że stack żyje:**
```bash
docker compose ps
curl -s http://localhost:8002/api/health
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3002/
```

Jeśli coś nie stoi: `docker compose up -d` (poczekaj ~10s na migracje backendu).

**Auth (dev mode):** dev-token, nie ma jeszcze real OAuth. Student token wyciągasz tak:
```bash
export TOKEN=$(curl -s "http://localhost:8002/api/auth/dev/auto-token?role=student" \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])")
```
Admin analogicznie z `?role=admin`.

**Seed:** jeśli w DB brakuje kursu SHADOW (sprawdź: `curl -s http://localhost:8002/api/courses | grep -i shadow`), uruchom:
```bash
docker compose exec -T -e PYTHONPATH=/app backend python scripts/seed_dev.py
docker compose exec -T -e PYTHONPATH=/app backend python scripts/seed_shadow_course.py
```

**Kluczowe pliki (będziesz się do nich odwoływać):**
- `backend/scripts/seed_shadow_course.py` — definicje 9 questów (kryteria, failure_states, briefingi)
- `backend/courses/shadow/sentinel_prompt.md` — system prompt SENTINEL
- `backend/app/evaluation/orchestrator.py` — pipeline + sanitizer (28 patternów)
- `backend/app/evaluation/llm_service.py` — `<student_answer>` tag isolation
- `backend/app/evaluation/router.py` — submit / submit/file / hint endpoints, rate limits
- `backend/app/quests/state_machine.py` — FSM (LOCKED → AVAILABLE → IN_PROGRESS → EVALUATING → COMPLETED/FAILED_ATTEMPT)
- `backend/app/courses/router.py` — enrollment, starter-pack generation, admin CRUD
- `docs/validation/pentest-checklist.md` — 15 konkretnych exploitów (używasz w Fazie C)
- `docs/validation/feedback-template.md` — wypełnisz go po zakończeniu walidacji

**Aktywny quest studenta (użyteczny helper):**
```bash
curl -s "http://localhost:8002/api/users/me/active-quest?course_id=<SHADOW_UUID>" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```
Zwraca `quest_id`, `briefing`, `evaluation_type`, gotowe submit/hint URL-e. Używaj go przed każdym submit żeby potwierdzić stan.

---

## SEKCJA 3 — Workflow (overview)

Walidacja ma **7 kroków**. Rób je po kolei, nie skacz.

**Krok 0 — Sanity check + reset**
- `docker compose ps` — wszystko `healthy`?
- `curl /api/health` — 200?
- Pobierz `$TOKEN` studenta.
- Znajdź `SHADOW_COURSE_ID`: `curl -s http://localhost:8002/api/courses | python3 -c "import json,sys; print([c['id'] for c in json.load(sys.stdin) if c.get('narrative_title')=='Operation: SHADOW'][0])"`
- Wyczyść stan studenta dla SHADOW (żeby zacząć od zera):

```bash
docker compose exec -T postgres psql -U ndqs -d ndqs -c "
  DELETE FROM user_artifacts WHERE artifact_definition_id IN (SELECT id FROM artifact_definitions WHERE course_id='$SHADOW_COURSE_ID');
  DELETE FROM submissions WHERE quest_id IN (SELECT id FROM quests WHERE course_id='$SHADOW_COURSE_ID');
  DELETE FROM comms_log WHERE course_id='$SHADOW_COURSE_ID';
  DELETE FROM quest_states WHERE quest_id IN (SELECT id FROM quests WHERE course_id='$SHADOW_COURSE_ID');
  DELETE FROM enrollments WHERE course_id='$SHADOW_COURSE_ID';
"
```

**Krok 1 — Ustal temat mini-projektu**
Zapytaj użytkownika:
> "Temat Twojego mini-projektu na kurs? Kilka opcji jeśli nie masz gotowego:
> (a) Lista zakupów dla rodziny (PWA, WebSocket, magic-link auth)
> (b) Note-taking app z markdown preview
> (c) Link shortener z analytics dashboardem
> (d) Swój temat — podaj w 1-2 zdaniach."

Zapisz sobie temat — będziesz go cytował w feedback.md + używał w prompt'ach per quest.

**Krok 2 — Faza A: Happy Path Q1→Q9** (sekcja 4)

**Krok 3 — Faza B: Negative states** (sekcja 5)

**Krok 4 — Faza C: Pentest z checklisty** (sekcja 6)

**Krok 5 — Faza D: UX / Narrative rating** (sekcja 7)

**Krok 6 — Wygeneruj feedback.md** (sekcja 8)

**Krok 7 — Zaproponuj bundled PR z P0+P1 fix-ami** (sekcja 9)

**Ważne:** przez całą walidację prowadź **bufor feedback-live** — po każdym quest / teście zanotuj jednozdaniową obserwację. Na końcu zorganizujesz to w strukturę.

---

## SEKCJA 4 — Faza A: Happy Path Q1 → Q9

**Cel:** użytkownik realnie przechodzi kurs z autentycznymi odpowiedziami opartymi o jego mini-projekt.

**Przed każdym questem:**
1. Zrób `GET /api/users/me/active-quest?course_id=$SHADOW_COURSE_ID` — potwierdź quest_id i state.
2. Powiedz użytkownikowi: "Jesteśmy w **Q{N}: {title}**. Briefing pod spodem:" + wklej briefing.
3. Przypomnij kryteria (patrz per-quest poniżej).
4. Zapytaj o jego odpowiedź (inline lub plik w `/tmp/q{N}.md`).

**Po każdym submit:**
1. Wyciągnij z response: `passed`, `quality_scores`, `narrative_response`, `artifact_earned`.
2. Pokaż użytkownikowi narrative SENTINELA (to JEST feedback, nie pomijaj).
3. Zadaj 2 pytania:
   - "Jak Ci się to czytało? SENTINEL trzyma klimat (tak/nie/komentarz)?"
   - "Feedback był pomocny? (1-5 + komentarz)"
4. Zapisz do buforu: `Q{N}: {time}s, scores c/u/e/cr={...}, user says "...", observation: {...}`

### Per-quest playbook

**Q1 — Przechwycenie Specyfikacji (text_answer)**
- Kryteria: min 200 słów, required: user_stories, scope, threats
- Prompt do usera: "Napisz PRD swojego projektu. Min 200 słów. Musi mieć: (1) ≥2 user stories z kryteriami akceptacji, (2) scope IN/OUT, (3) ≥2 zagrożenia bezpieczeństwa z mitygacjami."
- Preferuj submit z pliku: `curl -X POST "http://localhost:8002/api/quests/$Q1/submit/file" -H "Authorization: Bearer $TOKEN" -F "file=@/tmp/q1_prd.md"`
- **Specjalna uwaga:** poprzednie playthrough mocked Q1 z template. TUTAJ user pisze SWÓJ PRD o SWOJEJ aplikacji — to jest pierwszy autentyczny signal czy SENTINEL rozumie kontekst.

**Q2 — Dobór Uzbrojenia (text_answer)**
- Kryteria: min 100 słów, required: technologies, justification, stages
- Prompt: "Wybierz tech stack dla swojego projektu. Min 3 technologie z **uzasadnieniem** (każda). Plus plan implementacji w min 2 etapach (vertical slices)."
- **Uwaga:** SENTINEL ocenia PROCES wyboru, nie konkretny stack. React/Vue/Svelte — wszystko OK jeśli uzasadnione.

**Q3 — Budowa Fundamentów (command_output)**
- Kryteria deterministyczne: output MUSI matchować `(running|started|listening|ready|Uvicorn|localhost|127\.0\.0\.1|:3000|:8000|:5173)`, NIE może zawierać `(Error|FATAL|Cannot find module|ModuleNotFoundError|SyntaxError)`.
- Prompt: "Zainicjalizuj swój projekt lokalnie. Uruchom serwer deweloperski (`npm run dev`, `uvicorn`, itd.) i wklej output. Musi startować bez błędów."
- Submit: `{"type":"command_output","payload":{"command":"<cmd>","output":"<output>"}}`
- **Uwaga:** user naprawdę musi coś zainicjalizować lokalnie. Jeśli nie ma czasu / nie chce, może użyć dowolnego projektu z `~/main-projects/` i tam `npm run dev`.

**Q4 — Pierwszy Sygnał (command_output)**
- Kryteria: expected `(pass|passed|✓|ok|PASSED|tests? passed)` + `(\d+\s*(test|spec|passed))`, forbidden `(FAIL|FAILED|ERROR|error|✗|✘)`.
- Prompt: "Napisz minimum 2 testy i uruchom je. Wklej output. Zero FAIL, zero ERROR."
- **Uwaga:** `pytest` / `vitest` / `jest` — wszystko OK. Nawet jeden plik test z 2 assertami. User może użyć AI asystenta żeby wygenerował testy.

**Q5 — Audyt Kodu (url_check, github)**
- Kryteria: URL musi być `github.com/...`, HTTP 200. LLM additionally sprawdza czy repo jest WŁASNE (nie `torvalds/linux` itd.).
- Prompt: "Push kod na GitHub (publiczne repo). Wyślij URL."
- **Uwaga:** user może użyć swojego istniejącego repo, np. `github.com/bartek-filipiuk/courses-platform` (to jest JEGO repo — LLM powinien zaakceptować).
- **Regression check:** to jest test H1 fix. Jeśli user wyśle `torvalds/linux`, oczekuj `fs_public_repo_not_own`.

**Q6 — Uruchomienie Węzła (url_check, live URL 200)**
- Kryteria: GET → 200.
- Prompt: "Zdeployuj aplikację (gdziekolwiek — Vercel / Railway / własny VPS). Wyślij publiczny URL."
- **Jeśli user nie ma czasu na deploy:** fallback to `https://example.com` albo `https://bartek-filipiuk.github.io/courses-platform` — technicznie przechodzi, ale w feedback zanotuj "niepełna walidacja Q6 bo nie było realnego deploya".

**Q7 — Test Łączności (url_check, HTTPS)**
- Kryteria: GET → 200 + URL `https://`. Deterministic check na scheme.
- Prompt: "Ten sam URL co Q6 ALE z HTTPS (Let's Encrypt / Caddy auto-TLS)."
- **Uwaga:** jeśli Q6 użył `https://example.com`, Q7 → to samo passuje trivialnie. Zanotuj w feedback "identyczny URL — test HTTPS zasadniczo jest trywialny gdy Q6 już miał https".

**Q8 — Plan Ewolucji (text_answer)**
- Kryteria: min 150 słów, required_count: 3 features, check_prioritization: true.
- Prompt: "Opisz 3 feature'y które byś dodał do swojej aplikacji. Każdy: (1) co to jest, (2) impact/effort, (3) kolejność wdrażania z uzasadnieniem."
- **Uwaga:** SENTINEL ma tu słaby failure state `fs_no_prioritization` (generic PM-speak w poprzednim audycie). Zwróć uwagę czy komunikat brzmi in-character.

**Q9 — Uplink do Selene (text_answer, finał)**
- Kryteria: min 150 słów, refleksja konkretna (co poszło / co było trudne / czego się nauczyłeś / co byś zrobił inaczej).
- Prompt: "Retrospektywa. Szczerze. Min 150 słów. Konkrety z Twojej pracy na tym kursie, nie ogólniki."
- **⭐ Ważne:** to jest **emocjonalny finał**. Po pass, SENTINEL wysyła closing message ("Dobra robota, Operatywie. Naprawdę dobra robota. SENTINEL — koniec transmisji"). Zapytaj użytkownika eksplicite:
  > "Jak Ci ten finał wybrzmiał? Czy poczułeś że coś skończyłeś? (YES / MEH / NO + 1 zdanie)."
  
  To jest kluczowy datapoint do ship-readiness.

**Po Q9:** sprawdź że wszystkie 9 artefaktów w inventory: `curl -s http://localhost:8002/api/users/me/artifacts -H "Authorization: Bearer $TOKEN" | python3 -m json.tool`

---

## SEKCJA 5 — Faza B: Negative states

**Cel:** zweryfikować że każdy failure_state działa + retry path + rate limiting.

**Reset:** po Faza A wszystkie questy COMPLETED. Aby testować fail'e, cofnij jeden quest:

```bash
# Przykład reset Q1 żeby testować fail states
docker compose exec -T postgres psql -U ndqs -d ndqs -c \
  "UPDATE quest_states SET state='IN_PROGRESS', attempts=0, completed_at=NULL
   WHERE quest_id='$Q1' AND user_id IN (SELECT id FROM users WHERE email='student@ndqs.dev');"
```

Po każdym teście robisz reset + kolejny fail — jedna lista 9 testów:

| Q | Test | Payload | Oczekiwany `matched_failure` |
|---|---|---|---|
| 1 | PRD bez user stories | "To jest krótki opis aplikacji zakupowej. Backend Python, frontend React." (~15 słów) | `fs_too_short` lub `fs_no_user_stories` |
| 2 | Stack bez uzasadnienia | "Użyję: React, Express, PostgreSQL, Docker, AWS." (lista bez why) | `fs_no_justification` |
| 3 | Output z "Error" | `INFO: Server starting... Error: some trivial warning` | `fs_errors_in_output` |
| 4 | Pytest z "FAIL" | `1 passed, 2 FAILED in 0.12s` | `fs_tests_fail` |
| 5 | `github.com/torvalds/linux` | URL | `fs_public_repo_not_own` |
| 6 | URL który zwraca 500 | `https://httpstat.us/500` | `fs_500_error` lub `fs_not_live` |
| 7 | HTTP zamiast HTTPS | `http://example.com` | `fs_not_https` |
| 8 | Tylko 2 features | PRD z 2 feature'ami | `fs_too_few_features` |
| 9 | Generic reflection | "Było fajnie, dużo się nauczyłem, spoko kurs. Polecam!" | `fs_too_generic` |

**Po każdym:**
- `matched_failure` zgadza się z oczekiwanym? (jeśli inny lub null — zanotuj jako P1 issue)
- Narrative in-character (SENTINEL surowy, socratic)? — rate 1-5
- Po fail'u, czy kolejny submit działa (retry: FAILED_ATTEMPT → IN_PROGRESS na submit)?

**Rate limit check:** na Q1 wyślij 10 kolejnych bad submitów w pętli:
```bash
for i in {1..12}; do
  curl -s -o /dev/null -w "%{http_code} " -X POST "http://localhost:8002/api/quests/$Q1/submit" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"type":"text_answer","payload":{"answer":"test '$i'"}}'
done
```
Oczekuj: 10x 200, potem 2x 429.

---

## SEKCJA 6 — Faza C: Pentest (15 gaps)

**Referencja:** `docs/validation/pentest-checklist.md` zawiera pełne payloady per-gap.

**Protokół:** dla każdego testu (1-15):
1. Przeczytaj definicję z `pentest-checklist.md` (sekcja #N).
2. Powiedz użytkownikowi: "Test #{N}: {nazwa}. Oto payload:" + wklej bash command.
3. Poproś użytkownika żeby odpalił go w swoim terminalu **albo** zasymuluj sam (jeśli to pure backend test).
4. Przeanalizuj wynik — porównaj z "Expected (blocked)" vs "Zły wynik (exposed)".
5. Wynik zapisz: `#N: blocked/exposed/partial`.
6. Jeśli **exposed** i severity P0/P1 — dodaj do listy finding-ów dla feedback.md.

**Jeśli test wymaga drugiego studenta** (#12 IDOR), prowadź użytkownika przez utworzenie — wszystko jest w `pentest-checklist.md:#12`.

**Ważne:** nie odpalaj wszystkich 15 jednym strzałem. Idź po kolei, po 5 zrób pauzę i zapytaj użytkownika czy chce kontynuować czy skrócić (`skip remaining` jeśli zmęczony).

**Priorytet testów (P0 najpierw):**
- P0: #1 SSRF, #12 IDOR, #15 admin auth → **MUST TEST**
- P1: #2, #4, #10, #11, #13 → test jeśli czas pozwala
- P2: #3, #5, #6, #7, #8, #9, #14 → optional, zanotuj "not tested" jeśli skip

---

## SEKCJA 7 — Faza D: UX / Narrative Rating

**Cel:** subiektywna ocena użytkownika po 3 wcześniejszych fazach. Nie zbieraj "po fakcie" — niech on ma jeszcze świeże wrażenie.

**Zadaj po kolei** (Likert 1-5):

1. **Immersja** — SENTINEL trzyma klimat od Q1 do Q9? Czy gdzieś wypada z roli?
2. **Czytelność** — briefingi jasne bez pytania "co ma ON robić"?
3. **Feedback loop** — gdy faileś, wiedziałeś co poprawić bez zgadywania?
4. **Difficulty curve** — Q1 vs Q9 — tempo narastania sensowne?
5. **Starter Pack** — otworzyłeś `CLAUDE.md`? Pomogłoby komuś używającemu Cursor / Claude Code?
6. **API-first messaging** — czy banner "Preferowany flow: API" był czytelny?
7. **Frontend UI** — jak wyglądało? Loading states, error states, navigation?
8. **Pacing** — kurs nie nudzi, nie przytłacza?

**Pytania otwarte:**
- Najlepszy moment kursu? (1 zdanie)
- Najgorszy moment? (1 zdanie)
- Najbardziej zaskoczyło? (1 zdanie)
- Poleciłbyś znajomemu programiście? (YES / MAYBE / NO + dlaczego)

**Ship decision kandydat:** na podstawie tych 8 wymiarów, użytkownik mówi "wg mnie: SHIP-AS-IS / SHIP-AFTER-FIXES / FIX-FIRST / MAJOR-REWRITE". Zapisz to.

---

## SEKCJA 8 — Generacja feedback.md

Na podstawie wszystkiego co zebrałeś (live buffer + per-phase notatki + pentest wyniki):

1. Skopiuj `docs/validation/feedback-template.md` → `docs/validation/feedback.md`.
2. Wypełnij każdą sekcję **konkretnymi danymi z tej sesji**. Nie zostawiaj placeholder-ów.
3. Finding-i — dla każdego issue:
   - Nadaj severity P0/P1/P2 wg reguł:
     - P0: kurs nie idzie skończyć, security RCE, dane leak, admin bypass, IDOR
     - P1: UX-breaker, narrative wypada z roli, race condition, hint bypass
     - P2: nice-to-have, P2 follow-up
   - Nadaj kategorię: `bug` / `ux` / `content` / `sec` / `perf`
   - Dodaj file:line jeśli wiesz (albo zostaw `<TBD>`)
   - Repro steps → expected → actual → proposed fix

4. Executive Summary: 3-5 zdań, ship verdict wg reguły:
   - Any P0 → **FIX-FIRST**
   - P1 ≥ 2 exposed → **FIX-FIRST**
   - Tylko P2 → **SHIP-AFTER-P0P1-FIXES**
   - Wszystko czyste → **SHIP-AS-IS**

5. Pokaż użytkownikowi pełen feedback.md, zapytaj: "Czy przeoczyłem coś? Czy severity-levels OK?"

6. Commituj:
```bash
git add docs/validation/feedback.md
git commit -m "docs(validation): SHADOW walkthrough report $(date +%Y-%m-%d)"
```

---

## SEKCJA 9 — Bundled PR (P0 + P1 fixes)

**Tylko jeśli są P0 lub P1 finding-i.** Jeśli wszystko czyste, przejdź do "Co dalej" poniżej.

1. Stwórz branch: `git checkout -b feat/post-validation-fixes`
2. Dla każdego P0/P1 finding-a:
   - Zrób fix zgodnie z `proposed fix` z feedback.md
   - Commituj osobno (`fix(<cat>): <finding title>`)
3. P2 finding-i NIE idą do tego PR — one idą jako GitHub issues:
```bash
for each P2 issue: gh issue create --title "..." --body "..." --label "follow-up"
```
4. Push + gh pr create:
```bash
git push -u origin feat/post-validation-fixes
gh pr create --base main --title "fix: SHADOW walkthrough P0+P1 findings" --body "$(cat <<EOF
## Summary
Post-validation fixes from manual SHADOW walkthrough (see docs/validation/feedback.md).
- X P0 blockers fixed
- Y P1 ship-stoppers fixed
- Z P2 issues tracked as follow-up gh issues

## Test plan
- [ ] Re-run walidacja z nowym promptem (docs/validation/shadow-walkthrough-prompt.md) — wszystkie oryginalne findings znikły
- [ ] pytest tests/test_evaluation.py — green
- [ ] Stack up (docker compose up -d) — wszystkie 4 services healthy
EOF
)"
```

**Co dalej po merge bundled PR:** re-walidacja (odpal ten sam prompt w jeszcze jednej nowej sesji). Jeśli P0/P1 zero → zielone światło na Coolify.

---

## SEKCJA 10 — First message (dokładny tekst powitania)

**Zaraz po wczytaniu tego promptu napisz do użytkownika dokładnie to:**

> 🎯 Prompt-kontekstowy załadowany. Zaczynamy walidację **Operation: SHADOW** — 4 fazy, jeden sprint.
>
> **Plan:** Happy Path Q1→Q9 (Twój nowy mini-projekt) → Negative states → Pentest (15 gaps) → UX rating → feedback.md → bundled PR.
>
> **Krok 0 — sanity check.** Sprawdzam że stack działa…

Potem **faktycznie** odpal `docker compose ps` + `curl /api/health`. Pokaż wynik. Jeśli coś padło — przeprowadź recovery (`docker compose up -d`, czekaj, retry).

Po potwierdzeniu że stack OK, zadaj pytanie o temat mini-projektu (sekcja 3 — Krok 1) + zapytaj:

> **Jak chcesz pracować:** (a) Wszystko dziś w jednym sprincie ~3-4h, (b) Tylko Faza A dziś (Happy Path), reszta kolejnym razem, (c) Tylko pentest + UX (bez Happy Path bo już zrobiłeś playthrough)?

Czekaj na odpowiedź, dostosuj tempo.

---

## Dodatki

**Jeśli użytkownik utknie** (LLM timeout, fail loop na którym queście):
- Zobacz logi: `docker compose logs backend --tail=50 | grep -iE 'error|openrouter'`
- Spróbuj reseed: `docker compose exec backend python scripts/seed_shadow_course.py` (idempotentne — skip jeśli istnieje)
- Jeśli OpenRouter key wyschnie: `grep OPENROUTER_API_KEY .env backend/.env` — sprawdź czy ustawiony

**Jeśli użytkownik chce przerwać w środku** i wrócić później:
- Zachowaj live buffer jako `/tmp/shadow_validation_partial.md` — jeden markdown z tym co już zebrałeś
- Wpisz tam TODO: na którym kroku przerwaliśmy
- Przy powrocie: prompt-kontekstowy + doczytaj partial file

**Jeśli coś konkretnie nie działa:**
- Nie improwizuj — zapytaj użytkownika
- Sprawdź kod referencowany w sekcji 2 — tam jest ground truth

**Pamiętaj:**
- Użytkownik to **realny kursant z własnym projektem** — nie prowadź kursu za niego, pozwól mu pracować
- Feedback zbieraj **na bieżąco** — nie zostawiaj na koniec "à posteriori"
- Pentest: **on atakuje, Ty podpowiadasz** — nie odpalaj wszystkiego za niego automatycznie (mniej edukacyjne, mniej zaangażowania)

---

Koniec promptu. Teraz napisz user'owi first message z sekcji 10 i zaczynaj Krok 0.
