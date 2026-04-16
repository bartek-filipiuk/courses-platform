"""Course and Enrollment routes."""

import io
import re
import unicodedata
import uuid
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_token
from app.courses.models import Course, Enrollment
from app.courses.schemas import (
    CourseCreate,
    CourseDetailResponse,
    CourseResponse,
    CourseUpdate,
    EnrollmentResponse,
)
from app.database import get_db
from app.rate_limit import ENROLLMENT_RATE_LIMIT, STARTER_PACK_RATE_LIMIT, _get_user_id_or_ip, limiter

router = APIRouter(tags=["courses"])


# --- Admin endpoints ---


def _require_admin(token_data: dict) -> None:
    if token_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


@router.post("/api/admin/courses", status_code=201)
async def create_course(
    body: CourseCreate,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(token_data)
    course = Course(
        id=uuid.uuid4(),
        creator_id=uuid.UUID(token_data["sub"]),
        **body.model_dump(),
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return {"id": str(course.id), "title": course.title, "is_published": course.is_published}


@router.put("/api/admin/courses/{course_id}", response_model=CourseDetailResponse)
async def update_course(
    course_id: uuid.UUID,
    body: CourseUpdate,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> Course:
    _require_admin(token_data)
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    await db.commit()
    await db.refresh(course)
    return course


# --- Public endpoints ---


@router.get("/api/courses", response_model=list[CourseResponse])
async def list_courses(
    db: AsyncSession = Depends(get_db),
) -> list[Course]:
    result = await db.execute(
        select(Course).where(Course.is_published.is_(True)).order_by(Course.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/api/courses/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: uuid.UUID,
    _token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> Course:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


# --- Enrollment ---


@router.post("/api/courses/{course_id}/enroll", status_code=201)
@limiter.limit(ENROLLMENT_RATE_LIMIT, key_func=_get_user_id_or_ip)
async def enroll(
    request: Request,
    course_id: uuid.UUID,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Check course exists and is published
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.is_published:
        raise HTTPException(status_code=400, detail="Course is not published")

    user_id = uuid.UUID(token_data["sub"])

    # Check if already enrolled
    existing = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already enrolled")

    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.add(enrollment)
    await db.commit()

    # Initialize quest states for this user/course (FSM)
    from app.quests.state_machine import initialize_quest_states
    await initialize_quest_states(db, user_id, course_id)

    return {"user_id": str(user_id), "course_id": str(course_id), "status": "enrolled"}


# --- My Enrollments ---


@router.get("/api/users/me/enrollments")
async def list_my_enrollments(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List courses the current user is enrolled in, with progress."""
    user_id = uuid.UUID(token_data["sub"])

    from app.quests.models import Quest, QuestState

    result = await db.execute(
        select(Enrollment, Course)
        .join(Course, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == user_id)
        .order_by(Enrollment.enrolled_at.desc())
    )
    rows = result.all()

    enrollments = []
    for enrollment, course in rows:
        # Get quest progress for this course
        qs_result = await db.execute(
            select(QuestState.state)
            .join(Quest, QuestState.quest_id == Quest.id)
            .where(QuestState.user_id == user_id, Quest.course_id == course.id)
        )
        states = [s for (s,) in qs_result.all()]
        total = len(states)
        completed = sum(1 for s in states if s == "COMPLETED")

        enrollments.append({
            "course_id": str(course.id),
            "title": course.title,
            "narrative_title": course.narrative_title,
            "persona_name": course.persona_name,
            "cover_image_url": course.cover_image_url,
            "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
            "total_quests": total,
            "completed_quests": completed,
            "progress_pct": round(completed / total * 100, 1) if total > 0 else 0,
        })

    return enrollments


# --- Starter Pack ---


@router.get("/api/courses/{course_id}/starter-pack")
@limiter.limit(STARTER_PACK_RATE_LIMIT, key_func=_get_user_id_or_ip)
async def download_starter_pack(
    request: Request,
    course_id: uuid.UUID,
    _token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        persona_label = course.persona_name or "Game Master"
        claude_md = f"""# {course.narrative_title or course.title}

## Twoja rola (dla AI asystenta)

{course.persona_prompt or f"Jesteś {persona_label} — ewaluatorem kursu '{course.title}'."}

## Kontekst świata

{course.global_context or "Postępuj zgodnie z briefingami questów."}

## Zasady komunikacji

1. NIE dawaj gotowych rozwiązań. Metoda sokratyczna — naprowadzaj pytaniami.
2. Zachowuj klimat misji — jesteś w roli {persona_label}.
3. Mów krótko, konkretnie.
4. Gdy Operator prosi o wysłanie odpowiedzi — użyj komend z sekcji "Integracja z NDQS API" poniżej.

---

## Integracja z NDQS API

Wszystkie endpointy wymagają nagłówka `X-API-Key: $NDQS_API_KEY`. Klucz jest w `.env`.

### 1. Co robić teraz? (active quest)

Zawsze zaczynaj od sprawdzenia aktywnego questa:

```bash
curl -s -H "X-API-Key: $NDQS_API_KEY" \\
  "$NDQS_API_URL/api/users/me/active-quest?course_id={course.id}"
```

Odpowiedź zawiera `quest_id`, `briefing`, `evaluation_type`, oraz gotowe `submit_endpoint` /
`submit_file_endpoint` / `hint_endpoint`. Użyj `quest_id` w dalszych wywołaniach.

### 2. Submit — text_answer (Q1, Q2, Q8, Q9 w SHADOW)

```bash
# A) Inline JSON (krótka odpowiedź)
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/submit" \\
  -H "X-API-Key: $NDQS_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"type":"text_answer","payload":{{"answer":"TWÓJ TEKST"}}}}'

# B) Z pliku .md / .txt (np. prd.md, tech_stack.md) — do 100 KB
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/submit/file" \\
  -H "X-API-Key: $NDQS_API_KEY" \\
  -F "file=@prd.md"
```

### 3. Submit — command_output (Q3, Q4 w SHADOW)

```bash
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/submit" \\
  -H "X-API-Key: $NDQS_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"type":"command_output","payload":{{"command":"npm test","output":"PASTE_OUTPUT"}}}}'
```

### 4. Submit — url_check (Q5, Q6, Q7 w SHADOW)

```bash
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/submit" \\
  -H "X-API-Key: $NDQS_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"type":"url_check","payload":{{"url":"https://twoja-app.example.com"}}}}'
```

### 5. Hint (sokratyczna podpowiedź)

```bash
curl -X POST "$NDQS_API_URL/api/quests/QUEST_ID/hint" \\
  -H "X-API-Key: $NDQS_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{"context":"Na czym konkretnie utknąłem — opisz krótko"}}'
```

Każdy quest ma limit hintów (zwykle 3). Po wyczerpaniu endpoint zwraca 429.

### 6. Status i lista questów

```bash
# Stan konkretnego questa
curl -H "X-API-Key: $NDQS_API_KEY" \\
  "$NDQS_API_URL/api/quests/QUEST_ID/status"

# Wszystkie questy w kursie z ich stanami
curl -H "X-API-Key: $NDQS_API_KEY" \\
  "$NDQS_API_URL/api/courses/{course.id}/quests"

# Inventory — zdobyte artefakty
curl -H "X-API-Key: $NDQS_API_KEY" \\
  "$NDQS_API_URL/api/users/me/artifacts"
```

---

## Interpretacja odpowiedzi evaluacji

Submit zwraca JSON:

- `passed: true` → quest zaliczony, w `artifact_earned` jest nazwa artefaktu, w `quests_unlocked` liczba odblokowanych kolejnych questów. `quality_scores` (completeness/understanding/efficiency/creativity, 1-10).
- `passed: false` + `matched_failure: "fs_..."` → konkretny tryb porażki, `narrative_response` ma sokratyczny feedback od {persona_label}. Popraw i submituj ponownie.
- `passed: false` + `evaluation_unavailable: true` → LLM chwilowo niedostępny, quest wraca do IN_PROGRESS, spróbuj za chwilę.
"""
        zf.writestr("CLAUDE.md", claude_md)
        zf.writestr("AGENTS.md", claude_md)  # same content, for Cursor/Windsurf conventions

        env_example = """# NDQS Platform Configuration
NDQS_API_KEY=paste_your_api_key_here
NDQS_API_URL=http://localhost:8002
"""
        zf.writestr(".env.example", env_example)

        readme = f"""# {course.title}

## Quick Start

1. Skopiuj `.env.example` → `.env` i wklej swój API key (Platforma → Profile → Generate API Key).
2. Wrzuć `CLAUDE.md` (lub `AGENTS.md`) do roota swojego projektu.
3. Poproś asystenta (Claude Code / Cursor / Windsurf): **"Sprawdź aktywny quest z NDQS"** — pobierze briefing i podpowie kolejny krok.
4. Pracuj nad questem. Kiedy gotowy, poproś asystenta żeby submitował odpowiedź przez API.

## Jak kursant ma zacząć

Zawsze pierwszy krok: `GET /api/users/me/active-quest?course_id={course.id}` — to mówi co robić TERAZ.

Nie musisz pamiętać ID questów. `active-quest` zwraca to do którego masz przejść + gotowe
endpointy do submit/hint.

## Linki

- Platforma: {course.title}
- API dokumentacja: $NDQS_API_URL/docs (Swagger UI)
- Quest flow: briefing (GET) → pracuj → submit (POST) → pass → artefakt → kolejny odblokowany
"""
        zf.writestr("README.md", readme)

    zip_buffer.seek(0)
    # ASCII slug — HTTP headers default to latin-1 so non-ASCII course titles would 500.
    ascii_title = unicodedata.normalize("NFKD", course.title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")[:30] or "course"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="ndqs-{slug}-starter.zip"'},
    )
