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

## 2. Model wyniku — dwie fasety

`ContestResult` to opublikowany snapshot zakończonego meczu:

| Faseta | Odpowiedzialność | Kto czyta |
|--------|------------------|-----------|
| `ranking()` | miejsca w meczu (ex-aequo przy remisie) | `TournamentResultReader` |
| `side_metrics()` | agregaty per strona/contestant | wszystkie metryki meczu |

**Zagnieżdżenie individual w side:** statystyki zawodników nie są osobną fasetą interfejsu — siedzą w `side_metrics`:

- **Darts** (gracz = strona): `DartsSideMetrics.by_contestant_id` — sets, legs, darts_thrown
- **Football** (drużyna + skład): `FootballSideMetrics.by_team_id[team].players[player_id]` — gole, kartki, asysty

`MatchMetricsReader` czyta wyłącznie `side_metrics()` (football: `side.all_players()`, darts: `by_contestant_id`).

**Stan vs wynik:** `ContestantStats` w `ContestState` = live projection. `ResultBuilder` materializuje snapshot do `side_metrics` — downstream nie sięga do stanu po zakończeniu meczu.

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
| `ResultBuilder` | „Jaki jest sportowy wynik z aktualnej projekcji?” (ranking + side_metrics) |

---

## 5. `ResultBuilder`

```python
class ResultBuilder(Protocol):
    def build(self, state: ContestState) -> ContestResult: ...
```

Sportowe implementacje (`FootballResultBuilder`, `DartsResultBuilder`) budują ranking i `side_metrics` (z zagnieżdżonymi statystykami graczy w piłce).

Przykład football — remis ex-aequo: obie drużyny `place=1`. Statystyki graczy w `FootballTeamSideMetrics.players`.

---

## 6. Warstwa odczytu metryk

| Reader | Źródło | Przypadek użycia |
|--------|--------|------------------|
| `TournamentResultReader` | `ranking()` | punkty H2H, awans knockout |
| `MatchMetricsReader` | `side_metrics()` | zawieszenia, strzelcy, statystyki turniejowe |

Rejestracja readerów w `SportPlugin.match_metrics_reader`; dostęp przez `SportsSystemEngine.get_match_metrics_reader(sport_id)`.

Football: `FootballMatchMetricsReader.accrue_disciplinary(result, board)` czyta `side.all_players()`.

Darts: `DartsMatchMetricsReader.player_totals(result)` czyta `side.by_contestant_id`.

---

## 7. Interpretacja rankingu (turniej)

`ContestResult` udostępnia wyłącznie fasety — **nie** interpretuje zwycięzcy. Turniej czyta `ranking()` przez helpery w `src/core/tournament/ranking.py` lub `TournamentResultReader`:

- `single_first_place(ranking)` — jeden zwycięzca knockout 1v1
- `is_ex_aequo_first(ranking)` — remis ex-aequo
- `qualifiers_up_to_place(ranking, n)` — awans top-N
- `head_to_head_points(...)` — punkty tabeli z miejsc w rankingu

Sportowe `DartsResult` / `FootballResult` **implementują** `ContestResult` (ABC) — tylko dane + fasety, bez `get_winner()`.

---

## 9. Flow obsługi reverse command

Bez zmian względem poprzedniej architektury:

```
ReverseDecision → RuleSet.decide_reversal → CoR → EventReversed
→ append meta-events → state.reset() → replay effective_domain_events → refresh result
```

CoR służy wyłącznie do zbudowania markerów `EventReversed`; faktyczna zmiana stanu następuje przy replay.

---

## 10. Co musi zdefiniować nowy sport

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

- **`XxxResult`** — implementuje `ContestResult` (ranking + side_metrics)
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

## 11. Podsumowanie przepływów

| Akcja | Ścieżka | Mutacja stanu |
|-------|---------|---------------|
| `StartMatch`, `ScoreGoal`, … | `decide` → kolejka → `react` | `apply` per event (nowy obiekt) |
| Reversal | `decide_reversal` → CoR | `reset` + replay |
| Koniec meczu | reaction → `MatchConcluded` | `apply` ustawia `is_finished` |
| Odczyt wyniku | `get_final_result()` | `result_builder.build(state)` |
| Metryki turniejowe | po meczu | `MatchMetricsReader` na `ContestResult` |

---

## 12. Zrealizowane Wzorce Projektowe (Wymaganie projektowe)

Architektura systemu celowo wykorzystuje ugruntowane wzorce projektowe do zarządzania złożonością dyscyplin sportowych:

1. **Event Sourcing** – `Contest` nie przechowuje swojego ostatecznego stanu mutowalnego. Prawdą jest dopisywana lista zdarzeń (`_history`). Stan (`ContestState`) jest jedynie wypadkową (projekcją) wyliczaną poprzez sekwencyjne wywołanie metody `apply()`. Zapewnia to idealną odtwarzalność meczu i ułatwia cofanie akcji.
2. **Strategy (Strategia)** – logika i reguły poszczególnych dyscyplin są wydzielone do zewnętrznych klas (`RuleSet`). Główny agregat (`Contest`) nie posiada instrukcji `if sport == "football"`, lecz deleguje decyzje do wstrzykniętej strategii.
3. **Builder (Budowniczy)** – z uwagi na złożoność wyliczania ostatecznego wyniku (ranking + rozbudowane statystyki zawodników w różnych sportach), zadanie to zostało wyciągnięte do klas implementujących `ResultBuilder` (np. `FootballResultBuilder`). Builder materializuje gotowy snapshot wyniku (`ContestResult`) bazując na obecnym stanie.
4. **Chain of Responsibility (Łańcuch Zobowiązań)** – wykorzystany przy obsłudze unieważniania/cofania zdarzeń domenowych (`ReversalChain`). Żądanie cofnięcia akcji przechodzi przez łańcuch ewaluatorów, które decydują czy da się wygenerować `EventReversed`, czy należy zgłosić błąd.
5. **Observer (Obserwator)** – agregat sportowy (`Contest`) posiada mechanizm subskrypcji i emituje notyfikacje (`notify()`) po każdej skutecznej zmianie w swoim logu zdarzeń. Pozwala to na asynchroniczne reagowanie systemu (np. odświeżenie widoku lub przeliczenie tabeli turniejowej) bez twardego sprzęgania.
6. **Factory Method / Abstract Factory** – abstrakcja `ContestFactory` ukrywa skomplikowany proces tworzenia meczu. Każdy plugin sportowy dostarcza swój własny mechanizm budowy (`_build_football_contest`), który składa kompletny obiekt wstrzykując mu odpowiedni State, RuleSet i Builder.

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
