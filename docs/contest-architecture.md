# Architektura `Contest`

`Contest` to **agregat event-sourcingowy**: źródłem prawdy jest append-only log (`_history`). `current_state` to **immutable projekcja** — wynik złożenia `ProjectionEvent` przez `apply(fact) → Self`. `RuleSet` **nie mutuje** stanu; tylko decyduje, jakie fakty powstały. Wynik sportowy buduje **`ResultBuilder` on-the-fly** — bez cache na agregacie.

---

## 1. Składniki i tworzenie contestu

**Aggregate składa się z:**

| Element | Rola |
|---------|------|
| `ContestState` | immutable projekcja meczu (`@runtime_checkable` Protocol) |
| `RuleSet` | silnik decyzji: command → eventy, event → reakcje |
| `ResultBuilder` | materializuje `ContestResult` ze stanu (ABC) |
| `_history` | pełny log (`ProjectionEvent`, `OfficialOverrideEvent`, `EventReversed`) |

**Tworzenie** idzie przez `ContestFactory` — każdy sport rejestruje builder zwracający `ContestAssembly`.

**Rehydratacja** z zapisanego logu: `Contest.from_events()` → replay przez `_rebuild_state()`.

**Implementacja stanu:** każdy sport definiuje własną projekcję jako **jawną implementację** protokołu core — np. `class FootballContestState(ContestState): ...`. Nie polegamy na duck typingu; kontrakt (`is_finished`, `contestants`, `apply`, `reset`) musi być zadeklarowany przez dziedziczenie z `ContestState`.

---

## 2. Hierarchia eventów

Wspólny korzeń domeny: [`src/core/event.py`](../src/core/event.py) — `Event(event_id, occurred_at, caused_by)`.

```python
Event                          # src/core/event.py
├── TournamentEvent            # src/core/tournament/event.py
│   ├── RegistrationOpened / RegistrationClosed
│   ├── ContestantRegistered
│   ├── PhaseStarted / PhaseCompleted
│   ├── FixtureScheduled
│   ├── MatchOutcomeRecorded
│   └── TournamentCompleted
└── ContestEvent               # src/core/contest/event.py
    ├── ProjectionEvent        # fakt boiskowy — mutuje current_state (apply)
    ├── OfficialOverrideEvent  # decyzja administracyjna — tylko audyt w logu
    └── EventReversed          # meta: wycofanie wcześniejszego eventu
        └── sport events (FootballEvent, GoalScored, ContestResultOverridden, …)
```

Sport dziedziczy przez własne bazy, np. `FootballEvent(ProjectionEvent)`, `ContestResultOverridden(OfficialOverrideEvent)`.

**Przykłady:**

| Typ | Football | Darts |
|-----|----------|-------|
| Projection | `GoalScored`, `MatchConcluded`, `GoalScorerCorrected` | `DartScored`, `MatchConcluded` |
| Walkover command | `AwardWalkover(winner_id, reason)` | `AwardWalkover(winner_id, reason)` |
| Override event | `ContestResultOverridden` | `ContestResultOverridden` |

`Contest._record_event`: `OfficialOverrideEvent` → append bez `apply`; `ProjectionEvent` → `apply` + append.

Sport-specific `isinstance` (np. `ContestResultOverridden`) **tylko** w `ResultBuilder` sportu — core używa wyłącznie markerów `OfficialOverrideEvent` / `ProjectionEvent`.

Replay (`_rebuild_state`) używa wyłącznie `_effective_base_events()` (aktywne `ProjectionEvent`).

---

## 3. Kontrakt Contest (canonical)

### Zapis

| API | Semantyka |
|-----|-----------|
| `contest.handle(command)` | Jedyna ścieżka zmian (gole, walkover, korekty) |
| `contest.history` | Pełny append-only log |

### Odczyt wyniku

Guard: **`current_state.is_finished`** (jedyny).

| API | Semantyka |
|-----|-----------|
| `get_played_result()` | `ResultBuilder.build(state)` — wynik z boiska |
| `get_official_result()` | `build(state)` lub `build_official(state, last_override)` |

### Odczyt stanu / reversal

| API | Semantyka |
|-----|-----------|
| `current_state` | Projekcja z `_effective_base_events()` |
| `active_domain_events()` | Aktywne `ProjectionEvent` (kandydaci reversal) |

### Walkover — trzy ścieżki

| Sytuacja | Event | Mutacja stanu |
|----------|-------|---------------|
| Pre-match forfeit | `MatchConcluded` (`ProjectionEvent`) | `apply` — `winner_id`, `decided_by=reason` |
| Post-match override | `ContestResultOverridden` (`OfficialOverrideEvent`) | tylko append (audit); wynik via `build_official()` |
| In-match (np. za mało graczy) | `MatchConcluded(decided_by=walkover_…)` | `apply` |

Korekty po meczu (np. `CorrectGoalScorer`): osobny command → `GoalScorerCorrected` (`ProjectionEvent` + applier).

Football: command/override mogą nadać `winner_score`/`loser_score`. Oba sporty: `*AdminRules` mixin + `_own_command_handlers`; `register_contest` podaje `build_*_reversal_chain()`.

---

## 4. Flow obsługi command

```python
def _handle_domain_command(self, command: Command) -> list[Event]:
    queue = list(self._ruleset.decide(command, self.current_state, self._history))
    while queue:
        fact = queue.pop(0)
        self._record_event(fact)  # apply lub audit
        for reaction in self._ruleset.react(fact, self.current_state):
            queue.append(replace(reaction, caused_by=fact.event_id))
```

**Ważne:** `RuleSet` czyta `state` i `history`; mutacja danych z eventów jest po stronie `State.apply`.

---

## 5. `ResultBuilder` (ABC)

```python
class ResultBuilder(ABC):
    def build(self, state: ContestState) -> ContestResult: ...
    def build_official(
        self, state: ContestState, override: OfficialOverrideEvent
    ) -> ContestResult: ...
```

`build_official` wołane tylko gdy w logu jest aktywny override. Football: ranking/scores z eventu, metryki graczy ze stanu (kartki zostają).

### Rankingi — ex-aequo, bez tiebreakerów

`RankedEntry.place` odzwierciedla **jawnie ustalony wynik meczu**, nie sortuje uczestników po statystykach pomocniczych.

| Sytuacja | Miejsca |
|----------|---------|
| Remis | wszyscy remisujący — ta sama `place` (np. 1) |
| Jawny zwycięzca | zwycięzca `1`, pozostali wspólnie `2` (ex-aequo) |
| Override administracyjny | `1` / `2` z payloadu override |

Core helpers (`single_first_place`, `head_to_head_points`, `is_ex_aequo_first`) czytają `place` — nie nadają miejsc.

---

## 6. Flow reversal

```
ReverseDecision → RuleSet.decide_reversal → CoR → EventReversed
→ append meta-events → state.reset() → replay _effective_base_events()
```

Override w logu odwracalny przez `EventReversed`; nie wpływa na replay stanu, ale znika z `_effective_walkover_events()`.

---

## 7. Podsumowanie przepływów

| Akcja | Ścieżka | Mutacja stanu |
|-------|---------|---------------|
| `ScoreGoal`, korekty, … | `decide` → kolejka → `react` | `apply` per `ProjectionEvent` |
| Post-match walkover | `AwardWalkover` → `ContestResultOverridden` | tylko append (audit) |
| Pre-match forfeit | `AwardWalkover` → `MatchConcluded` | `apply` |
| Reversal | `decide_reversal` → CoR | `reset` + replay bazowych |
| Odczyt wyniku | `get_official_result()` | `ResultBuilder` on-the-fly |

---

## 8. Zasada nadrzędna

**Log decyduje o prawdzie, RuleSet o regułach, State o danych (immutable), ResultBuilder o wyniku.**

---

## Kluczowe pliki

| Obszar | Ścieżki |
|--------|---------|
| Root event | `src/core/event.py` |
| Aggregate | `src/core/contest/contest.py`, `event.py`, `result_builder.py` |
| Turniej | `src/core/tournament/event.py`, `tournament.py`, `tournament_policy.py` |
| Piłka nożna | `src/sports/football/contest/` |
| Darts | `src/sports/darts/contest/` |
| Turniej ↔ mecz | `RecordMatchOutcome` + `Contest.get_official_result()` |
