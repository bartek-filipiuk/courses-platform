"""Seed script for SHADOW course — 9 quests with full evaluation config.

Usage:
    python scripts/seed_shadow_course.py
"""

import asyncio
import json
import uuid

from sqlalchemy import text

from app.config import settings
from app.database import async_session_factory

# --- SENTINEL System Prompt ---
SENTINEL_PROMPT = open("courses/shadow/sentinel_prompt.md").read()

GLOBAL_CONTEXT = """Rok 2027. Consortium SHADOW przejęło kontrolę nad dostępem do AI. \
Wszystkie duże modele LLM są płatne, monitorowane i cenzurowane. SHADOW konfiskuje lokalne serwery. \
Ruch oporu przesyła open-source modele do Serwerowni Selene na Księżycu — jedynego miejsca poza zasięgiem SHADOW. \
Dostęp chroniony przez 9 zapór cyfrowych. Każda zapora = quest. Każdy klucz = artefakt."""

# --- Quest definitions ---
QUESTS = [
    {
        "sort_order": 1,
        "title": "Przechwycenie Specyfikacji",
        "skills": ["planning", "prd", "requirements"],
        "evaluation_type": "text_answer",
        "briefing": (
            "SENTINEL: Operatywie, raport. Zapora #1 wymaga dokumentu specyfikacji.\n\n"
            "Twoje zadanie: opisz aplikację, którą budujesz. Jedno zdanie — co to jest. "
            "Potem stwórz PRD — Product Requirements Document. Musi zawierać:\n"
            "- User Stories z kryteriami akceptacji\n"
            "- Scope: co IN, co OUT\n"
            "- Minimum 2 zagrożenia bezpieczeństwa\n\n"
            "Minimum 200 słów. Precyzja, nie objętość. "
            "SHADOW skanuje sieć — masz ograniczony czas na transmisję. Wyślij PRD."
        ),
        "success_response": (
            "SENTINEL: Zapora #1 przebita. Twoja specyfikacja jest solidna — "
            "wiesz co budujesz i dla kogo. Klucz #1 w Twoim posiadaniu. "
            "Nie trać czasu — następna zapora wymaga doboru arsenału technologicznego."
        ),
        "evaluation_criteria": {
            "min_words": 200,
            "required_elements": ["user_stories", "scope", "threats"],
            "llm_instruction": (
                "Sprawdź czy PRD zawiera: (1) minimum 2 user stories z kryteriami akceptacji, "
                "(2) jasny scope IN/OUT, (3) minimum 2 zagrożenia bezpieczeństwa. "
                "Oceniaj jakość PROCESU tworzenia PRD, nie konkretną aplikację."
            ),
        },
        "failure_states": [
            {
                "id": "fs_no_user_stories",
                "trigger": "brak user stories lub kryteriów akceptacji",
                "error_category": "completeness",
                "gm_response": (
                    "SENTINEL: Operatywie, problem. Twój dokument nie ma user stories. "
                    "Jak zamierzasz budować system, którego nie potrafisz opisać z perspektywy użytkownika? "
                    "Kto będzie z tego korzystać? Co dokładnie musi móc zrobić? Popraw i wyślij ponownie."
                ),
            },
            {
                "id": "fs_no_scope",
                "trigger": "brak sekcji scope IN/OUT",
                "error_category": "completeness",
                "gm_response": (
                    "SENTINEL: Bez jasnego scope budujesz w ciemno. Co jest IN a co OUT? "
                    "SHADOW szuka nadmiarowych systemów — im mniejszy footprint, tym trudniej nas namierzyć. "
                    "Zdefiniuj granice."
                ),
            },
            {
                "id": "fs_too_short",
                "trigger": "mniej niż 200 słów",
                "error_category": "effort",
                "gm_response": (
                    "SENTINEL: To za mało, Operatywie. Specyfikacja musi być precyzyjna. "
                    "200 słów to minimum — nie dla biurokracji, ale żebyś sam wiedział co budujesz. "
                    "Rozwiń user stories i zagrożenia."
                ),
            },
        ],
        "artifact_name": "Zapora #1: Specyfikacja",
        "artifact_description": "Klucz do pierwszej zapory. Wiesz dokładnie co budujesz.",
        "max_hints": 3,
        "required_artifact_ids": [],
    },
    {
        "sort_order": 2,
        "title": "Dobór Uzbrojenia",
        "skills": ["architecture", "tech-stack", "planning"],
        "evaluation_type": "text_answer",
        "briefing": (
            "SENTINEL: Zapora #2 — dobór arsenału.\n\n"
            "Na podstawie PRD z poprzedniej misji — wybierz tech stack. "
            "Backend, frontend, baza danych, deployment. Uzasadnij KAŻDY wybór. "
            "SHADOW monitoruje popularne platformy — im prostszy i bardziej niezależny stack, tym lepiej.\n\n"
            "Stwórz też plan implementacji podzielony na etapy (vertical slices). "
            "Co budujesz najpierw? Co potem?\n\n"
            "Minimum 3 technologie z uzasadnieniem + plan w etapach."
        ),
        "success_response": (
            "SENTINEL: Zapora #2 przebita. Arsenal dobrany. Plan jest solidny — "
            "wiesz czym budujesz i w jakiej kolejności. Klucz #2 w posiadaniu. "
            "Czas na budowę fundamentów. Ruszaj."
        ),
        "evaluation_criteria": {
            "min_words": 100,
            "required_elements": ["technologies", "justification", "stages"],
            "llm_instruction": (
                "Sprawdź: (1) min 3 technologie wymienione, (2) uzasadnienie wyboru każdej, "
                "(3) plan implementacji w min 2 etapach. "
                "Akceptuj dowolny stack — oceniaj logikę wyboru, nie konkretne technologie."
            ),
        },
        "failure_states": [
            {
                "id": "fs_no_justification",
                "trigger": "technologie bez uzasadnienia",
                "error_category": "reasoning",
                "gm_response": (
                    "SENTINEL: Wybrałeś narzędzia, ale nie powiedziałeś DLACZEGO. "
                    "Każdy wybór musi mieć powód. Dlaczego ten framework a nie inny? "
                    "Co zyskujesz? SHADOW szuka nieprzemyślanych systemów — uzasadnij."
                ),
            },
            {
                "id": "fs_no_plan",
                "trigger": "brak planu etapów",
                "error_category": "completeness",
                "gm_response": (
                    "SENTINEL: Masz narzędzia ale nie masz planu. "
                    "Co budujesz NAJPIERW? W jakiej kolejności? Vertical slices — nie próbuj budować wszystkiego naraz."
                ),
            },
        ],
        "artifact_name": "Zapora #2: Arsenal",
        "artifact_description": "Klucz do drugiej zapory. Twój zestaw narzędzi jest gotowy.",
        "max_hints": 3,
        "required_artifact_ids": [],  # filled dynamically
    },
    {
        "sort_order": 3,
        "title": "Budowa Fundamentów",
        "skills": ["setup", "docker", "scaffold"],
        "evaluation_type": "command_output",
        "briefing": (
            "SENTINEL: Zapora #3 — infrastruktura.\n\n"
            "Zainicjalizuj projekt. Backend, frontend, Docker jeśli używasz. "
            "Pokaż mi że Twoje środowisko jest gotowe — "
            "wyślij output z uruchomienia serwera deweloperskiego.\n\n"
            "Polecenie: uruchom swój serwer (`npm run dev`, `python manage.py runserver`, `uvicorn`, cokolwiek) "
            "i wklej output. Muszę widzieć że startuje bez błędów."
        ),
        "success_response": (
            "SENTINEL: Zapora #3 przebita. Fundamenty stoją — serwer startuje czysto. "
            "Klucz #3 w posiadaniu. Czas zbudować pierwszy działający moduł."
        ),
        "evaluation_criteria": {
            "expected_patterns": [
                "(running|started|listening|ready|Uvicorn|localhost|127\\.0\\.0\\.1|:3000|:8000|:5173)",
            ],
            "forbidden_patterns": [
                "(Error|FATAL|Cannot find module|ModuleNotFoundError|SyntaxError)",
            ],
        },
        "failure_states": [
            {
                "id": "fs_not_running",
                "trigger": "brak dowodu uruchomienia serwera",
                "error_category": "setup",
                "gm_response": (
                    "SENTINEL: Nie widzę potwierdzenia że serwer działa. "
                    "Potrzebuję output z terminala — linia 'listening on' lub 'started'. "
                    "Uruchom serwer i wklej output."
                ),
            },
            {
                "id": "fs_errors_in_output",
                "trigger": "Error lub FATAL w output",
                "error_category": "setup",
                "gm_response": (
                    "SENTINEL: Twój serwer rzuca błędy. SHADOW namierza niestabilne systemy. "
                    "Sprawdź logi — co dokładnie nie działa? Napraw i spróbuj ponownie."
                ),
            },
        ],
        "artifact_name": "Zapora #3: Infrastruktura",
        "artifact_description": "Klucz do trzeciej zapory. Twoje środowisko jest operacyjne.",
        "max_hints": 3,
        "required_artifact_ids": [],
    },
    {
        "sort_order": 4,
        "title": "Pierwszy Sygnał",
        "skills": ["tdd", "testing", "coding"],
        "evaluation_type": "command_output",
        "briefing": (
            "SENTINEL: Zapora #4 — pierwszy działający moduł.\n\n"
            "Zbuduj cokolwiek co DZIAŁA i jest PRZETESTOWANE. "
            "Endpoint API, komponent UI, funkcja — cokolwiek z Twojego Stage 1. "
            "Ale MUSI mieć testy. Red-Green-Refactor.\n\n"
            "Uruchom testy i wyślij mi output. "
            "Potrzebuję widzieć: co najmniej 2 testy przechodzące, zero FAIL."
        ),
        "success_response": (
            "SENTINEL: Zapora #4 przebita. Pierwszy sygnał nadany — Twój system żyje i jest przetestowany. "
            "Klucz #4 w posiadaniu. SHADOW nie wykrył transmisji. Imponujące."
        ),
        "evaluation_criteria": {
            "expected_patterns": [
                "(pass|passed|✓|ok|PASSED|tests? passed)",
                "(\\d+\\s*(test|spec|passed))",
            ],
            "forbidden_patterns": [
                "(FAIL|FAILED|ERROR|error|✗|✘)",
            ],
        },
        "failure_states": [
            {
                "id": "fs_tests_fail",
                "trigger": "FAIL lub ERROR w output",
                "error_category": "testing",
                "gm_response": (
                    "SENTINEL: Testy padają. Niestabilny system to zaproszenie dla SHADOW. "
                    "Przeczytaj error message — co dokładnie nie przechodzi? "
                    "Napraw i uruchom ponownie."
                ),
            },
            {
                "id": "fs_no_tests",
                "trigger": "brak dowodu testów",
                "error_category": "process",
                "gm_response": (
                    "SENTINEL: Nie widzę testów. Kod bez testów to kod, któremu nie ufamy. "
                    "Red-Green-Refactor, Operatywie. Napisz test NAJPIERW, potem kod."
                ),
            },
        ],
        "artifact_name": "Zapora #4: Sygnał",
        "artifact_description": "Klucz do czwartej zapory. Twój system żyje i jest przetestowany.",
        "max_hints": 3,
        "required_artifact_ids": [],
    },
    {
        "sort_order": 5,
        "title": "Audyt Kodu",
        "skills": ["git", "github", "code-review"],
        "evaluation_type": "url_check",
        "briefing": (
            "SENTINEL: Zapora #5 — audyt.\n\n"
            "Twój kod musi być w repozytorium — jawnie, na GitHubie. "
            "Tak, SHADOW monitoruje GitHub. Ale potrzebujemy historii commitów "
            "jako dowodu integralności systemu.\n\n"
            "Push do GitHub i wyślij mi URL repozytorium. "
            "Musi być publiczne (na razie) i odpowiadać HTTP 200."
        ),
        "success_response": (
            "SENTINEL: Zapora #5 przebita. Repozytorium zweryfikowane — historia commitów czysta. "
            "Klucz #5 w posiadaniu. Czas na deployment. To będzie najtrudniejsza zapora."
        ),
        "evaluation_criteria": {
            "method": "GET",
            "expected_status": 200,
            "body_contains": None,
            "llm_instruction": (
                "Zweryfikuj czy URL to github.com. Dodatkowo sprawdź, czy repo przypomina WŁASNĄ pracę kursanta "
                "nad aplikacją z poprzednich questów — patrz na ścieżkę (user/repo-name). "
                "Jeśli to znany duży publiczny projekt (np. torvalds/linux, facebook/react, vercel/next.js, "
                "microsoft/vscode, kubernetes/kubernetes, django/django, angular/angular, itp.) — "
                "zwróć passed=false z matched_failure=fs_public_repo_not_own. "
                "Kursant miał wysłać swoje repo z aplikacji, nie cudze."
            ),
        },
        "failure_states": [
            {
                "id": "fs_repo_not_found",
                "trigger": "404 lub URL nie zawiera github.com",
                "error_category": "setup",
                "gm_response": (
                    "SENTINEL: Repozytorium nie istnieje lub nie jest publiczne. "
                    "Sprawdź URL — musi być format github.com/user/repo. "
                    "Upewnij się że jest publiczne (Settings → Danger Zone → Change visibility)."
                ),
            },
            {
                "id": "fs_not_github",
                "trigger": "URL nie zawiera github.com",
                "error_category": "format",
                "gm_response": (
                    "SENTINEL: Potrzebuję URL do GitHuba — github.com/twój-user/twój-repo. "
                    "Nie gitlab, nie bitbucket. GitHub — tam mamy nasze kanały."
                ),
            },
            {
                "id": "fs_public_repo_not_own",
                "trigger": "URL prowadzi do znanego popularnego publicznego repo (linux kernel, react, next.js, django itp.), a nie do własnego projektu kursanta",
                "error_category": "authenticity",
                "gm_response": (
                    "SENTINEL: Operatywie, znam ten repozytorium. "
                    "To nie Twoja praca — to znany publiczny projekt. "
                    "Potrzebuję TWOJEGO kodu: repo które sam założyłeś, z aplikacją którą projektowałeś w Zaporach #1-#4. "
                    "Historia commitów musi pokazywać Twoją pracę. Wyślij poprawny URL."
                ),
            },
        ],
        "artifact_name": "Zapora #5: Audyt",
        "artifact_description": "Klucz do piątej zapory. Twój kod przeszedł audyt.",
        "max_hints": 3,
        "required_artifact_ids": [],
    },
    {
        "sort_order": 6,
        "title": "Uruchomienie Węzła",
        "skills": ["deployment", "coolify", "devops"],
        "evaluation_type": "url_check",
        "briefing": (
            "SENTINEL: Zapora #6 — deployment.\n\n"
            "Czas na wdrożenie. Podłącz swoje repozytorium GitHub do naszego węzła transmisyjnego. "
            "Dostaniesz subdomenę na naszym serwerze.\n\n"
            "Kiedy Twoja aplikacja będzie live — wyślij mi URL. "
            "Muszę widzieć HTTP 200."
        ),
        "success_response": (
            "SENTINEL: Zapora #6 przebita. Węzeł operacyjny — Twoja aplikacja jest live. "
            "Klucz #6 w posiadaniu. Ale SHADOW skanuje nieszyfrowane połączenia. "
            "Następna zapora: HTTPS."
        ),
        "evaluation_criteria": {
            "method": "GET",
            "expected_status": 200,
        },
        "failure_states": [
            {
                "id": "fs_not_live",
                "trigger": "URL nie odpowiada lub timeout",
                "error_category": "deployment",
                "gm_response": (
                    "SENTINEL: Twoja aplikacja nie odpowiada. Timeout. "
                    "Sprawdź logi deploymentu — czy build przeszedł? "
                    "Czy port jest poprawny? Czy serwer nasłuchuje na 0.0.0.0, nie localhost?"
                ),
            },
            {
                "id": "fs_500_error",
                "trigger": "HTTP 500",
                "error_category": "deployment",
                "gm_response": (
                    "SENTINEL: Serwer odpowiada 500 — Internal Server Error. "
                    "Aplikacja deployowała się, ale coś jest nie tak. Sprawdź zmienne środowiskowe "
                    "i połączenie z bazą danych. Logi Ci powiedzą co."
                ),
            },
        ],
        "artifact_name": "Zapora #6: Węzeł",
        "artifact_description": "Klucz do szóstej zapory. Twoja aplikacja jest live.",
        "max_hints": 5,
        "required_artifact_ids": [],
    },
    {
        "sort_order": 7,
        "title": "Test Łączności",
        "skills": ["https", "ssl", "security"],
        "evaluation_type": "url_check",
        "briefing": (
            "SENTINEL: Zapora #7 — szyfrowanie.\n\n"
            "SHADOW skanuje nieszyfrowane połączenia. Twój system MUSI mieć HTTPS. "
            "Certyfikat SSL — automatyczny przez Caddy/Coolify lub Let's Encrypt.\n\n"
            "Wyślij mi URL zaczynający się od https://. "
            "Musi odpowiadać 200 i mieć ważny certyfikat."
        ),
        "success_response": (
            "SENTINEL: Zapora #7 przebita. Połączenie szyfrowane — SHADOW nie może przechwycić transmisji. "
            "Klucz #7 w posiadaniu. Zostały dwie zapory. Prawie na miejscu, Operatywie."
        ),
        "evaluation_criteria": {
            "method": "GET",
            "expected_status": 200,
        },
        "failure_states": [
            {
                "id": "fs_not_https",
                "trigger": "URL nie zaczyna się od https://",
                "error_category": "security",
                "gm_response": (
                    "SENTINEL: HTTP, nie HTTPS. To jak wysyłanie raportów pocztą otwartą — "
                    "SHADOW przechwyci wszystko. Skonfiguruj certyfikat SSL. "
                    "Caddy robi to automatycznie. Coolify też."
                ),
            },
            {
                "id": "fs_cert_invalid",
                "trigger": "certyfikat nieważny lub self-signed",
                "error_category": "security",
                "gm_response": (
                    "SENTINEL: Certyfikat jest nieważny. Self-signed nie wystarczy — "
                    "przeglądarka go odrzuci, a SHADOW oznaczy jako podejrzany. "
                    "Użyj Let's Encrypt — darmowy i automatyczny."
                ),
            },
        ],
        "artifact_name": "Zapora #7: Szyfrowanie",
        "artifact_description": "Klucz do siódmej zapory. Twoje połączenie jest szyfrowane.",
        "max_hints": 3,
        "required_artifact_ids": [],
    },
    {
        "sort_order": 8,
        "title": "Plan Ewolucji",
        "skills": ["planning", "product", "prioritization"],
        "evaluation_type": "text_answer",
        "briefing": (
            "SENTINEL: Zapora #8 — ewolucja.\n\n"
            "System działa, ale SHADOW się adaptuje. Musisz zaplanować rozwój.\n\n"
            "Przygotuj plan 3 nowych feature'ów do Twojej aplikacji:\n"
            "- Co to jest (1-2 zdania)\n"
            "- Impact vs Effort (wysoki/średni/niski)\n"
            "- Kolejność wdrażania i dlaczego\n\n"
            "Minimum 150 słów. Myśl strategicznie — co daje największą wartość najmniejszym kosztem?"
        ),
        "success_response": (
            "SENTINEL: Zapora #8 przebita. Twój plan ewolucji jest przemyślany — "
            "priorytetyzujesz jak profesjonalista. Klucz #8 w posiadaniu. "
            "Ostatnia zapora. Przygotuj się na retrospektywę."
        ),
        "evaluation_criteria": {
            "min_words": 150,
            "required_count": 3,
            "llm_instruction": (
                "Sprawdź: (1) 3 feature'y opisane, (2) priorytetyzacja impact vs effort, "
                "(3) uzasadniona kolejność wdrażania. "
                "Akceptuj dowolne feature'y — oceniaj jakość myślenia strategicznego."
            ),
        },
        "failure_states": [
            {
                "id": "fs_too_few_features",
                "trigger": "mniej niż 3 feature'y",
                "error_category": "completeness",
                "gm_response": (
                    "SENTINEL: Potrzebuję 3 feature'y. SHADOW nie czeka — "
                    "musisz mieć plan na kilka ruchów do przodu. Dodaj brakujące i wyślij ponownie."
                ),
            },
            {
                "id": "fs_no_prioritization",
                "trigger": "brak priorytetyzacji impact/effort",
                "error_category": "reasoning",
                "gm_response": (
                    "SENTINEL: Feature'y są, ale nie widzę priorytetyzacji. "
                    "Co daje NAJWIĘKSZY impact przy NAJMNIEJSZYM effort? "
                    "W ruchu oporu nie mamy zasobów na wszystko naraz."
                ),
            },
        ],
        "artifact_name": "Zapora #8: Ewolucja",
        "artifact_description": "Klucz do ósmej zapory. Twój system ewoluuje.",
        "max_hints": 3,
        "required_artifact_ids": [],
    },
    {
        "sort_order": 9,
        "title": "Uplink do Selene",
        "skills": ["reflection", "communication", "meta-learning"],
        "evaluation_type": "text_answer",
        "briefing": (
            "SENTINEL: Ostatnia zapora — #9.\n\n"
            "Operatywie, 8 zapór przebytych. Ostatni klucz wymaga czegoś innego — retrospektywy.\n\n"
            "Selene musi wiedzieć kogo wpuszcza do swojej sieci. Napisz:\n"
            "- Co poszło dobrze w Twojej misji?\n"
            "- Co było najtrudniejsze?\n"
            "- Czego się nauczyłeś?\n"
            "- Co zrobiłbyś inaczej?\n\n"
            "Minimum 150 słów. Szczerze. To nie formalność — to Twój dowód że potrafisz się uczyć."
        ),
        "success_response": (
            "SENTINEL: Zapora #9 przebita. Uplink otwarty.\n\n"
            "Operatywie... transmisja rozpoczęta. Open-source modele AI są przesyłane "
            "do Serwerowni Selene. SHADOW nie może ich dosięgnąć.\n\n"
            "Zbudowałeś system od zera — od pomysłu do produkcji. "
            "PRD, tech stack, kod, testy, deployment, HTTPS, plan rozwoju. "
            "To są prawdziwe umiejętności. Nikt Ci ich nie odbierze.\n\n"
            "Dobra robota, Operatywie. Naprawdę dobra robota.\n\n"
            "SENTINEL — koniec transmisji."
        ),
        "evaluation_criteria": {
            "min_words": 150,
            "llm_instruction": (
                "Sprawdź: (1) refleksja jest konkretna (wspomina specyficzne kroki/wyzwania), "
                "(2) minimum 150 słów, (3) wspomina co poszło dobrze I co było trudne. "
                "Bądź hojny — to finał misji. Jeśli kursant napisał szczerą refleksję, zalicz."
            ),
        },
        "failure_states": [
            {
                "id": "fs_too_short",
                "trigger": "mniej niż 150 słów",
                "error_category": "effort",
                "gm_response": (
                    "SENTINEL: Za krótko, Operatywie. Selene potrzebuje więcej. "
                    "Rozwiń — co konkretnie było najtrudniejsze? Co zaskoczyło?"
                ),
            },
            {
                "id": "fs_too_generic",
                "trigger": "ogólniki bez konkretów",
                "error_category": "depth",
                "gm_response": (
                    "SENTINEL: To są ogólniki. 'Nauczyłem się dużo' nic nie mówi. "
                    "CO konkretnie? Który moment? Który error? Który przełom? "
                    "Selene potrzebuje konkretów."
                ),
            },
        ],
        "artifact_name": "Zapora #9: Uplink Selene",
        "artifact_description": "Ostatni klucz. Transmisja rozpoczęta. Open-source AI jest wolne.",
        "max_hints": 3,
        "required_artifact_ids": [],
    },
]


async def seed_shadow() -> None:
    async with async_session_factory() as db:
        # Check if SHADOW course already exists
        result = await db.execute(
            text("SELECT id FROM courses WHERE narrative_title = 'Operation: SHADOW'")
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"SHADOW course already exists (id: {existing}). Skipping.")
            return

        # Get admin user
        admin_result = await db.execute(
            text("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        )
        admin_id = admin_result.scalar_one_or_none()
        if not admin_id:
            print("No admin user found. Run seed_dev.py first.")
            return

        # Create course
        course_id = uuid.uuid4()
        await db.execute(
            text("""
                INSERT INTO courses (id, creator_id, title, narrative_title, description,
                    global_context, persona_name, persona_prompt, model_id, is_published)
                VALUES (:id, :creator, :title, :ntitle, :desc, :ctx, :pname, :pprompt, :model, true)
            """),
            {
                "id": str(course_id),
                "creator": str(admin_id),
                "title": "Od pomysłu do deploy w weekend",
                "ntitle": "Operation: SHADOW",
                "desc": (
                    "Zbuduj i wdróż swoją web aplikację od zera — od pomysłu do produkcji. "
                    "9 questów, 9 zapór cyfrowych korporacji SHADOW. "
                    "Twój cel: przesłać open-source modele AI do Serwerowni Selene na Księżycu."
                ),
                "ctx": GLOBAL_CONTEXT,
                "pname": "SENTINEL",
                "pprompt": SENTINEL_PROMPT,
                "model": "anthropic/claude-sonnet-4-6",
            },
        )
        print(f"Created course: Operation SHADOW (id: {course_id})")

        # Create quests + artifacts
        artifact_ids = []
        quest_ids = []

        for i, q in enumerate(QUESTS):
            qid = uuid.uuid4()
            aid = uuid.uuid4()

            # Build required_artifact_ids (linear chain: each quest requires previous artifact)
            required = [str(artifact_ids[i - 1])] if i > 0 else []

            await db.execute(
                text("""
                    INSERT INTO quests (id, course_id, sort_order, title, briefing, evaluation_type,
                        skills, success_response, evaluation_criteria, failure_states, max_hints,
                        required_artifact_ids)
                    VALUES (:id, :cid, :ord, :title, :brief, :etype,
                        cast(:skills as jsonb), :success, cast(:criteria as jsonb),
                        cast(:failures as jsonb), :hints, cast(:req as jsonb))
                """),
                {
                    "id": str(qid),
                    "cid": str(course_id),
                    "ord": q["sort_order"],
                    "title": q["title"],
                    "brief": q["briefing"],
                    "etype": q["evaluation_type"],
                    "skills": json.dumps(q["skills"]),
                    "success": q["success_response"],
                    "criteria": json.dumps(q["evaluation_criteria"]),
                    "failures": json.dumps(q["failure_states"]),
                    "hints": q["max_hints"],
                    "req": json.dumps(required),
                },
            )

            await db.execute(
                text("""
                    INSERT INTO artifact_definitions (id, course_id, quest_id, name, description)
                    VALUES (:id, :cid, :qid, :name, :desc)
                """),
                {
                    "id": str(aid),
                    "cid": str(course_id),
                    "qid": str(qid),
                    "name": q["artifact_name"],
                    "desc": q["artifact_description"],
                },
            )

            quest_ids.append(qid)
            artifact_ids.append(aid)

        await db.commit()
        print(f"Created 9 quests + 9 artifacts (linear chain)")
        print(f"\nCourse ID: {course_id}")
        print(f"Quest IDs: {[str(q) for q in quest_ids]}")
        print(f"Artifact IDs: {[str(a) for a in artifact_ids]}")
        print(f"\nSHADOW course ready! Enroll a student to start.")


if __name__ == "__main__":
    asyncio.run(seed_shadow())
