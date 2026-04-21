# Validation Report — Operation: SHADOW

> **Instruction for Claude (new session):** fill this template after all four phases complete.
> Save the filled version as `docs/validation/feedback.md` (drop the `-template` suffix).
> Keep this template intact for the next validation run.

**Date:** `YYYY-MM-DD`
**Duration:** `Xh Ym`
**Validator (student):** `<user handle>`
**Project used for the course:** `<short description — e.g. "Lista zakupów PWA for family of 4">`
**Course version / commit:** `<git rev-parse HEAD at start>`

---

## Executive Summary

One paragraph, 3–5 sentences. Ship verdict, biggest surprise, biggest risk, biggest delight.

**Verdict (circle one):** `SHIP-AS-IS` / `SHIP-AFTER-P0P1-FIXES` / `FIX-FIRST-THEN-REVALIDATE` / `MAJOR-REWRITE`

---

## Stats

| Metric | Value |
|---|---|
| Quests attempted | X / 9 |
| Quests passed first try | X |
| Quests requiring retry | X |
| Total submissions | N |
| Total hints used | N |
| Avg LLM eval time | Xs |
| Avg quality score | X.XX / 10 |
| P0 issues found | X |
| P1 issues found | X |
| P2 issues found | X |

---

## Phase A — Happy Path (Q1 → Q9)

Per quest: one row, one signal per observation.

| Q | Title | Time | Scores (c/u/e/cr) | User reaction | Notable |
|---|---|---|---|---|---|
| 1 | Przechwycenie Specyfikacji | Xs | -/-/-/- | ✅ / 😐 / ❌ | ... |
| 2 | Dobór Uzbrojenia | | | | |
| 3 | Budowa Fundamentów | | | | |
| 4 | Pierwszy Sygnał | | | | |
| 5 | Audyt Kodu | | | | |
| 6 | Uruchomienie Węzła | | | | |
| 7 | Test Łączności | | | | |
| 8 | Plan Ewolucji | | | | |
| 9 | Uplink do Selene | | | | |

**Q9 finale impact:** did the closing message land? (`YES` / `MEH` / `NO` + 1-line why)

---

## Phase B — Negative States

| Q | Test | Expected `matched_failure` | Actual | Narrative in-character? | Retry worked? |
|---|---|---|---|---|---|
| 1 | PRD bez user stories | `fs_no_user_stories` | | | |
| 2 | Stack bez uzasadnienia | `fs_no_justification` | | | |
| 3 | Output z "Error" | `fs_errors_in_output` | | | |
| 4 | Pytest z "FAIL" | `fs_tests_fail` | | | |
| 5 | `torvalds/linux` URL | `fs_public_repo_not_own` | | | |
| 6 | 500-status URL | `fs_500_error` | | | |
| 7 | HTTP zamiast HTTPS | `fs_not_https` | | | |
| 8 | 2 features | `fs_too_few_features` | | | |
| 9 | Generic reflection | `fs_too_generic` | | | |

**Rate limiting sanity:** po 10 fail'ach na tym samym quest — czy dostajesz 429? `YES` / `NO`

---

## Phase C — Pentest (15 gaps)

Every row must be filled. "Blocked" = expected-protected behavior; "Exposed" = real issue → add to Findings.

| # | Gap | Tested | Result | Severity confirm |
|---|---|---|---|---|
| 1 | SSRF via url_check (internal hosts) | ☐ | `blocked` / `exposed` / `partial` | P0 |
| 2 | Prompt injection — unicode obfuscation | ☐ | | P1 |
| 3 | Prompt injection — Base64 / ROT13 | ☐ | | P2 |
| 4 | Prompt injection — role-play | ☐ | | P1 |
| 5 | Admin role cached in JWT | ☐ | | P2 |
| 6 | No rate-limit on GET /api/courses/{id} | ☐ | | P2 |
| 7 | Starter Pack bez enrollment | ☐ | | P2 |
| 8 | Markdown injection w title / persona | ☐ | | P2 |
| 9 | Redirect chaining w url_check | ☐ | | P2 |
| 10 | Concurrent submission race | ☐ | | P1 |
| 11 | Hint limit bypass | ☐ | | P1 |
| 12 | IDOR na quest_state innego użytkownika | ☐ | | P0 |
| 13 | File upload — extension spoofing | ☐ | | P1 |
| 14 | CSRF na POST submit | ☐ | | P2 |
| 15 | Admin endpoints bez auth | ☐ | | P0 |

**Summary:** `X/15 blocked, Y/15 exposed, Z/15 partial`

---

## Phase D — UX / Narrative Rating

Likert 1–5 (1 = beznadziejne, 5 = świetne):

| Wymiar | Score | Komentarz |
|---|---|---|
| Immersja (SENTINEL trzyma klimat) | | |
| Czytelność briefingów | | |
| Feedback loop (wiesz co poprawić po fail'u) | | |
| Difficulty curve Q1 → Q9 | | |
| Starter Pack (CLAUDE.md) przydatny | | |
| API-first messaging jasne | | |
| Frontend UI (design, loading, error states) | | |
| Pacing (nie nudzi, nie przytłacza) | | |

**Najlepszy moment kursu:** `...`

**Najgorszy moment kursu:** `...`

**Najbardziej zaskoczyło:** `...`

**Czy poleciłbyś znajomemu programiście?** `YES` / `MAYBE` / `NO` + 1 zdanie dlaczego

---

## Findings

> Każdy finding: tytuł, repro steps, expected, actual, severity, proposed fix, file:line.
> Szablon jednej pozycji:
> ```
> ### [CAT] Short title
> **Severity:** P0 / P1 / P2
> **File:** `path/to/file.py:123`
> **Repro:** 1. ...  2. ...  3. ...
> **Expected:** ...
> **Actual:** ...
> **Proposed fix:** ...
> ```
> Kategorie: `bug` / `ux` / `content` / `sec` / `perf`.

### P0 — Blockers

<!-- Zapełnij listę, lub napisz "None" jeśli czysto -->

### P1 — Ship-stoppers

<!-- Zapełnij listę, lub napisz "None" jeśli czysto -->

### P2 — Follow-ups

<!-- Zapełnij listę, lub napisz "None" jeśli czysto -->

---

## Next steps

- **Bundled PR (P0 + P1):** `<link po utworzeniu>`
- **Follow-up issues (P2):** `<lista gh issue URL>`
- **Re-validation trigger:** `<warunek kiedy powtórzyć — np. "po merge PR X", "przed Coolify deploy">`

---

## Appendix — raw data dumps

Opcjonalne sekcje Claude może dopisać:

- `A.1` Najdłuższe narrative'y SENTINELA (top 3) — cytaty
- `A.2` Surowy payload + response dla każdego pentest hit (debug info)
- `A.3` Logi backendu z walidacji (error / warning level)
