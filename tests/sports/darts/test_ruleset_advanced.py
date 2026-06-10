import pytest


from src.core.contestant import IndividualPlayer

from src.sports.darts.contest.commands import CallOcheFault, ThrowDart

from src.sports.darts.contest.darts_match_config import DartsMatchConfig

from src.sports.darts.contest.events import MatchConcluded, MatchStarted, SetWon

from src.sports.darts.contest.darts_rule_set import DartsRuleSet

from src.sports.darts.contest.darts_contest_state import DartsContestState

from src.core.shared.command_rejected import CommandRejected


@pytest.fixture
def players() -> list[IndividualPlayer]:

    return [IndividualPlayer("A", "p1"), IndividualPlayer("B", "p2")]


def _bootstrap(state: DartsContestState) -> None:

    state.apply(MatchStarted())


def _process(
    state: DartsContestState, ruleset: DartsRuleSet, command: object
) -> list[object]:

    emitted: list[object] = []

    queue = list(ruleset.decide(command, state))  # type: ignore[arg-type]

    while queue:

        fact = queue.pop(0)

        state.apply(fact)

        emitted.append(fact)

        queue.extend(ruleset.react(fact, state))

    return emitted


def test_ruleset_match_completed(players: list[IndividualPlayer]) -> None:

    config = DartsMatchConfig()

    state = DartsContestState(players, config)

    state.is_completed = True

    with pytest.raises(CommandRejected):
        DartsRuleSet(config).decide(ThrowDart(sector=20, multiplier=1), state)


def test_three_darts_switches_turn(players: list[IndividualPlayer]) -> None:

    config = DartsMatchConfig()

    state = DartsContestState(players, config)

    rs = DartsRuleSet(config)

    _bootstrap(state)

    _process(state, rs, ThrowDart(sector=20, multiplier=1))

    _process(state, rs, ThrowDart(sector=20, multiplier=1))

    assert state.current_player.id == "p1"

    _process(state, rs, ThrowDart(sector=20, multiplier=1))

    assert state.current_player.id == "p2"


def test_set_and_match_won(players: list[IndividualPlayer]) -> None:

    config = DartsMatchConfig(
        starting_score=2,
        legs_to_win_set=1,
        sets_to_win_match=1,
        in_multiplier=1,
        out_multiplier=2,
    )

    state = DartsContestState(players, config)

    rs = DartsRuleSet(config)

    _bootstrap(state)

    emitted = _process(state, rs, ThrowDart(sector=1, multiplier=2))

    event_types = [type(e) for e in emitted]

    assert SetWon in event_types

    assert MatchConcluded in event_types

    assert state.is_completed is True


def test_set_won_but_not_match(players: list[IndividualPlayer]) -> None:

    config = DartsMatchConfig(
        starting_score=2,
        legs_to_win_set=1,
        sets_to_win_match=2,
        in_multiplier=1,
        out_multiplier=2,
    )

    state = DartsContestState(players, config)

    rs = DartsRuleSet(config)

    _bootstrap(state)

    emitted = _process(state, rs, ThrowDart(sector=1, multiplier=2))

    event_types = [type(e) for e in emitted]

    assert SetWon in event_types

    assert MatchConcluded not in event_types

    assert state.is_completed is False

    assert state.sets_won["p1"] == 1


def test_oche_fault_scores_zero_but_consumes_dart(
    players: list[IndividualPlayer],
) -> None:

    config = DartsMatchConfig(starting_score=501)

    state = DartsContestState(players, config)

    rs = DartsRuleSet(config)

    _bootstrap(state)

    _process(state, rs, CallOcheFault())

    assert state.scores["p1"] == 501

    assert state.current_player == players[0]

    assert state.current_turn is not None

    assert len(state.current_turn.throws) == 1

    assert state.current_turn.throws[0].points == 0


def test_missed_dart_scores_zero(players: list[IndividualPlayer]) -> None:

    config = DartsMatchConfig(starting_score=501)

    state = DartsContestState(players, config)

    rs = DartsRuleSet(config)

    _bootstrap(state)

    _process(state, rs, ThrowDart(sector=0, multiplier=1))

    assert state.scores["p1"] == 501

    assert state.current_turn is not None

    assert len(state.current_turn.throws) == 1

    assert state.current_turn.throws[0].points == 0
