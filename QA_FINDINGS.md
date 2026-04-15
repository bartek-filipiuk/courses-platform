# QA Findings — NDQS Platform Local Testing
**Date:** 2026-04-15
**Tested on:** localhost (backend :8001, frontend :3001, PG :5440, Redis :6379)

---

## CRITICAL

### F1: Hardcoded "demo" tokens in all authenticated pages
**Pages:** `/missions/[id]`, `/quest/[id]`, `/(dashboard)/*`, `/admin/*`
**Issue:** Frontend sends `token: "demo"` to API → 401. Pages requiring auth show error instead of content.
**Fix needed:** Implement proper auth flow (NextAuth session → JWT) or add dev-mode token injection from `GET /api/auth/dev/token/{user_id}`.
**Category:** Function

### F2: CSP blocks non-default API port
**File:** `frontend/next.config.ts:28`
**Issue:** `connect-src` hardcodes `http://localhost:8000`. If backend runs on different port, browser blocks all API calls.
**Fix needed:** Use `NEXT_PUBLIC_API_URL` env var in CSP dynamically.
**Status:** Partially fixed (added 8001 hardcoded too), needs proper dynamic approach.
**Category:** Security/Function

### F3: Alembic migrations fail with asyncpg + Enum
**Files:** All migration files in `backend/alembic/versions/`
**Issue:** `sa.Enum().create(checkfirst=True)` doesn't work with asyncpg driver — throws `DuplicateObjectError`.
**Fix applied:** Replaced all Enum columns with `sa.String(20/30)` in migrations. Application-level ORM still enforces.
**Category:** Function

### F4: `required_artifact_ids` ARRAY(UUID) incompatible with asyncpg
**File:** `backend/alembic/versions/003_*`, `backend/app/quests/models.py`
**Issue:** asyncpg expects Python list, not string `{}` for ARRAY parameters.
**Fix applied:** Changed column from `ARRAY(UUID)` to `JSONB` (list of UUID strings).
**Category:** Function

---

## HIGH

### F5: No navigation / sidebar component
**Issue:** Every page is isolated — no shared sidebar, header, or navigation. User has no way to navigate between pages except manual URL.
**Fix needed:** Create a `(dashboard)/layout.tsx` with sidebar (Missions, Quest Map, Inventory, Comms Log, Profile, Settings).
**Category:** UX

### F6: Courses list endpoint requires auth but should be public
**File:** `backend/app/courses/router.py`
**Issue:** `GET /api/courses` had `Depends(get_current_user_token)` — catalog should be browsable without login.
**Fix applied:** Removed auth dependency from list_courses.
**Category:** Function

### F7: Seed script incomplete — no quests/artifacts/submissions
**File:** `backend/scripts/seed_dev.py`
**Issue:** Original seed only created users + courses. No quests, quest_states, artifacts, submissions, comms_log.
**Fix applied:** Extended seed with 12 quests, 12 artifacts, enrollments, quest_states, submissions, comms_log.
**Category:** Data

### F8: Enrollment doesn't initialize quest states
**File:** `backend/app/courses/router.py` (enroll endpoint)
**Issue:** `initialize_quest_states()` from `state_machine.py` is never called on enrollment.
**Fix needed:** Call `initialize_quest_states(db, user_id, course_id)` after creating enrollment.
**Category:** Function

---

## MEDIUM

### F9: Port 8000 often occupied
**Issue:** Port 8000 commonly used by other services (Django, etc.). Backend should default to different port or be configurable.
**Category:** DevEx

### F10: No global error boundary on frontend
**Issue:** API errors show raw error text. Should have toast notifications (sonner) or error boundary with retry.
**Category:** UX

### F11: Missing cover images on course cards
**Issue:** `cover_image_url` is null in seed data — cards look empty without visual.
**Fix:** Add placeholder/default cover image, or add URLs to seed data.
**Category:** UI

### F12: Comms Log hardcodes courseId="demo"
**File:** `frontend/src/app/(dashboard)/comms/page.tsx:38`
**Issue:** Uses `"/api/courses/demo/comms-log"` — should get courseId from route/context.
**Category:** Function

### F13: Admin forms don't list existing courses/quests
**Issue:** Admin pages only have create forms, no list view of existing items.
**Category:** UX

---

## LOW

### F14: Quality score radar chart uses SVG circles not Recharts
**File:** `frontend/src/app/(dashboard)/profile/page.tsx`
**Issue:** Uses custom SVG circles instead of Recharts RadarChart. Works but not as polished.
**Category:** UI

### F15: Emoji icons instead of proper icons (Lucide)
**Issue:** QuestNode and feature cards use emoji (🎮 🤖 🏆) instead of Lucide/icon library.
**Category:** UI

### F16: Frontend page.test.tsx may break with new page.tsx
**File:** `frontend/src/app/page.test.tsx`
**Issue:** Test was written for old static page, new landing page is `"use client"`.
**Category:** Test

---

## Verified Working

| Page | Status | Notes |
|------|--------|-------|
| Landing `/` | OK | Hero, features, CTA, dark theme, gradients |
| Login `/login` | OK | Terminal aesthetic, GitHub button, "Initializing..." |
| Missions `/missions` | OK | 2 course cards with descriptions, GM names |
| Admin: Courses | OK | Full create form, all fields, publish toggle |
| Admin: Quests | OK | Tabbed form (Story/Technical/Artifact) |
| Backend Health | OK | `{"status":"ok","service":"ndqs-backend"}` |
| API: Courses list | OK | Returns 2 published courses with full data |
| API: User stats | OK | Returns quality scores, progress, streak |
| API: Dev token | OK | Generates valid JWT for testing |
| Swagger UI | OK | Full API docs at `:8001/docs` |

## Screenshots
- `qa-screenshots/01-landing.png` — Landing page (full)
- `qa-screenshots/02-login.png` — Login page
- `qa-screenshots/03-missions-final.png` — Missions catalog with data
- `qa-screenshots/04-admin-courses.png` — Admin course creation form
- `qa-screenshots/05-admin-quests.png` — Admin quest editor (tabbed)
- `qa-screenshots/06-course-detail.png` — Course detail (auth error)
