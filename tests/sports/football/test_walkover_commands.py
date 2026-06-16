from src.core.contest import ContestFactory
from src.core.contestant.models import IndividualPlayer, Team
from src.core.tournament.ranking import single_first_place
from src.sports.football.contest.commands import (
    AwardWalkover,
    EndPeriod,
    ScoreGoal,
    StartMatch,
)
from src.sports.football.contest.events import ContestResultOverridden
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.descriptor import FOOTBALL_SPORT


def _played_match():
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    match = ContestFactory.create(
        FOOTBALL_SPORT.id, [home, away], FootballMatchConfig(allow_draw=True)
    )
    match.handle(StartMatch())
    match.handle(ScoreGoal(team_index=0, minute=10))
    return match


def _finish_match(match) -> None:
    for _ in range(2):
        match.handle(EndPeriod())


def test_post_match_walkover_records_override_event() -> None:
    match = _played_match()
    _finish_match(match)
    away = match.contestants[1]

    match.handle(AwardWalkover(winner_id=away.id, reason="disciplinary_forfeit"))

    assert any(isinstance(e, ContestResultOverridden) for e in match.history)
    assert match.current_state.scores["home"] == 1
    assert single_first_place(match.get_official_result().ranking()) is away
    assert (
        single_first_place(match.get_played_result().ranking()) is match.contestants[0]
    )


def test_post_match_walkover_official_scores() -> None:
    match = _played_match()
    _finish_match(match)
    away = match.contestants[1]

    match.handle(
        AwardWalkover(
            winner_id=away.id,
            reason="result_correction",
            winner_score=3,
            loser_score=0,
        )
    )

    official = match.get_official_result()
    assert official.scores == {"home": 0, "away": 3}
    assert match.get_played_result().scores == {"home": 1, "away": 0}


def test_pre_match_walkover_uses_match_concluded() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    match = ContestFactory.create(
        FOOTBALL_SPORT.id, [home, away], FootballMatchConfig(allow_draw=True)
    )

    match.handle(AwardWalkover(winner_id=away.id, reason="walkover"))

    assert not any(isinstance(e, ContestResultOverridden) for e in match.history)
    assert match.current_state.is_finished
    assert single_first_place(match.get_official_result().ranking()) is away


def test_played_equals_official_without_override() -> None:
    match = _played_match()
    _finish_match(match)

    played = match.get_played_result()
    official = match.get_official_result()
    assert played.ranking() == official.ranking()
    assert played.scores == official.scores


def test_in_match_walkover_is_rejected() -> None:
    """AwardWalkover while match is in progress must be rejected."""
    import pytest
    from src.core.shared.command_rejected import CommandRejected

    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    match = ContestFactory.create(
        FOOTBALL_SPORT.id, [home, away], FootballMatchConfig(allow_draw=True)
    )
    match.handle(StartMatch())
    # Match started but not finished → in-progress → walkover must be rejected

    with pytest.raises(CommandRejected, match="in progress"):
        match.handle(AwardWalkover(winner_id=away.id, reason="walkover"))


def test_walkover_with_invalid_winner_is_rejected() -> None:
    """AwardWalkover with a winner_id that is not a contestant must be rejected."""
    import pytest
    from src.core.shared.command_rejected import CommandRejected

    home = Team("Home", "home")
    away = Team("Away", "away")
    match = ContestFactory.create(
        FOOTBALL_SPORT.id, [home, away], FootballMatchConfig(allow_draw=True)
    )

    with pytest.raises((CommandRejected, ValueError)):
        match.handle(AwardWalkover(winner_id="unknown_team_id", reason="walkover"))
