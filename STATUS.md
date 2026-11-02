# Vantage — stan weryfikacji (migawka 2026-11-02)

**Rola:** prototyp deny-by-default execution/safety gate w ekosystemie OLA. Repozytorium nie jest dowodem produkcyjnej dostępności usługi.

## Dowody bieżące i ich zakres

- [Vantage Verify, 2026-10-29](https://github.com/krzysztofcieciwa07-ship-it/vantage/actions/runs/40968975127): `success` dla przebiegu na commicie PR `ffed66c8361a...`. Ten przebieg **nie oznacza**, że osobna weryfikacja podpisów się powiodła.
- [Vantage Independent Provenance Verify, 2026-11-02](https://github.com/krzysztofcieciwa07-ship-it/vantage/actions/runs/41539129421): `failure` — **dokładny komunikat**: podpisany workflow ma SAN `verify.yml@refs/pull/10/merge`, a aktualny weryfikator z `main` oczekuje `verify.yml@refs/heads/main`. Nie oznacza to, że podpis jest niepoprawny; oznacza błąd oczekiwanego kontekstu podpisu i brak pozytywnego dowodu niezależnego sprawdzenia. [Proponowana poprawka PR #10](https://github.com/krzysztofcieciwa07-ship-it/vantage/pull/10) jest gotowa do przeglądu, lecz nie jest jeszcze scalona. [Starszy przebieg 2026-10-29](https://github.com/krzysztofcieciwa07-ship-it/vantage/actions/runs/40969041489) zakończył się analogicznym błędem.
- [CFR-18, 2026-10-29](https://github.com/krzysztofcieciwa07-ship-it/vantage/actions/runs/40968949566): `failure` w najnowszym zaobserwowanym przebiegu.
- W README podano historyczny zweryfikowany baseline `3063bcd9268315910e9db4f72a3de1f875019831`. Dotyczy **tylko tego SHA** i nie zastępuje weryfikacji późniejszych zmian.

Dodatkowy problem: [CFR-18 #11](https://github.com/krzysztofcieciwa07-ship-it/vantage/issues/11) — automatyczne przebiegi zgłaszają `failure` przy **zerowej liczbie zadań**. Takiego uruchomienia nie wolno uznawać za przeprowadzony test scenariusza.

## Warunki zdjęcia blokady

1. Odtworzyć failure z niezależnego `workflow_run`, ustalić dokładną przyczynę, nie osłabiając podpisu ani asercji.
2. Wykonać udany przebieg `Vantage Verify`, `Independent Provenance Verify` i wymaganych scenariuszy CFR-18 na jednoznacznie powiązanym commicie/artefakcie.
3. Sprawdzić oddzielnie weryfikację poprawnego artefaktu, artefaktu zmienionego, podpisu niedopasowanego do SHA i braku dowodu.
4. Dopiero potem zaktualizować raport i zatwierdzić część lokalnych wymagań; osobne testy produkcyjne nadal wymagane.

**Stan odbioru:** `BLOCKED` dla pełnego aktualnego łańcucha niezależnej weryfikacji provenance.

## Granice

Kod ma charakter prototypu. Heurystyczna klasyfikacja sygnatur nie jest kompletną ochroną przed atakami. Brak danych o wdrożeniu produkcyjnym pozostaje `UNKNOWN`, nie `PASS`.

[Katalog repozytoriów OLA](https://github.com/krzysztofcieciwa07-ship-it/OLA/blob/main/docs/REPOSITORY_CATALOG.md) — link zacznie prowadzić do nowej dokumentacji po zatwierdzeniu PR w OLA.
