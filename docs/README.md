# NDQS Platform — Narrative-Driven Quest Sandbox

IT courses wrapped in narrative gameplay. Quests instead of lessons, artifacts instead of grades, an LLM Game Master instead of checkboxes.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for frontend dev)
- Python 3.12+ (for backend dev)

### 1. Clone and configure
```bash
git clone <repo-url>
cd courses-platform
cp .env.example .env
# Edit .env with your GitHub OAuth credentials and secrets
```

### 2. Run with Docker Compose
```bash
docker compose up --build
```

Services:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 3. Local development (without Docker)

**Backend:**
```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
courses-platform/
├── backend/
│   ├── app/
│   │   ├── auth/           # OAuth, JWT, API Keys
│   │   ├── courses/        # Course CRUD, enrollment (Stage 2)
│   │   ├── quests/         # Quest FSM, submissions (Stage 3)
│   │   ├── evaluation/     # LLM Judge, pipeline (Stage 4)
│   │   ├── config.py       # Pydantic BaseSettings
│   │   ├── database.py     # SQLAlchemy async engine
│   │   ├── main.py         # FastAPI app, middleware, exception handlers
│   │   ├── middleware.py   # Correlation ID, security headers, CSRF
│   │   ├── rate_limit.py   # slowapi rate limiter config
│   │   └── logging.py      # structlog setup
│   ├── alembic/            # Database migrations
│   ├── tests/              # pytest test suite
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router pages
│   │   ├── lib/            # API client, auth, utils
│   │   ├── test/           # Vitest tests
│   │   └── types/          # Shared TypeScript types
│   ├── package.json
│   └── next.config.ts
├── docs/                   # API docs, changelog
├── docker-compose.yml
├── .env.example
├── PRD.md                  # Product Requirements
├── TECH_STACK.md           # Technology decisions
├── STACK_GUIDELINES.md     # Coding standards
└── HANDOFF_STAGES_PLAN.md  # Implementation plan with progress
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12+) |
| Frontend | Next.js 15 (App Router, TypeScript) |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 async |
| Cache | Redis 7 |
| Auth | OAuth (GitHub) + JWT + API Keys |
| UI | shadcn/ui + Tailwind CSS 4 + Framer Motion |
| LLM | OpenRouter (multi-model) |
| Tests | pytest (backend), Vitest + Playwright (frontend) |

## Running Tests

**Backend:**
```bash
cd backend
python -m pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm test
```

## API Documentation

See [docs/API.md](docs/API.md) for endpoint reference.

Interactive Swagger docs available at http://localhost:8000/docs when the backend is running.
