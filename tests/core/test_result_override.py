from src.core.contestant.models import IndividualPlayer, Team
from src.core.contest.result_override import ContestOutcome, ResultOverride
from src.core.system.sports_system_engine import SportsSystemEngine
from src.sports.football.contest.commands import ScoreGoal, StartMatch
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_result import FootballResult
from src.sports.football.football_sport_factory import FootballSportFactory


def _played_match() -> object:
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    match = FootballSportFactory().create_contest(
        [home, away], FootballMatchConfig(allow_draw=True)
    )
    match.handle(StartMatch())
    match.handle(ScoreGoal(team_index=0, minute=10))
    return match


def test_result_override_wraps_official_outcome() -> None:
    engine = SportsSystemEngine()
    match = _played_match()
    engine.register_active_match(match)
    away = match.contestants[1]

    engine.override_result(
        match.id,
        ContestOutcome(away, decided_by="commission"),
        reason="disciplinary_forfeit",
    )

    assert match.result_override is not None
    assert isinstance(match.result_override, ResultOverride)
    assert match.result_override.reason == "disciplinary_forfeit"
    assert match.official_result is match.result_override.result
    assert match.official_result.get_winner() is away
    assert match.current_state.scores["home"] == 1
    assert match.result is None  # mecz nie zakonczony — override dziala niezaleznie


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

    assert match.official_result is revised
    assert match.official_result.scores == {"home": 0, "away": 3}
    assert match.current_state.scores["home"] == 1


def test_award_walkover_uses_result_override_wrapper() -> None:
    engine = SportsSystemEngine()
    match = _played_match()
    engine.register_active_match(match)
    away = match.contestants[1]

    engine.award_walkover(match.id, away, reason="walkover")

    assert match.result_override is not None
    assert match.result_override.reason == "walkover"
    assert match.official_result.get_winner() is away


def test_official_result_falls_back_to_played_result() -> None:
    match = _played_match()
    assert match.result_override is None
    assert match.official_result is match.result
