from __future__ import annotations



from src.core.contest import ContestFactory

from src.core.contestant.models import IndividualPlayer, Team

from src.sports.football.contest.commands import EndPeriod, ScoreGoal, StartMatch, VarOverturnGoal

from src.sports.football.contest.events import GoalScored

from src.sports.football.contest.football_match_config import FootballMatchConfig

from src.core.tournament.ranking import single_first_place
from src.sports.football.contest.football_result import FootballResult

from src.sports.football.descriptor import FOOTBALL_SPORT





def _teams() -> tuple[Team, Team]:

    home = Team("Home", "home")

    away = Team("Away", "away")

    home.add_player(IndividualPlayer("P9", "p9"))

    return home, away





def test_from_events_rebuilds_same_projection_as_live_handle() -> None:

    home, away = _teams()

    config = FootballMatchConfig()



    live = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)

    live.handle(StartMatch())

    live.handle(ScoreGoal(team_index=0, minute=10))

    live.handle(ScoreGoal(team_index=0, minute=20))



    rehydrated = ContestFactory.from_events(

        FOOTBALL_SPORT.id, [home, away], config, live.history

    )



    assert rehydrated.current_state.scores == live.current_state.scores

    assert len(rehydrated.history) == len(live.history)

    assert rehydrated.current_state.match_started is True





def test_event_log_is_source_of_truth_after_reversal() -> None:

    home, away = _teams()

    config = FootballMatchConfig()

    match = ContestFactory.create(FOOTBALL_SPORT.id, [home, away], config)

    match.handle(StartMatch())

    match.handle(ScoreGoal(team_index=0, minute=10))

    match.handle(ScoreGoal(team_index=0, minute=20))



    goal = next(e for e in match.history if isinstance(e, GoalScored) and e.minute == 10)

    match.handle(VarOverturnGoal(target_event_id=goal.event_id, reason="offside"))



    replayed = ContestFactory.from_events(

        FOOTBALL_SPORT.id, [home, away], config, match.history

    )



    assert replayed.current_state.scores["home"] == 1

    assert match.current_state.scores == replayed.current_state.scores





def test_to_result_on_completed_match() -> None:

    home, away = _teams()

    match = ContestFactory.create(

        FOOTBALL_SPORT.id, [home, away], FootballMatchConfig()

    )

    match.handle(StartMatch())

    match.handle(ScoreGoal(team_index=0, minute=10))



    for _ in range(2):

        match.handle(EndPeriod())



    final = match.get_final_result()

    assert isinstance(final, FootballResult)

    assert single_first_place(final.ranking()) is not None

