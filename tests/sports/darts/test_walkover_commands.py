from src.core.contest import ContestFactory
from src.core.contestant.models import IndividualPlayer
from src.core.tournament.ranking import single_first_place
from src.sports.darts.contest.commands import AwardWalkover, StartMatch, ThrowDart
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.events import ContestResultOverridden
from src.sports.darts.descriptor import DARTS_SPORT


def test_darts_pre_match_award() -> None:
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = ContestFactory.create(DARTS_SPORT.id, players, DartsMatchConfig())

    match.handle(AwardWalkover(winner_id="b", reason="walkover"))

    assert match.current_state.is_finished
    assert match.get_played_result().decided_by == "walkover"
    assert not any(isinstance(e, ContestResultOverridden) for e in match.history)
    assert single_first_place(match.get_official_result().ranking()) is players[1]


def test_darts_in_match_walkover_is_rejected() -> None:
    """AwardWalkover while match is in progress must be rejected."""
    import pytest
    from src.sports.darts.contest.commands import StartMatch, ThrowDart
    from src.core.shared.command_rejected import CommandRejected

    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = ContestFactory.create(DARTS_SPORT.id, players, DartsMatchConfig())
    match.handle(StartMatch())
    match.handle(ThrowDart(sector=20, multiplier=1))  # Started but not finished

    with pytest.raises(CommandRejected, match="in progress"):
        match.handle(AwardWalkover(winner_id="b", reason="walkover"))


def test_darts_walkover_with_invalid_winner_is_rejected() -> None:
    """AwardWalkover with an unknown winner_id must be rejected."""
    import pytest
    from src.core.shared.command_rejected import CommandRejected

    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = ContestFactory.create(DARTS_SPORT.id, players, DartsMatchConfig())

    with pytest.raises((CommandRejected, ValueError)):
        match.handle(AwardWalkover(winner_id="unknown_player", reason="walkover"))


def test_darts_post_match_award() -> None:
    config = DartsMatchConfig(
        starting_score=2,
        legs_to_win_set=1,
        sets_to_win_match=1,
        in_multiplier=1,
        out_multiplier=2,
    )
    players = [IndividualPlayer("A", "a"), IndividualPlayer("B", "b")]
    match = ContestFactory.create(DARTS_SPORT.id, players, config)
    match.handle(StartMatch())
    match.handle(ThrowDart(sector=1, multiplier=2))
    assert match.current_state.is_finished

    match.handle(AwardWalkover(winner_id="b", reason="forfeit"))

    assert any(isinstance(e, ContestResultOverridden) for e in match.history)
    assert single_first_place(match.get_official_result().ranking()) is players[1]
    assert match.get_official_result().decided_by == "forfeit"
