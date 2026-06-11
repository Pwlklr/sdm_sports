from src.core.contestant.models import IndividualPlayer, Team
from src.core.contest.contest_result import ContestOutcome
from src.core.system.sports_system_engine import SportsSystemEngine
from src.sports.football.contest.commands import ScoreGoal, StartMatch
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_result import FootballResult
from src.core.contest import ContestFactory
from src.sports.football.descriptor import FOOTBALL_SPORT


def _played_match() -> object:
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


def test_result_wrapper_preserves_played_outcome() -> None:
    engine = SportsSystemEngine()
    match = _played_match()
    engine.register_active_match(match)
    away = match.contestants[1]

    engine.override_result(
        match.id,
        ContestOutcome(away, decided_by="commission"),
        reason="disciplinary_forfeit",
    )

    assert match.result.is_overridden
    assert match.result.override_reason == "disciplinary_forfeit"
    assert match.result.effective_result.get_winner() is away
    assert match.result.played is None
    assert match.current_state.scores["home"] == 1


def test_override_can_wrap_full_sport_result() -> None:
    engine = SportsSystemEngine()
    match = _played_match()
    engine.register_active_match(match)
    away = match.contestants[1]

    revised = FootballResult(
        winner=away,
        scores={"home": 0, "away": 3},
        was_draw=False,
        decided_by="commission",
    )
    engine.override_result(match.id, revised, reason="result_correction")

    assert match.result.effective_result.get_winner() is away
    assert revised.scores == {"home": 0, "away": 3}
    assert match.current_state.scores["home"] == 1


def test_award_walkover_uses_result_wrapper() -> None:
    engine = SportsSystemEngine()
    match = _played_match()
    engine.register_active_match(match)
    away = match.contestants[1]

    engine.award_walkover(match.id, away, reason="walkover")

    assert match.result.is_overridden
    assert match.result.override_reason == "walkover"
    assert match.result.effective_result.get_winner() is away


def test_result_delegates_to_played_when_not_overridden() -> None:
    match = _played_match()
    assert not match.result.is_overridden
    assert not match.result.is_finished()
    assert match.result.played is None
