from src.core.contestant import IndividualPlayer
from src.core.contest.metrics import EmptyIndividualMetrics
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.darts_result import DartsSideMetrics
from src.sports.darts.contest.darts_result_builder import DartsResultBuilder
from src.sports.darts.contest.events import MatchConcluded
from src.sports.darts.contest.darts_contest_state import create_darts_contest_state


def test_darts_ranking_and_side_metrics() -> None:
    p1 = IndividualPlayer("A", "p1")
    p2 = IndividualPlayer("B", "p2")
    config = DartsMatchConfig()
    builder = DartsResultBuilder(config=config)
    state = create_darts_contest_state([p1, p2], config)
    state = state.apply(MatchConcluded(winner_id="p1"))
    result = builder.build(state)

    ranking = result.ranking()
    assert ranking[0].contestant == p1
    assert ranking[0].place == 1
    assert ranking[1].place == 2

    side = result.side_metrics()
    assert isinstance(side, DartsSideMetrics)
    assert isinstance(result.individual_metrics(), EmptyIndividualMetrics)
