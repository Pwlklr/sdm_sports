import pytest


from src.core.contest import ContestFactory

from src.core.contest.command import ReverseDecision

from src.core.contestant.models import IndividualPlayer, Team

from src.core.shared.command_rejected import CommandRejected

from src.core.tournament.ranking import single_first_place

from src.sports.football.contest.commands import (
    CorrectGoalScorer,
    EndPeriod,
    ScoreGoal,
    StartMatch,
    SubmitLineup,
)

from src.sports.football.contest.events import (
    GoalScored,
    GoalScorerCorrected,
    MatchConcluded,
)

from src.sports.football.contest.football_match_config import FootballMatchConfig

from src.sports.football.descriptor import FOOTBALL_SPORT


def _finished_match_with_goal():
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    home.add_player(IndividualPlayer("P10", "p10"))
    away.add_player(IndividualPlayer("Other", "other"))
    config = FootballMatchConfig(
        allow_draw=True, players_on_pitch=1, min_players_on_pitch=1
    )
    match = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)
    match.handle(StartMatch())
    match.handle(SubmitLineup(team_index=0, starting=("p9",), bench=("p10",)))
    match.handle(SubmitLineup(team_index=1, starting=("other",), bench=()))
    match.handle(ScoreGoal(team_index=0, minute=10, scorer_id="p9"))
    for _ in range(2):
        match.handle(EndPeriod())
    return match


def _setup_match_with_lineup():
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("Other", "other"))
    config = FootballMatchConfig(
        allow_draw=True, players_on_pitch=1, min_players_on_pitch=1
    )
    match = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)
    match.handle(StartMatch())
    match.handle(SubmitLineup(team_index=0, starting=("p9",), bench=()))
    match.handle(SubmitLineup(team_index=1, starting=("other",), bench=()))
    return match


def test_correct_goal_scorer_updates_stats_not_team_score() -> None:

    match = _finished_match_with_goal()

    goal = next(e for e in match.history if isinstance(e, GoalScored))

    match.handle(CorrectGoalScorer(goal_event_id=goal.event_id, new_scorer_id="p10"))

    assert any(isinstance(e, GoalScorerCorrected) for e in match.history)

    assert match.current_state.scores["home"] == 1

    assert match.current_state.player_stats["p9"].goals == 0

    assert match.current_state.player_stats["p10"].goals == 1


def test_correct_goal_scorer_rejected_before_finish() -> None:
    match = _setup_match_with_lineup()
    match.handle(ScoreGoal(team_index=0, minute=10, scorer_id="p9"))

    goal = next(e for e in match.history if isinstance(e, GoalScored))

    with pytest.raises(CommandRejected):

        match.handle(CorrectGoalScorer(goal_event_id=goal.event_id, new_scorer_id="p9"))


def test_reversal_of_match_concluded_reopens_match() -> None:

    match = _finished_match_with_goal()

    concluded = next(e for e in match.history if isinstance(e, MatchConcluded))

    match.handle(ReverseDecision(target_event_id=concluded.event_id, reason="test"))

    assert not match.current_state.is_finished

    with pytest.raises(ValueError, match="not completed"):

        match.get_official_result()


def test_reversal_of_override_restores_played_result() -> None:

    from src.sports.football.contest.commands import AwardWalkover

    from src.sports.football.contest.events import ContestResultOverridden

    match = _finished_match_with_goal()

    home = match.contestants[0]

    away = match.contestants[1]

    match.handle(AwardWalkover(winner_id=away.id, reason="commission"))

    override = next(e for e in match.history if isinstance(e, ContestResultOverridden))

    match.handle(ReverseDecision(target_event_id=override.event_id, reason="undo"))

    assert single_first_place(match.get_official_result().ranking()) is home

    assert match.get_official_result().scores == match.get_played_result().scores
