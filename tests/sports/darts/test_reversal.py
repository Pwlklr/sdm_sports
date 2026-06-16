from __future__ import annotations

from src.core.contestant.models import IndividualPlayer
from src.sports.darts.contest.commands import RevokeDartThrow, StartMatch, ThrowDart
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.events import DartScored, LegWon
from src.core.contest import ContestFactory
from src.sports.darts.descriptor import DARTS_SPORT


def test_revoke_winning_dart_withdraws_leg_via_caused_by() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    config = DartsMatchConfig(starting_score=12, legs_to_win_set=1, sets_to_win_match=1)
    match = ContestFactory.create(DARTS_SPORT.id, players, config)
    match.handle(StartMatch())
    match.handle(ThrowDart(sector=6, multiplier=2))
    winning_dart = next(e for e in match.history if isinstance(e, DartScored))

    match.handle(
        RevokeDartThrow(target_event_id=winning_dart.event_id, reason="review")
    )

    assert match.current_state.legs_won["a"] == 0
    assert match.current_state.scores["a"] == config.starting_score


def test_revoke_middle_dart_invalidates_leg_won() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    config = DartsMatchConfig(starting_score=40, legs_to_win_set=1, sets_to_win_match=1)
    match = ContestFactory.create(DARTS_SPORT.id, players, config)
    match.handle(StartMatch())
    match.handle(ThrowDart(sector=10, multiplier=1))
    first_dart = next(e for e in match.history if isinstance(e, DartScored))
    match.handle(ThrowDart(sector=15, multiplier=2))
    assert any(isinstance(e, LegWon) for e in match.history)

    match.handle(RevokeDartThrow(target_event_id=first_dart.event_id, reason="review"))

    assert match.current_state.legs_won["a"] == 0
    assert match.current_state.scores["a"] == 10
