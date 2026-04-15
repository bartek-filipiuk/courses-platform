# Architecture — NDQS Platform

## System Overview

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Next.js 15  │────▶│  FastAPI      │────▶│  PostgreSQL    │
│  (Frontend)  │     │  (Backend)    │     │  (Database)    │
│  Port 3000   │     │  Port 8000    │     │  Port 5432     │
└─────────────┘     └──────┬───────┘     └────────────────┘
                           │
                    ┌──────┴───────┐
                    │              │
               ┌────▼────┐  ┌─────▼─────┐
               │  Redis   │  │ OpenRouter │
               │  Cache   │  │  LLM API   │
               │ Port 6379│  │            │
               └──────────┘  └────────────┘
```

## Backend Modules

| Module | Path | Responsibility |
|--------|------|---------------|
| **auth** | `app/auth/` | OAuth, JWT, API keys, dependencies |
| **courses** | `app/courses/` | Course CRUD, enrollment, starter pack |
| **quests** | `app/quests/` | Quest CRUD, FSM state machine, artifacts |
| **evaluation** | `app/evaluation/` | Submit, hint, LLM Judge, deterministic checks |
| **stats** | `app/stats/` | Comms log, user stats, admin analytics |

## Data Flow: Quest Submission

```
Student submits answer
    → POST /api/quests/{id}/submit
    → Pydantic validation (per evaluation_type)
    → Input sanitization (prompt injection patterns)
    → Deterministic check (if quiz/url_check/command_output)
    → LLM Judge via OpenRouter (if text_answer/url_check/command_output)
    → Result: PASS → mint artifact → unlock dependents → comms log
             FAIL → narrative feedback → comms log
    → Response to student
```

## Database Schema (4 migrations)

- **001**: users (with role enum)
- **002**: courses, enrollments
- **003**: quests, quest_states, artifact_definitions, user_artifacts
- **004**: submissions, comms_log

## Frontend Routes

| Route | Access | Description |
|-------|--------|-------------|
| `/` | Public | Landing page |
| `/login` | Public | GitHub OAuth login |
| `/missions` | Auth | Course catalog |
| `/missions/[id]` | Auth | Course detail + enroll |
| `/quest-map` | Auth | React Flow quest map |
| `/quest/[id]` | Auth | Quest briefing + submit |
| `/inventory` | Auth | Earned artifacts |
| `/comms` | Auth | Communication log |
| `/profile` | Auth | Stats dashboard |
| `/admin/courses` | Admin | Course CRUD |
| `/admin/quests` | Admin | Quest CRUD |
| `/admin/analytics` | Admin | Course metrics |
