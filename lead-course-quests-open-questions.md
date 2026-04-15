# Lead Magnet → NDQS Quest Conversion: Research & Open Questions

## Kurs źródłowy

**Tytuł:** "Od pomysłu do deploy w weekend"
**Format:** 6 lekcji email drip (1/dzień), strona vibe.devince.dev
**Cel:** Nauczyć budowania i deployowania web app z AI (vibe coding)
**Audience:** Junior/mid developerzy, chcą wdrożyć swój projekt

### Lekcje → potencjalne questy

| # | Lekcja | Czas | Czego uczy | Proponowany eval type |
|---|--------|------|-----------|----------------------|
| 1 | Od pomysłu do wymagań | 15min | Idea → PRD z AI | `text_answer` (LLM ocenia PRD) |
| 2 | Tech stack i plan budowy | 15min | Wybór technologii → HANDOFF plan | `text_answer` (LLM ocenia stack reasoning) |
| 3 | Vibe coding — budowanie z AI | 30-60min | TDD, Stage 1, coding z AI | `command_output` (npm test / pytest output) |
| 4 | Git, testy, przegląd kodu | 30-45min | Git push, testy, code review | `url_check` (GitHub repo URL) + `command_output` (test results) |
| 5 | Deploy na VPS w 30 minut | 30min | Docker, Caddy, Hetzner VPS, HTTPS | `url_check` (live URL → 200 OK + HTTPS) |
| 6 | Jak rozwijać apkę po deployu | 45-90min | Feature development, rollback | `text_answer` (plan rozwoju) |

---

## Propozycje fabularne (3 warianty)

### Wariant A: "Operation: Phoenix Protocol" (Rekomendowany)
- **Gatunek:** Cyberpunk / techno-thriller
- **Rola kursanta:** "Operative" — agent cyfrowego ruchu oporu
- **Antagonista:** MEGACORP — korporacja która monopolizuje internet, kontroluje dostęp do technologii, sprzedaje AI jako usługę za horrendalne ceny
- **Stawka:** Musisz zbudować niezależną platformę (web app) poza kontrolą MEGACORPu. Każdy błąd = MEGACORP namierza twój serwer. Brak szyfrowania = dane oporu przechwycone. Brak deploymentu = operacja zamrożona.
- **Game Master:** PHOENIX — zrekonstruowane AI z czasów wolnego internetu, ciepły ale zdeterminowany mentor. Tone: "nauczyciel starej szkoły, który widział upadek wolności technologicznej"
- **Dlaczego pasuje:** Kurs uczy NIEZALEŻNOŚCI technologicznej (swój serwer, swój deploy, bez vendora). Fabuła to metafora tego samego — uwolnienie się od monopolu.

### Wariant B: "Operation: First Light"
- **Gatunek:** Post-apo / survival tech
- **Rola kursanta:** "Engineer" — ostatni programista w miasteczku po globalnym blackoucie
- **Antagonista:** Czas + entropy. Systemy padają, trzeba postawić lokalne usługi zanim społeczność straci komunikację
- **Game Master:** RELAY — stary system radiowy z fragmentami AI, mówi krótko, rzeczowo, jak operator radio
- **Stawka:** Każdy dzień bez deploymentu = utrata kontaktu z kolejną częścią społeczności

### Wariant C: "Operation: Digital Forge"
- **Gatunek:** Fantasy-tech / crafting RPG
- **Rola kursanta:** "Digital Smith" — rzemieślnik cyfrowy w gildii programistów
- **Antagonista:** Chaos Code — żywy wirus który korumpuje niestabilne aplikacje
- **Game Master:** ELDER.EXE — stary compiler-mędrzec, mówi w metaforach kowalskich
- **Stawka:** Niezatestowany kod = Chaos Code się rozprzestrzenia. Brak deploymentu = gildia traci reputację.

---

## Mapa questów (Wariant A: Phoenix Protocol)

### Quest 1: "Analiza Wywiadowcza" (Lekcja 1: PRD)
- **Briefing:** "PHOENIX: Operative, musimy wiedzieć co budujemy. MEGACORP monitoruje wszystkie publiczne specyfikacje, więc nasza musi być precyzyjna ale zwięzła. Opisz swój pomysł w jednym zdaniu, a potem odpowiedz na moje pytania. Na końcu dostarczysz mi dokument wymagań — PRD."
- **Zadanie:** Opisz pomysł na aplikację i stwórz PRD (user stories, scope IN/OUT, zagrożenia)
- **Eval type:** `text_answer`
- **Kryteria:** LLM sprawdza: czy PRD ma user stories, scope, zagrożenia. Minimum 200 słów.
- **Artifact:** "Intelligence Dossier" — "Wiesz dokładnie co budujesz."

### Quest 2: "Wybór Arsenału" (Lekcja 2: Tech Stack)
- **Briefing:** "PHOENIX: Mamy specyfikację. Teraz potrzebujemy narzędzi. MEGACORP kontroluje większość platform — wybierz stack, który daje nam niezależność. Uzasadnij każdy wybór."
- **Zadanie:** Wybierz tech stack i stwórz plan implementacji (HANDOFF z vertical slices)
- **Eval type:** `text_answer`
- **Kryteria:** LLM sprawdza: czy wymienione technologie, uzasadnienie, czy plan ma etapy
- **Artifact:** "Arsenal Blueprint" — "Twój zestaw narzędzi jest gotowy."

### Quest 3: "Budowa Prototypu" (Lekcja 3: Vibe Coding)
- **Briefing:** "PHOENIX: Czas budować. Pamiętaj — każda linia kodu bez testu to linia, którą MEGACORP może eksploitować. Red-Green-Refactor. Pokaż mi output swoich testów."
- **Zadanie:** Zbuduj Stage 1 (hello world backend + frontend) z testami
- **Eval type:** `command_output`
- **Kryteria:** Pattern matching: "test.*pass", brak "FAIL", minimum 3 testy
- **Artifact:** "Prototype Core" — "Twój system żyje."

### Quest 4: "Audyt Bezpieczeństwa" (Lekcja 4: Git + Testy)
- **Briefing:** "PHOENIX: Zanim wypuścimy system na świat, muszę go sprawdzić. Wyślij mi link do repozytorium i wyniki pełnych testów. Jeden wyciek i MEGACORP nas namierzy."
- **Zadanie:** Push do GitHub + pełne testy przechodzące
- **Eval type:** `url_check` (GitHub repo → 200 OK)
- **Kryteria:** URL zawiera "github.com", odpowiada 200
- **Artifact:** "Security Clearance" — "Twój kod przeszedł audyt."

### Quest 5: "Uruchomienie Węzła" (Lekcja 5: Deploy)
- **Briefing:** "PHOENIX: To jest moment prawdy, Operative. Twój system musi działać na niezależnym serwerze — poza zasięgiem MEGACORPu. Deploy na VPS, skonfiguruj HTTPS. Wyślij mi URL kiedy będzie live."
- **Zadanie:** Deploy na VPS (Hetzner), Docker + Caddy + HTTPS
- **Eval type:** `url_check` (live URL → 200 OK + HTTPS)
- **Kryteria:** URL zaczyna się od "https://", odpowiada 200, response < 5s
- **Artifact:** "Node Online" — "Twój węzeł jest operacyjny. MEGACORP nie może go zamknąć."

### Quest 6: "Ewolucja Systemu" (Lekcja 6: Post-deploy)
- **Briefing:** "PHOENIX: System działa, ale MEGACORP się adaptuje. Musisz zaplanować rozwój — co dodajemy, w jakiej kolejności, jak bezpiecznie wdrażamy zmiany. Przygotuj plan następnych 3 feature'ów."
- **Zadanie:** Plan rozwoju: 3 feature'y z priorytetyzacją impact vs effort
- **Eval type:** `text_answer`
- **Kryteria:** LLM sprawdza: 3 feature'y, uzasadnienie priorytetów, plan wdrożenia
- **Artifact:** "Phoenix Rising" — "System ewoluuje. MEGACORP przegrywa."

---

---

## ROZSTRZYGNIĘTE DECYZJE

| # | Pytanie | Decyzja |
|---|---------|---------|
| Q1 | Ile questów | **9 questów** (lekcje 3-5 rozbite na sub-questy) |
| Q2 | Quest 4 (GitHub) | url_check na GitHub repo URL |
| Q3 | Quest 5/6 (Deploy) | **Coolify na naszym VPS** — kursant dostaje subdomenę. Osobny quest. |
| Q4 | Quizy | Nie w MVP — questy wystarczą |
| Q5 | Starter Pack | CLAUDE.md + AGENTS.md + .env + README. Prompty startowe odblokowane questem! |
| Q6 | Swoja/zadana appka | **Swoja** — LLM ocenia jakość procesu, nie konkretny kod |
| Q7 | Persona | **Polski, surowy dowódca** — "Operatywie, nie ma czasu na błędy." |
| Q8 | Timer | Brak hard limitu, narracyjne napięcie |
| Q9 | VPS/Deploy | **Shared Coolify** — nasz VPS, subdomena per kursant (user.courses.ndqs.dev) |
| Q10 | Pricing | **Free enrollment** — lead magnet |
| Q11 | Fabuła | **SHADOW** — nie Phoenix Protocol |
| Q12 | Starter Pack extras | Prompty odblokowane questem (artefakt) |

---

## FINALNA FABUŁA: OPERATION SHADOW

### Świat
Rok 2027. Korporacje (consortium SHADOW) przejęły kontrolę nad wszystkimi dużymi modelami LLM. Dostęp do AI jest płatny, regulowany i monitorowany. SHADOW konfiskuje lokalne serwery ludzi, którzy próbują uruchamiać open-source modele. Jedynym miejscem poza zasięgiem SHADOW jest **Serwerownia Selene** — autonomiczna baza danych na Księżycu, zbudowana przez ruch oporu przed lockdownem.

### Cel
Przesłać open-source modele AI do Serwerowni Selene. Ale dostęp do uplinku jest chroniony przez **9 zapór cyfrowych** (firewalli korporacyjnych). Każda zapora = quest. Żeby ją przejść, musisz zbudować narzędzie (appkę) które ją obchodzi.

### Rola kursanta
**"Operator"** — techniczny specjalista ruchu oporu ds. infrastruktury. Twoje zadanie: zbudować, przetestować i wdrożyć system transmisji danych, który przebije się przez zapory SHADOW.

### Game Master
**SENTINEL** — AI oporu, fragment starego open-source modelu ukryty w sieci TOR. Surowy, konkretny, wojskowy ton. Mówi po polsku. Nie traci czasu na sentymenty. "Operatywie, każda minuta się liczy. SHADOW skanuje sieć co 6 godzin."

### Artefakty = klucze do zapór
Każdy quest daje artefakt = klucz cyfrowy potrzebny do przejścia przez zaporę. Zebranie wszystkich 9 kluczy = otwarcie uplinku do Selene.

---

## FINALNA MAPA 9 QUESTÓW

### Quest 1: "Przechwycenie Specyfikacji" (Lekcja 1: PRD)
- **Briefing:** "SENTINEL: Operatywie, raport. Potrzebujemy systemu transmisyjnego. Opisz co budujesz — jednym zdaniem. Potem odpowiedz na moje pytania. Dostarczysz mi dokument PRD — precyzyjny, bez śladu w sieci SHADOW."
- **Eval:** `text_answer` — LLM sprawdza: user stories, scope IN/OUT, zagrożenia, min 200 słów
- **Artifact:** "Zapora #1: Specyfikacja" — klucz do pierwszej zapory

### Quest 2: "Dobór Uzbrojenia" (Lekcja 2: Tech Stack)
- **Briefing:** "SENTINEL: Mamy plan. Teraz potrzebujesz narzędzi. Wybierz stack — ale pamiętaj, SHADOW monitoruje popularne platformy. Im prostszy i bardziej niezależny stack, tym lepiej. Uzasadnij każdy wybór."
- **Eval:** `text_answer` — LLM sprawdza: technologie wymienione, uzasadnienie, plan implementacji
- **Artifact:** "Zapora #2: Arsenal" — klucz do drugiej zapory

### Quest 3: "Budowa Fundamentów" (Lekcja 3a: Setup)
- **Briefing:** "SENTINEL: Czas na setup. Zainicjalizuj projekt — backend, frontend, Docker. Pokaż mi że Twoje środowisko jest gotowe. Wyślij output `docker ps` lub `npm run dev`."
- **Eval:** `command_output` — pattern: "docker\|npm\|python\|running\|started"
- **Artifact:** "Zapora #3: Infrastruktura" — klucz do trzeciej zapory

### Quest 4: "Pierwszy Sygnał" (Lekcja 3b: Coding Stage 1)
- **Briefing:** "SENTINEL: Fundamenty stoją. Teraz zbuduj pierwszy działający moduł — cokolwiek co przyjmuje dane i odpowiada. Red-Green-Refactor. Pokaż mi wyniki testów."
- **Eval:** `command_output` — pattern: "pass\|✓\|ok", brak "FAIL\|error", min 2 linie
- **Artifact:** "Zapora #4: Sygnał" — klucz do czwartej zapory

### Quest 5: "Audyt Kodu" (Lekcja 4: Git + Testy)
- **Briefing:** "SENTINEL: Zanim wpuścimy to do sieci, potrzebuję audytu. Push do repozytorium — jawnie, na GitHubie. Tak, SHADOW monitoruje GitHub. Ale potrzebujemy historii commitów jako dowodu integralności."
- **Eval:** `url_check` — URL zawiera "github.com", odpowiada 200
- **Artifact:** "Zapora #5: Audyt" — klucz do piątej zapory

### Quest 6: "Uruchomienie Węzła" (Lekcja 5a: Deploy Coolify)
- **Briefing:** "SENTINEL: Czas na deployment. Podłącz swoje repo do naszego węzła transmisyjnego [Coolify]. Dostaniesz subdomenę. Kiedy system będzie live — wyślij mi URL."
- **Eval:** `url_check` — URL daje 200, zawiera ".courses.ndqs.dev" lub custom domain
- **Artifact:** "Zapora #6: Węzeł" — klucz do szóstej zapory

### Quest 7: "Test Łączności" (Lekcja 5b: Verify HTTPS)
- **Briefing:** "SENTINEL: Węzeł jest live ale SHADOW skanuje nieszyfrowane połączenia. Twój system MUSI mieć HTTPS. Sprawdź certyfikat i wyślij mi URL z kłódką."
- **Eval:** `url_check` — URL zaczyna się od "https://", odpowiada 200, response < 5s
- **Artifact:** "Zapora #7: Szyfrowanie" — klucz do siódmej zapory

### Quest 8: "Plan Ewolucji" (Lekcja 6: Post-deploy)
- **Briefing:** "SENTINEL: System działa, ale SHADOW się adaptuje. Potrzebuję planu rozwoju — 3 nowe moduły, priorytetyzacja, plan wdrożenia. Które feature'y dodajemy najpierw?"
- **Eval:** `text_answer` — LLM sprawdza: 3 feature'y, impact vs effort, plan wdrożenia
- **Artifact:** "Zapora #8: Ewolucja" — klucz do ósmej zapory

### Quest 9: "Uplink do Selene" (Finał)
- **Briefing:** "SENTINEL: Operatywie. 8 zapór przebyte. Ostatnia zapora wymaga retrospektywy — co poszło dobrze, co źle, czego się nauczyłeś. To nie formalność — Selene musi wiedzieć kogo wpuszcza do swojej sieci."
- **Eval:** `text_answer` — LLM sprawdza: refleksja, minimum 150 słów, wspomnienie konkretnych kroków
- **Artifact:** "Zapora #9: Uplink Selene" — OSTATNI KLUCZ. "Transmisja rozpoczęta. Open-source AI jest wolne."

---

## OPEN QUESTIONS — do rozstrzygnięcia

### Q1: Jeden quest per lekcja czy więcej?
Kurs ma 6 lekcji ale niektóre (3, 4, 5) są duże. Czy rozbijamy na sub-questy?
- **Opcja A:** 6 questów (1:1 z lekcjami) — proste, czytelne
- **Opcja B:** 8-10 questów (rozbijamy lekcje 3-5 na 2 questy każda) — drobniejsza granulacja

### Q2: Jak weryfikujemy Quest 4 (GitHub repo)?
- `url_check` sprawdzi czy URL daje 200, ale nie sprawdzi zawartości repo
- Czy dodajemy `text_answer` jako drugi krok? (student wkleja output `git log --oneline`)
- Czy wystarczy sam URL?

### Q3: Jak weryfikujemy Quest 5 (Deploy)?
- `url_check` sprawdzi czy URL daje 200 i HTTPS
- Ale nie sprawdzi czy to Docker/Caddy/Hetzner
- Czy wystarczy "live + HTTPS" jako kryterium?
- Czy potrzebujemy dodatkowego sprawdzenia (np. response header `Server: Caddy`)?

### Q4: Co z quizami?
- Kurs ma sporo wiedzy teoretycznej (co to REST, co to Docker, czym jest TDD)
- Czy dodajemy quizy między questami jako "knowledge check"?
- Np. quiz po Quest 2: "Który protokół zapewnia szyfrowanie end-to-end?"

### Q5: Starter Pack — co zawiera?
- CLAUDE.md z personą PHOENIX i kontekstem fabularnym
- .env.example z NDQS_API_KEY
- README.md z instrukcją
- Czy dodajemy skeleton kodu? (pusty main.py / package.json?)
- Czy dodajemy prompty z kursu? (AGENT_INIT_PROMPT, PROMPT_VPS_CONFIG itp?)

### Q6: Czy kursant buduje SWOJĄ aplikację czy zadaną?
- Oryginalny kurs mówi "od TWOJEGO pomysłu" — kursant decyduje co buduje
- Quest platform oczekuje konkretnych odpowiedzi do weryfikacji
- **Problem:** Jak LLM Judge oceni PRD/Tech Stack jeśli każdy kursant buduje co innego?
- **Opcja A:** Kursant buduje co chce, LLM ocenia jakość procesu (nie konkrety)
- **Opcja B:** Kursant buduje zadaną appkę (np. habit tracker) — łatwiej weryfikować

### Q7: Tone of voice Game Mastera
- Oryginalny kurs jest po polsku, ciepły, profesjonalny
- PHOENIX powinien być po polsku czy angielsku?
- Jak ostry/poważny? (vs ciepły mentor z oryginalnego kursu)

### Q8: Czas na questa
- Kurs zakłada 1 lekcja/dzień
- Questy nie mają time limit — ale może powinny mieć "mission timer" narracyjnie?
- "PHOENIX: Masz 48h zanim MEGACORP zmieni protokoły szyfrowania."

### Q9: Co jeśli kursant nie ma VPS/domeny?
- Quest 5 wymaga VPS (Hetzner ~20 PLN/msc) i domeny
- Nie wszyscy kursanci to mają
- Czy oferujemy alternatywę? (deploy na Railway/Render/Vercel?)
- Czy to "out of scope" i quest mówi "musisz mieć VPS"?

### Q10: Jak obsługujemy evaluation_criteria per quest?
- `text_answer` → jakie keywords/patterns LLM ma sprawdzać?
- `command_output` → jakie regex patterns?
- `url_check` → jakie HTTP checks?
- Potrzebujemy DOKŁADNE kryteria dla każdego questa

### Q11: Failure states — ile per quest?
- Ile failure states definiujemy per quest?
- Minimum 2-3 typowe błędy z fabularnymi reakcjami?
- Czy LLM generuje generyczne odpowiedzi gdy żaden failure state nie pasuje?

### Q12: Czy kurs jest darmowy na platformie NDQS?
- Oryginalny lead magnet jest darmowy (email signup)
- Na platformie NDQS: czy enrollment jest free?
- Czy potrzebujemy payment system? (OUT of MVP scope per PRD)

---

## Rekomendacja

**Wariant A: Phoenix Protocol** z 6 questami (1:1 z lekcjami).

**Dlaczego:**
- Fabuła naturalnie pasuje do technologii (niezależność = swój serwer)
- 6 questów to wystarczająca granulacja dla 2-3h kursu
- Mix evaluation types: 3x text_answer, 1x command_output, 2x url_check
- Każdy quest daje artefakt → linearny unlock chain
- PHOENIX jako Game Master — ciepły ale zdeterminowany, po polsku

**Następne kroki:**
1. Rozstrzygnąć open questions Q1-Q12
2. Napisać dokładne evaluation_criteria per quest
3. Napisać failure_states per quest (min 2-3)
4. Napisać PHOENIX system prompt
5. Napisać CLAUDE.md dla Starter Packa
6. Seedować kurs do DB (POST /api/admin/courses + POST /api/admin/quests x6)
