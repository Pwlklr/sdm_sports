# Architektura `Contest`

`Contest` to **agregat event-sourcingowy**: źródłem prawdy jest append-only log (`_history`). `current_state` to **projekcja** — wynik złożenia eventów. `RuleSet` **nie mutuje** stanu i **nie trzyma kontekstu meczu**; tylko decyduje, jakie fakty powstały, czytając `state`. Stan zmienia się wyłącznie przez `state.apply(fact)` (oraz przez pola setupu ustawione przed meczem — patrz §4).

---

## 1. Składniki i tworzenie contestu

**Aggregate składa się z:**

| Element | Rola |
|---------|------|
| `ContestState` | projekcja meczu (dane, uczestnicy, kontekst wejścia) |
| `RuleSet` | silnik decyzji: command → eventy, event → reakcje |
| `ContestResult` | wrapper wyniku (rozegrany + ewentualny override) |
| `_history` | pełny log (fakty domenowe + meta-eventy `EventReversed`) |

**Tworzenie** idzie przez `ContestFactory` — każdy sport rejestruje builder zwracający parę `(state, ruleset)`:

```python
# src/sports/football/register_contest.py
def _build_football_contest(contestants, config, **options):
    suspended = options.get("suspended_player_ids")  # opcjonalnie z turnieju
    state = FootballContestState(
        contestants,
        config=config,
        suspended_player_ids=suspended,
    )
    ruleset = FootballRuleSet(
        config,
        reversal_chain=build_football_reversal_chain(),
    )
    return state, ruleset

ContestFactory.register(FOOTBALL_SPORT.id, _build_football_contest)
```

Factory opakowuje to w `Contest`:

```python
# src/core/contest/contest_factory.py
state, ruleset = cls._build(sport_id, contestants, config, **options)
return Contest(state, ruleset, contest_id=contest_id)
```

Opcje buildera (`**options`) służą do kontekstu wejścia w mecz — np. `suspended_player_ids` przy tworzeniu z turnieju.

**Rehydratacja** z zapisanego logu: `Contest.from_events()` → replay przez `_rebuild_state()`.

Rejestracja sportu w pluginie (`SportPlugin` + import `register_contest`) sprawia, że builder jest dostępny przy starcie aplikacji.

---

## 2. Flow obsługi command (domenowego)

Punkt wejścia: `contest.handle(command)`.

```python
# src/core/contest/contest.py
def handle(self, command: Command) -> list[Event]:
    if isinstance(command, ReverseDecision):
        return self._handle_reversal(command)
    return self._handle_domain_command(command)

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

**Sekwencja:**

1. Adapter / Engine wywołuje `contest.handle(ScoreGoal)`.
2. `RuleSet.decide(command, state)` → lista początkowych eventów (np. `[GoalScored]`).
3. Dla każdego eventu z kolejki:
   - `_record_event(fact)` → `state.apply(fact)` + append do historii + notify + refresh wyniku.
   - `RuleSet.react(fact, state)` → ewentualne reakcje (np. druga żółta → `PlayerDismissed`).
   - Reakcje trafiają z powrotem do kolejki z `caused_by=parent.event_id`.

**Kolejność w `_record_event`:**

1. `current_state.apply(fact)` — mutacja projekcji
2. append do `_history`
3. `notify()` (Observer)
4. `_refresh_result()` — jeśli mecz zakończony, `build_result()` trafia do `ContestResult.played`

**Ważne:** `RuleSet` dostaje `state` tylko do **odczytu** przy walidacji i decyzji. Mutacja danych z eventów jest zawsze po stronie `State.apply`.

---

## 3. `RuleSet` — jak działa

`RuleSet` to czysty silnik decyzji z dwoma mapami handlerów:

- `command_handlers` — `Command` → `list[Event]`
- `reaction_handlers` — `Event` → `list[Event]` (efekty uboczne po fakcie)

Handlery **składane są z mixinów** przez MRO (`FootballCoreRules`, `FootballDisciplineRules`, …). Konflikt dwóch handlerów na ten sam typ → `TypeError`.

```python
# src/core/contest/rule_set.py
def decide(self, command, state) -> list[Event]:
    handler = self.command_handlers.get(type(command))
    if handler:
        return handler(self, command, state)
    return []

def react(self, fact, state) -> list[Event]:
    handler = self.reaction_handlers.get(type(fact))
    if handler:
        return handler(self, fact, state)
    return []
```

**Przykład command handler** (walidacja + emisja faktów):

```python
def decide_score_goal(self, command: ScoreGoal, state: FootballContestState) -> list[Event]:
    if state.is_completed:
        reject("Mecz jest zakonczony - nie mozna strzelic gola.")
    return [GoalScored(team_id=..., minute=..., ...)]
```

**Przykład reaction handler** (druga fala logiki po evencie):

```python
def react_player_cautioned(self, fact: PlayerCautioned, state) -> list[Event]:
    if state.disciplinary.yellows_for(fact.offender_id) >= state.config.yellows_per_dismissal:
        return [PlayerDismissed(team_id=..., offender_id=..., minute=...)]
    return []
```

**Przykład walidacji z kontekstu na `State`** (nie w `RuleSet`):

```python
# FootballSquadRules.decide_submit_lineup
if state.is_suspended(player_id):
    reject(f"Zawodnik {name} jest zawieszony i nie moze byc zgloszony.")
```

Reakcje dostają `caused_by=parent.event_id` — to klucz przy kaskadowym wycofywaniu (VAR, żółte karty).

---

## 4. `State` — mutacja przez eventy i kontekst wejścia

`ContestState` to projekcja z czterema kontraktami:

```python
# src/core/contest/contest_state.py
def apply(self, fact: Event) -> None: ...      # bookkeeping — bez reguł biznesowych
def reset(self) -> ContestState: ...           # świeża projekcja przed replay
def build_result(self) -> Result: ...           # sportowy wynik z aktualnej projekcji
@property
def contestants(self) -> list[Contestant]: ...
```

### Dane z eventów vs kontekst setupu

| Rodzaj danych | Skąd się bierze | Przykład (piłka) |
|---------------|-----------------|------------------|
| Event-sourced | `apply(fact)` | `scores`, `lineups`, `disciplinary`, `phase` |
| Setup (nie z logu) | konstruktor / opcje factory / przed startem meczu | `config`, `teams`, `suspended_player_ids` |

Pola setupu **nie są** wyciągane z eventów, ale muszą żyć na `State`, żeby `RuleSet` mógł je czytać. Przy `reset()` (replay) kopiujemy je tak jak `config` — np. zawieszenia turniejowe zostają na meczu.

```python
# src/sports/football/contest/state.py
def __init__(self, teams, config, *, suspended_player_ids=None):
    self.config = config
    self.suspended_player_ids = suspended_player_ids or frozenset()

def is_suspended(self, player_id: str) -> bool:
    return player_id in self.suspended_player_ids

def reset(self) -> FootballContestState:
    return FootballContestState(
        list(self.teams), self.config,
        suspended_player_ids=self.suspended_player_ids,
    )
```

**Integracja z turniejem** — przed meczem konsola ustawia zawieszenia z tablicy dyscyplinarnej na stanie, nie na rulesecie:

```python
# src/console/main.py — _apply_suspension_context
state.suspended_player_ids = frozenset(tournament.disciplinary_board.suspended_ids())
```

Po meczu: `accrue_suspensions(board, state)` — karty z `state.disciplinary` trafiają do turniejowej tablicy na kolejne spotkania.

### Wzorzec `apply`

Tabela `_appliers` + cienkie funkcje `_apply_*` — tylko bookkeeping, zero reguł biznesowych.

```python
def apply(self, fact: Event) -> None:
    handler = self._appliers.get(type(fact))
    if handler:
        handler(self, fact)

def build_result(self) -> Result:
    return FootballResult(
        winner=self.winner,
        scores=self.scores,
        was_draw=self.was_draw,
        decided_by=self.decided_by,
    )
```

**Podział odpowiedzialności:**

| Warstwa | Odpowiada za |
|---------|--------------|
| `RuleSet` | „Czy wolno?”, „Co się wydarzyło?” → emituje `Event` |
| `State.apply` | „Jak event zmienia dane meczu?” (wynik, faza, kartki…) |
| `State` (setup) | Kontekst wejścia: config, zawieszenia turniejowe, … |
| `State.build_result` | „Jaki jest sportowy wynik z aktualnej projekcji?” |

`contestants` żyją w `State` — `Contest.contestants` to delegacja do `current_state.contestants`.

---

## 5. Flow obsługi reverse command

Komendy wycofania dziedziczą po `ReverseDecision` (np. `VarOverturnGoal`, `RevokeCaution`, `RevokeDartThrow`). `handle()` kieruje je na osobną ścieżkę.

```python
def _handle_reversal(self, command: ReverseDecision) -> list[EventReversed]:
    markers = self._ruleset.decide_reversal(command, self.current_state, self._history)
    for marker in markers:
        self._record_meta_event(marker)
    self._rebuild_state()
    return markers
```

**Różnica względem zwykłego commandu:**

- **nie** woła `state.apply` od razu na markerze
- dopisuje `EventReversed` do historii (meta-event)
- **replayuje** cały efektywny log: `reset()` → `apply` tylko na eventach, które nie są wycofane

**Efektywny log** — event wycofany + wszystko, co ma `caused_by` wycofanego:

```python
def _effective_domain_events(self) -> list[Event]:
    withdrawn = self._get_withdrawn_event_ids()
    return [
        e for e in self._history
        if not isinstance(e, EventReversed) and e.event_id not in withdrawn
    ]
```

**Przepływ reversal:**

```
ReverseDecision
  → RuleSet.decide_reversal
    → CoR reversal chain
      → list[EventReversed]
  → append meta-events do history
  → state.reset()
  → replay effective_domain_events
  → refresh result
```

---

## 6. Chain of Responsibility (CoR) — tylko przy reversal

CoR **nie** obsługuje zwykłych commandów. Służy wyłącznie do zbudowania listy markerów `EventReversed` w `decide_reversal`.

**Rdzeń (core):**

```python
class ReversalHandler(ABC):
    def handle(self, ctx: ReversalContext) -> None:
        self._contribute(ctx)
        if self._successor is not None:
            self._successor.handle(ctx)
```

Domyślny łańcuch: walidacja istnienia targetu → zapis markera dla targetu.

**Sport rozszerza łańcuch** wstawiając handlery **przed** `RecordTargetHandler`:

```python
def build_football_reversal_chain() -> ReversalHandler:
    return ValidateTargetExistsHandler(
        FootballVarValidationHandler(
            FootballDisciplinaryInvalidationHandler(RecordTargetHandler())
        )
    )
```

**Przykłady logiki sportowej w CoR:**

- `FootballVarValidationHandler` — VAR tylko na `GoalScored`, mecz niezakończony
- `FootballDisciplinaryInvalidationHandler` — przy `RevokeCaution` dodatkowo wycofuje `PlayerDismissed` spowodowany tą kartką (`caused_by`)
- `DartsLegIntegrityHandler` — przy `RevokeDartThrow` unieważnia `LegWon` w tym samym legu

Każdy link tylko **dopisuje markery** do `ReversalContext.markers`; faktyczna zmiana stanu następuje dopiero przy replay.

---

## 7. Wynik meczu

- `State.build_result()` → sportowy `Result` (`FootballResult`, `DartsResult`, …)
- `ContestResult` trzyma `played` (z replay) i opcjonalny `official` (walkower, korekta komisji)
- `get_final_result()` — tylko gdy `is_completed`; zwraca `effective_result`

Bazowy `Result` w core ma tylko `is_finished()`. Interpretacja (remis, zwycięzca, ranking) jest po stronie typów sportowych — warstwy turniejowe/konsola używają `isinstance` na konkretnych wynikach, nie wspólnego `get_winner()` na ABC.

---

## 8. Co musi zdefiniować nowy sport

### A. Model domeny

- **`XxxMatchConfig`** — VO z parametrami meczu
- **`Contestant`** — walidacja typu w `State.__init__`

### B. Event-sourcing

- **`commands.py`** — intencje (`Command`) + ewentualnie `ReverseDecision`
- **`events.py`** — fakty (`Event`, frozen dataclasses)
- **`XxxContestState`** — `apply` / `reset` / `build_result` / `contestants`
- **`XxxRuleSet(RuleSet)`** — mixiny z `_own_command_handlers` i `_own_reaction_handlers`

### C. Kontekst na `State` (nie na `RuleSet`)

Wszystko, co ruleset musi „wiedzieć” o meczu poza danymi z eventów, trafia na **projekcję**:

- stały setup: `config`, lista graczy/drużyn
- zewnętrzny kontekst: np. `suspended_player_ids` (turniej), później ewentualnie pogoda, neutralne boisko itd.

`RuleSet` czyta `state.*` — nie trzyma własnych worków kontekstu.

### D. Wynik

- **`XxxResult(Result)`** — sportowy kształt wyniku
- Logika wyłącznie w `State.build_result()` (bez zewnętrznych `build_xxx_result(state)`)

### E. Reversal (opcjonalnie, ale zalecane)

- **`build_xxx_reversal_chain()`** — łańcuch CoR
- Przekazanie do `XxxRuleSet(..., reversal_chain=...)`

### F. Rejestracja

- **`register_contest.py`** — builder + `ContestFactory.register(sport_id, builder)`
- **`plugin.py`** — `SportPlugin(descriptor, adapter)` + import `register_contest`
- **`descriptor.py`** — `sport_id` używany w factory

### G. Warstwa wejścia

- **`ConsoleAdapter`** — parsowanie inputu → `Command`, widok stanu
- Katalog reversal w konsoli, jeśli sport wspiera cofanie

### H. Czego **nie** robi sport w core

- Nie implementuje `Contest` — tylko dostarcza `State` + `RuleSet`
- Nie mutuje stanu w `RuleSet` — tylko zwraca eventy
- Nie chowa kontekstu meczu w `RuleSet` — tylko na `State`
- Nie interpretuje wyniku w `ContestState` ABC — tylko `build_result()` zwraca swój typ

---

## 9. Podsumowanie przepływów

| Akcja | Ścieżka | Mutacja stanu |
|-------|---------|---------------|
| `StartMatch`, `ScoreGoal`, … | `decide` → kolejka → `react` | `apply` per event, na bieżąco |
| `VarOverturnGoal`, `RevokeDartThrow`, … | `decide_reversal` → CoR → meta-eventy | `reset` + replay efektywnego logu |
| Koniec meczu | reaction emituje `MatchConcluded` | `apply(MatchConcluded)` ustawia `is_completed` |
| Odczyt wyniku | `get_final_result()` | `build_result()` z aktualnej projekcji |
| Zawieszenia turniejowe | przed meczem / w factory | `state.suspended_player_ids` (setup, nie event) |

---

## Zasada nadrzędna

**Log decyduje o prawdzie, RuleSet o regułach, State o danych (w tym kontekście wejścia), CoR o polityce wycofywania.**

Nowy sport to w praktyce nowy zestaw command/event + para projection/ruleset zarejestrowana w factory.

---

## Kluczowe pliki

| Obszar | Ścieżki |
|--------|---------|
| Aggregate | `src/core/contest/contest.py`, `contest_factory.py`, `contest_state.py`, `contest_result.py` |
| RuleSet | `src/core/contest/rule_set.py` |
| Reversal CoR | `src/core/contest/reversal_chain.py`, `src/sports/*/contest/*_reversal.py` |
| Piłka nożna | `src/sports/football/contest/`, `register_contest.py` |
| Darts | `src/sports/darts/contest/`, `register_contest.py` |
| Turniej ↔ mecz (zawieszenia) | `src/console/main.py`, `discipline_carryover.py` |
