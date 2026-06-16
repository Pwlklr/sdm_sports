from src.core.contestant.models import IndividualPlayer
from src.sports.darts.contest.darts_match_config import DartsMatchConfig
from src.sports.darts.contest.darts_result import DartsSideMetrics
from src.sports.darts.contest.darts_result_builder import DartsResultBuilder
from src.sports.darts.contest.events import MatchConcluded
from src.sports.darts.contest.darts_contest_state import create_darts_contest_state
from src.sports.darts.contest.match_metrics_reader import DartsMatchMetricsReader
from src.sports.darts.contest.player_stats import DartsPlayerStats
from dataclasses import replace


def test_darts_match_metrics_reader_reads_side_metrics() -> None:
    p1 = IndividualPlayer("A", contestant_id="p1")
    p2 = IndividualPlayer("B", contestant_id="p2")
    config = DartsMatchConfig()
    state = create_darts_contest_state([p1, p2], config)
    stats = dict(state.contestant_stats)
    stats["p1"] = DartsPlayerStats(
        contestant_id="p1", sets_won=2, legs_won=5, darts_thrown=120
    )
    state = replace(state, contestant_stats=stats)
    concluded = MatchConcluded(winner_id="p1")
    state = state.apply(concluded)
    result = DartsResultBuilder(config=config).build(state, [concluded])

    side = DartsMatchMetricsReader().player_totals(result)
    assert isinstance(side, DartsSideMetrics)
    assert side.by_contestant_id["p1"].sets_won == 2
    assert side.by_contestant_id["p1"].darts_thrown == 120
