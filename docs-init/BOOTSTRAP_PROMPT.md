# BOOTSTRAP_PROMPT

Użyj tej instrukcji, aby przygotować pliki startowe w katalogu wskazanym przez użytkownika.

## Cel
Utwórz **dokładnie 4 pliki** w katalogu docelowym użytkownika (bez narzucania dodatkowego podkatalogu):

- `AGENT_INIT_PROMPT.md`
- `ARTIFACT_CHECKLIST.md`
- `VERIFICATION_PROMPT.md`
- `PROMPT_HANDOFF_CHECK.md`

## Kroki do wykonania

1. Zapytaj użytkownika o **katalog docelowy** (pełna ścieżka lub katalog otwarty w IDE).
2. Potwierdź ścieżkę i upewnij się, że masz prawo zapisu.
3. Pobierz treść plików z poniższych URL-i:
   - `https://vibe.devince.dev/prompts/AGENT_INIT_PROMPT.md`
   - `https://vibe.devince.dev/prompts/ARTIFACT_CHECKLIST.md`
   - `https://vibe.devince.dev/prompts/VERIFICATION_PROMPT.md`
   - `https://vibe.devince.dev/prompts/PROMPT_HANDOFF_CHECK.md`
4. Zapisz je w katalogu docelowym użytkownika **pod dokładnie tymi nazwami**:
   - `<katalog_docelowy>/AGENT_INIT_PROMPT.md`
   - `<katalog_docelowy>/ARTIFACT_CHECKLIST.md`
   - `<katalog_docelowy>/VERIFICATION_PROMPT.md`
   - `<katalog_docelowy>/PROMPT_HANDOFF_CHECK.md`
5. Wykonaj self-check:
   - [ ] wszystkie 4 pliki istnieją,
   - [ ] żaden plik nie jest pusty,
   - [ ] nazwy plików są dokładne.
6. Wyświetl użytkownikowi krótkie podsumowanie i zaproponuj następny krok:

```text
Gotowe. Pliki zostały utworzone.
Teraz uruchom agenta w tym katalogu i wklej:
Przeczytaj AGENT_INIT_PROMPT.md i ARTIFACT_CHECKLIST.md. Zacznij.
```

## Dodatkowe narzędzia

Dodatkowe narzędzia (audyt bezpieczeństwa, scoring, autofix) → https://vibe.devince.dev/audyt/

## Ważne zasady

- Nie zmieniaj nazw plików.
- Nie zapisuj plików do stałego folderu typu `init_prompts`.
- Jeśli nie możesz pobrać URL-i, poproś użytkownika o ręczne pobranie plików i wskaż, których dokładnie brakuje.
