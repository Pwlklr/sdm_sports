from src.core.contest.contest_result import ContestOutcome, RankedEntry
from src.core.tournament.ranking import single_first_place
from src.core.contestant.models import IndividualPlayer, Team
from src.core.system.sports_system_engine import SportsSystemEngine
from src.sports.football.contest.commands import ScoreGoal, StartMatch
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.core.contest.metrics import FootballPlayerMatchStats
from src.sports.football.contest.football_result import (
    FootballResult,
    FootballSideMetrics,
    FootballTeamSideMetrics,
)
from src.core.contest import ContestFactory
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


def _football_result(winner, loser, scores, decided_by="commission"):
    return FootballResult(
        ranking_entries=(
            RankedEntry(contestant=winner, place=1),
            RankedEntry(contestant=loser, place=2),
        ),
        side=FootballSideMetrics(
            by_team_id={
                winner.id: FootballTeamSideMetrics(
                    team_id=winner.id,
                    score=scores.get(winner.id, 0),
                    penalty_score=0,
                    players={},
                ),
                loser.id: FootballTeamSideMetrics(
                    team_id=loser.id,
                    score=scores.get(loser.id, 0),
                    penalty_score=0,
                    players={},
                ),
            },
            decided_by=decided_by,
        ),
    )


def test_result_wrapper_preserves_played_outcome() -> None:
    engine = SportsSystemEngine()
    match = _played_match()
    engine.register_active_match(match)
    away = match.contestants[1]

    engine.override_result(
        match.id,
        ContestOutcome(winner=away, decided_by="disciplinary_forfeit"),
        reason="disciplinary_forfeit",
    )

    assert match.result.is_overridden
    assert match.result.override_reason == "disciplinary_forfeit"
    assert single_first_place(match.result.effective_result.ranking()) is away
    assert match.result.played is None
    assert match.current_state.scores["home"] == 1


def test_override_can_wrap_full_sport_result() -> None:
    engine = SportsSystemEngine()
    match = _played_match()
    engine.register_active_match(match)
    home = match.contestants[0]
    away = match.contestants[1]

    revised = _football_result(away, home, {"home": 0, "away": 3})
    engine.override_result(match.id, revised, reason="result_correction")

    assert single_first_place(match.result.effective_result.ranking()) is away
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
    assert single_first_place(match.result.effective_result.ranking()) is away


def test_result_delegates_to_played_when_not_overridden() -> None:
    match = _played_match()
    assert not match.result.is_overridden
    assert not match.result.is_finished()
    assert match.result.played is None
