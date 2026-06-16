# Architektura `Tournament`

`Tournament` to **agregat event-sourcingowy** wzorowany na `Contest`: źródłem prawdy jest append-only log (`_history`). `TournamentState` / `PhaseState` to **immutable projekcje** — wynik `TournamentProjectionEvent` przez `apply(fact)`. `TournamentPolicy` **nie mutuje** stanu; tylko decyduje o eventach.

---

## 1. Składniki

| Element | Rola |
|---------|------|
| `TournamentState` | projekcja turnieju (rejestracja, fazy, dyscyplina) |
| `PhaseState` | projekcja fazy (fixture, outcomes, standings / bracket) |
| `TournamentPolicy` | silnik decyzji: command → eventy, event → reakcje |
| `SportTournamentProfile` | interpreter wyniku, tiebreaker, discipline carryover per sport |
| `TournamentBlueprint` | łańcuch faz macro (liga, knockout, world_cup) |
| `_history` | pełny log turniejowy |

---

## 2. Phase vs Round vs SchedulingMode

- **Phase** = format (RoundRobin, SingleElimination, DoubleElimination)
- **Round** = R16 / QF / SF / F **wewnątrz** jednej Phase knockout
- **SchedulingMode**: `FIXED` | `PROGRESSIVE` | `DRAW_BETWEEN_ROUNDS`

Macro przejście (grupy → puchar) = osobna `PhaseDefinition`. Rundy drabinki **nie** tworzą nowych faz.

---

## 3. Kontrakt Tournament

### Zapis

| API | Semantyka |
|-----|-----------|
| `tournament.handle(command)` | jedyna ścieżka zmian turniejowych |
| `tournament.history` | append-only log |

### Integracja z Contest

| API | Semantyka |
|-----|-----------|
| `Contest.handle(command)` | mutacja meczu (osobny agregat) |
| `contest.get_official_result()` | wejście do `RecordMatchOutcome` / `CorrectMatchOutcome` |
| `MatchProvider` | tworzy `Contest` przy `FixtureScheduled` |

---

## 4. Flow Policy → State

```
TournamentCommand
  → TournamentPolicy.decide → TournamentProjectionEvent
  → TournamentState.apply / PhaseState.apply
  → TournamentPolicy.react → follow-up events (kolejka)
```

---

## 5. Blueprinty

| id | Fazy |
|----|------|
| `league` | 1× RoundRobin (FIXED) |
| `knockout_8` | 1× SingleElimination (PROGRESSIVE) |
| `double_elim_8` | 1× DoubleElimination (PROGRESSIVE) |
| `world_cup` | GroupStage (FIXED) → KnockoutBracket (PROGRESSIVE) |

---

## 6. Kluczowe pliki

| Obszar | Ścieżki |
|--------|---------|
| Aggregate | `src/core/tournament/tournament.py` |
| Policy | `src/core/tournament/tournament_policy.py` |
| State | `src/core/tournament/tournament_state.py`, `phase_state.py` |
| Blueprint | `src/core/tournament/blueprint.py`, `blueprint_factory.py` |
| Sport | `src/sports/*/register_tournament.py` |
