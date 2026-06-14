# Architektura `Contest`

`Contest` to **agregat event-sourcingowy**: źródłem prawdy jest append-only log (`_history`). `current_state` to **immutable projekcja** — wynik złożenia eventów przez `apply(fact) → Self`. `RuleSet` **nie mutuje** stanu; tylko decyduje, jakie fakty powstały, czytając `state`. Wynik sportowy buduje **`ResultBuilder`**, nie stan.

---

## 1. Składniki i tworzenie contestu

**Aggregate składa się z:**

| Element | Rola |
|---------|------|
| `ContestState` | immutable projekcja meczu (Protocol) |
| `RuleSet` | silnik decyzji: command → eventy, event → reakcje |
| `ResultBuilder` | materializuje `ContestResult` ze stanu po zakończeniu meczu |
| `OfficialResultView` | wrapper wyniku (rozegrany + ewentualny override) |
| `_history` | pełny log (fakty domenowe + meta-eventy `EventReversed`) |

**Tworzenie** idzie przez `ContestFactory` — każdy sport rejestruje builder zwracający `ContestAssembly`:

```python
# src/sports/football/register_contest.py
def _build_football_contest(contestants, config, **options):
    state = create_football_contest_state(contestants, config, ...)
    ruleset = FootballRuleSet(config, reversal_chain=...)
    result_builder = FootballResultBuilder(config=config)
    return ContestAssembly(state=state, ruleset=ruleset, result_builder=result_builder)

ContestFactory.register(FOOTBALL_SPORT.id, _build_football_contest)
```

Factory opakowuje assembly w `Contest`:

```python
# src/core/contest/contest_factory.py
assembly = cls._build(sport_id, contestants, config, **options)
return Contest(assembly.state, assembly.ruleset, assembly.result_builder, contest_id=...)
```

**Rehydratacja** z zapisanego logu: `Contest.from_events()` → replay przez `_rebuild_state()`.

---

## 2. Model wyniku — trzy fasety

`ContestResult` to opublikowany snapshot zakończonego meczu:

| Faseta | Odpowiedzialność | Kto czyta |
|--------|------------------|-----------|
| `ranking()` | miejsca w meczu (ex-aequo przy remisie) | `TournamentResultReader` |
| `side_metrics()` | agregaty per strona/contestant | Darts: jedyne źródło metryk |
| `individual_metrics()` | statystyki per zawodnik | Football: zawieszenia, strzelcy |

**Stan vs wynik:** `ContestantStats` w `ContestState` = live projection (aktualizowane przez `apply`). `ResultBuilder` materializuje snapshot do `side_metrics` / `individual_metrics` — downstream nie sięga do stanu po zakończeniu meczu.

`OfficialResultView` trzyma `played` (z buildera po replay) i opcjonalny `official` (walkover, korekta komisji). `ContestOutcome` implementuje `ContestResult` z pustymi metrykami.

---

## 3. Flow obsługi command (domenowego)

Punkt wejścia: `contest.handle(command)`.

```python
def _handle_domain_command(self, command: Command) -> list[Event]:
    emitted: list[Event] = []
    queue: list[Event] = list(self._ruleset.decide(command, self.current_state))

    while queue:
        fact = queue.pop(0)
        self._record_event(fact)
        emitted.append(fact)
        for reaction in self._ruleset.react(fact, self.current_state):
            queue.append(replace(reaction, caused_by=fact.event_id))

    return emitted
```

**Kolejność w `_record_event`:**

1. `current_state = current_state.apply(fact)` — nowa immutable projekcja
2. append do `_history`
3. `notify()` (Observer)
4. `_refresh_result()` — jeśli `is_finished`, `result_builder.build(state)` trafia do `OfficialResultView.played`

**Ważne:** `RuleSet` dostaje `state` tylko do **odczytu**. Mutacja danych z eventów jest zawsze po stronie `State.apply`.

---

## 4. `ContestState` — immutable projekcja

```python
class ContestState(Protocol):
    @property
    def is_finished(self) -> bool: ...
    @property
    def contestants(self) -> list[Contestant]: ...
    def apply(self, fact: Event) -> Self: ...
    def reset(self) -> Self: ...
```

Bez `build_result()` — stan nie interpretuje wyniku.

### `ContestResult` — jawny interfejs (ABC)

```python
class ContestResult(ABC):
    @abstractmethod
    def is_finished(self) -> bool: ...
    @abstractmethod
    def ranking(self) -> tuple[RankedEntry, ...]: ...
    @abstractmethod
    def side_metrics(self) -> SideMetrics: ...
    @abstractmethod
    def individual_metrics(self) -> IndividualMetrics: ...
```

Implementacje: `class DartsResult(ContestResult)`, `class FootballResult(ContestResult)`, `class ContestOutcome(ContestResult)`.

### Live stats (`ContestantStats`)

Embedded w stanie sportowym, aktualizowane przez appliers:

- Football: `FootballPlayerStats` (gole, kartki, asysty, dismissed)
- Darts: `DartsPlayerStats` (sets_won, legs_won, darts_thrown, highest_checkout)

### Dane z eventów vs kontekst setupu

| Rodzaj danych | Skąd się bierze | Przykład |
|---------------|-----------------|----------|
| Event-sourced | `apply(fact)` | scores, lineups, phase, player_stats |
| Setup | konstruktor / factory options | config, teams, suspended_player_ids |

Przy `reset()` (replay) kopiujemy setup — np. zawieszenia turniejowe zostają na meczu (`with_tournament_context`).

### Wzorzec `apply`

Tabela `_appliers` + czyste funkcje `_apply_*` zwracające `replace(state, ...)`.

**Podział odpowiedzialności:**

| Warstwa | Odpowiada za |
|---------|--------------|
| `RuleSet` | „Czy wolno?”, „Co się wydarzyło?” → emituje `Event` |
| `State.apply` | „Jak event zmienia dane meczu?” |
| `ResultBuilder` | „Jaki jest sportowy wynik z aktualnej projekcji?” (3 fasety) |

---

## 5. `ResultBuilder`

```python
class ResultBuilder(Protocol):
    def build(self, state: ContestState) -> ContestResult: ...
```

Sportowe implementacje (`FootballResultBuilder`, `DartsResultBuilder`) budują jednocześnie ranking, side_metrics i individual_metrics.

Przykład football — remis ex-aequo: obie drużyny `place=1`.

Darts — gracz = strona; `individual_metrics()` zwraca `EmptyIndividualMetrics`.

---

## 6. Warstwa odczytu metryk

| Reader | Faseta | Przypadek użycia |
|--------|--------|------------------|
| `TournamentResultReader` | `ranking()` | punkty H2H, awans knockout |
| `MatchMetricsReader` | `side_metrics()` / `individual_metrics()` | zawieszenia, strzelcy, statystyki turniejowe |

Rejestracja readerów w `SportPlugin.match_metrics_reader`; dostęp przez `SportsSystemEngine.get_match_metrics_reader(sport_id)`.

Football: `FootballMatchMetricsReader.accrue_disciplinary(result, board)` czyta `individual_metrics()`.

Darts: `DartsMatchMetricsReader.player_totals(result)` czyta `side_metrics()`.

---

## 7. Interpretacja rankingu (turniej)

`ContestResult` udostępnia wyłącznie fasety — **nie** interpretuje zwycięzcy. Turniej czyta `ranking()` przez helpery w `src/core/tournament/ranking.py` lub `TournamentResultReader`:

- `single_first_place(ranking)` — jeden zwycięzca knockout 1v1
- `is_ex_aequo_first(ranking)` — remis ex-aequo
- `qualifiers_up_to_place(ranking, n)` — awans top-N
- `head_to_head_points(...)` — punkty tabeli z miejsc w rankingu

Sportowe `DartsResult` / `FootballResult` **implementują** `ContestResult` (ABC) — tylko dane + fasety, bez `get_winner()`.

---

## 8. Flow obsługi reverse command

Bez zmian względem poprzedniej architektury:

```
ReverseDecision → RuleSet.decide_reversal → CoR → EventReversed
→ append meta-events → state.reset() → replay effective_domain_events → refresh result
```

CoR służy wyłącznie do zbudowania markerów `EventReversed`; faktyczna zmiana stanu następuje przy replay.

---

## 8. Co musi zdefiniować nowy sport

### A. Model domeny

- **`XxxMatchConfig`** — VO z parametrami meczu
- **`Contestant`** — walidacja typu w factory

### B. Event-sourcing

- **`commands.py`** — intencje + ewentualnie `ReverseDecision`
- **`events.py`** — fakty (frozen dataclasses)
- **`XxxContestState`** — frozen dataclass; `apply` / `reset` / `contestants` / `is_finished`
- **`XxxPlayerStats`** — live stats embedded w stanie
- **`XxxRuleSet(RuleSet)`** — mixiny z handlerami

### C. Wynik

- **`XxxResult`** — implementuje `ContestResult` (3 fasety)
- **`XxxResultBuilder`** — buduje wynik ze stanu
- **`XxxMatchMetricsReader`** — ekstrakcja metryk do turnieju (opcjonalnie)

### D. Rejestracja

- **`register_contest.py`** — walidacja + `ContestAssembly` + `ContestFactory.register`
- **`plugin.py`** — `SportPlugin(descriptor, adapter, match_metrics_reader=...)`

### E. Czego **nie** robi sport w core

- Nie implementuje `Contest` — tylko dostarcza assembly
- Nie mutuje stanu w `RuleSet` — tylko zwraca eventy
- Nie buduje wyniku w `State` — tylko `ResultBuilder`

---

## 9. Podsumowanie przepływów

| Akcja | Ścieżka | Mutacja stanu |
|-------|---------|---------------|
| `StartMatch`, `ScoreGoal`, … | `decide` → kolejka → `react` | `apply` per event (nowy obiekt) |
| Reversal | `decide_reversal` → CoR | `reset` + replay |
| Koniec meczu | reaction → `MatchConcluded` | `apply` ustawia `is_finished` |
| Odczyt wyniku | `get_final_result()` | `result_builder.build(state)` |
| Metryki turniejowe | po meczu | `MatchMetricsReader` na `ContestResult` |

---

## Zasada nadrzędna

**Log decyduje o prawdzie, RuleSet o regułach, State o danych (immutable), ResultBuilder o wyniku, MatchMetricsReader o agregacji turniejowej.**

---

## Kluczowe pliki

| Obszar | Ścieżki |
|--------|---------|
| Aggregate | `src/core/contest/contest.py`, `contest_factory.py`, `contest_state.py`, `contest_result.py`, `result_builder.py` |
| Metryki | `src/core/contest/metrics.py`, `match_metrics_reader.py` |
| Piłka nożna | `src/sports/football/contest/`, `register_contest.py`, `plugin.py` |
| Darts | `src/sports/darts/contest/`, `register_contest.py`, `plugin.py` |
| Turniej ↔ mecz | `src/console/main.py`, `discipline_carryover.py`, `tournament_result_reader.py` |
