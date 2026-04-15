# Security — NDQS Platform

## Threat Model (from PRD)

| Threat | Mitigation | Status |
|--------|-----------|--------|
| Prompt injection via submit | Input sanitization (6 regex patterns), system prompt hardening | Implemented |
| API abuse / DDoS | Rate limiting per endpoint (slowapi + Redis) | Implemented |
| XSS via LLM response | CSP headers, output escaping | Implemented |
| Stolen API Key | bcrypt hashing, regeneration, IP logging | Implemented |
| SQL Injection | SQLAlchemy ORM (parameterized queries) | Implemented |
| Secrets in repo | .env + .gitignore, BaseSettings validation | Implemented |
| CSRF | Origin check middleware, SameSite cookies | Implemented |
| Error exposure | Generic 500 in production, sanitized validation errors | Implemented |
| Session hijacking | JWT short-lived (15min), refresh rotation, logout blacklist | Implemented |
| Evaluation replay | Identical payload caching (planned, Redis-based) | Planned |
| Artifact forgery | HMAC SHA256 signatures, server-side generation | Implemented |

## Implemented Security Controls (Baseline #1-9)

1. **Auth + Authorization** — JWT + API Key dual auth, role-based admin middleware
2. **Input Validation** — Pydantic schemas on all endpoints, size limits
3. **SQL Injection** — SQLAlchemy ORM, no raw SQL
4. **XSS Prevention** — CSP headers, no dangerouslySetInnerHTML
5. **Secrets Management** — .env + BaseSettings, .gitignore
6. **CORS + Headers** — Restrictive allowlist, CSP, X-Frame-Options, Referrer-Policy
7. **Password/Token Security** — JWT 15min TTL, bcrypt API keys, refresh rotation
8. **Rate Limiting** — Per-endpoint limits (login, submit, hint, enrollment, starter-pack)
9. **Security Testing** — Negative test cases in each stage

## Known Limitations

- Evaluation replay protection not yet implemented (Redis caching planned)
- API key expiry enforcement not active (field exists, middleware check pending)
- No automated OWASP scanning in CI (manual review only)
- File upload evaluation type not implemented (OUT of MVP scope)
