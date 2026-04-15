# Runbook — NDQS Platform

## Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health
# Expected: {"status": "ok", "service": "ndqs-backend"}

# Frontend
curl http://localhost:3000
# Expected: 200 OK with HTML
```

## Common Issues

### Database connection failed
```
asyncpg.exceptions.InvalidPasswordError
```
**Fix**: Check `DATABASE_URL` in `.env`. Ensure PostgreSQL is running: `docker compose ps db`

### Redis connection refused
**Fix**: Check `REDIS_URL` in `.env`. Ensure Redis is running: `docker compose ps redis`

### LLM evaluation timeout
```
OpenRouter timeout after 30s
```
**Fix**: Check `OPENROUTER_API_KEY` validity. Try fallback model. Check OpenRouter status page.

### Migration failed
```bash
# Check current migration state
docker compose exec backend alembic current

# Run pending migrations
docker compose exec backend alembic upgrade head

# Rollback last migration
docker compose exec backend alembic downgrade -1
```

### Rate limit hit (429)
Limits are configured in `app/rate_limit.py`:
- Login: 10/5min per IP
- API key gen: 3/hour per user
- Submit: 5/hour per user per quest
- Hint: 10/hour per user
- Enrollment: 10/hour per user

## Backup & Restore

```bash
# Backup
docker compose exec db pg_dump -U ndqs ndqs > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260415.sql | docker compose exec -T db psql -U ndqs ndqs
```

## Logs

```bash
# Backend logs (structured JSON)
docker compose logs backend --tail 100 -f

# Filter by correlation ID
docker compose logs backend | grep "correlation_id.*abc123"

# Frontend logs
docker compose logs frontend --tail 100 -f
```

## Environment Variables

See `.env.example` for full list with descriptions.

Critical vars: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET`, `OPENROUTER_API_KEY`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
