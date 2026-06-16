from dataclasses import replace

from src.core.contest.contest_result import RankedEntry
from src.core.contestant.models import IndividualPlayer, Team
from src.sports.football.contest.events import ContestResultOverridden, MatchConcluded
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.sports.football.contest.football_result import FootballSideMetrics
from src.sports.football.contest.football_result_builder import FootballResultBuilder
from src.sports.football.contest.player_stats import FootballPlayerStats
from src.sports.football.contest.football_contest_state import create_football_contest_state


def _teams():
    home = Team("Home", "home")
    away = Team("Away", "away")
    home.add_player(IndividualPlayer("P9", "p9"))
    away.add_player(IndividualPlayer("P10", "p10"))
    return home, away


def test_draw_ranking_ex_aequo() -> None:
    home, away = _teams()
    config = FootballMatchConfig()
    builder = FootballResultBuilder(config=config)
    state = create_football_contest_state([home, away], config)
    state = replace(
        state,
        is_finished=True,
        was_draw=True,
        scores={home.id: 1, away.id: 1},
    )
    result = builder.build(state)
    ranking = result.ranking()
    assert len(ranking) == 2
    assert ranking[0].place == 1
    assert ranking[1].place == 1


def test_winner_ranking() -> None:
    home, away = _teams()
    config = FootballMatchConfig()
    builder = FootballResultBuilder(config=config)
    state = create_football_contest_state([home, away], config)
    state = state.apply(
        MatchConcluded(winner_id=home.id, draw=False, decided_by="regulation")
    )
    result = builder.build(state)
    ranking = result.ranking()
    assert ranking[0].contestant == home
    assert ranking[0].place == 1
    assert ranking[1].contestant == away
    assert ranking[1].place == 2


def test_player_stats_nested_in_side_metrics() -> None:
    home, away = _teams()
    config = FootballMatchConfig()
    builder = FootballResultBuilder(config=config)
    state = create_football_contest_state([home, away], config)
    stats = dict(state.player_stats)
    stats["p9"] = FootballPlayerStats(player_id="p9", goals=2, yellow_cards=1)
    state = replace(state, player_stats=stats)
    state = state.apply(
        MatchConcluded(winner_id=None, draw=True, decided_by="regulation")
    )
    result = builder.build(state)
    side = result.side_metrics()
    assert isinstance(side, FootballSideMetrics)
    assert side.by_team_id[home.id].players["p9"].goals == 2
    assert side.by_team_id[home.id].players["p9"].yellow_cards == 1
    assert side.all_players()["p9"].goals == 2


def test_build_official_overrides_team_scores_keeps_player_stats() -> None:
    home, away = _teams()
    config = FootballMatchConfig()
    builder = FootballResultBuilder(config=config)
    state = create_football_contest_state([home, away], config)
    stats = dict(state.player_stats)
    stats["p9"] = FootballPlayerStats(player_id="p9", goals=1, yellow_cards=1)
    state = replace(
        state,
        player_stats=stats,
        scores={home.id: 1, away.id: 0},
        is_finished=True,
        winner=home,
        decided_by="regulation",
    )
    override = ContestResultOverridden(
        winner_id=away.id,
        reason="walkover",
        winner_score=3,
        loser_score=0,
    )
    result = builder.build_official(state, override)
    assert result.scores == {home.id: 0, away.id: 3}
    side = result.side_metrics()
    assert side.by_team_id[home.id].players["p9"].goals == 1
    assert side.by_team_id[home.id].players["p9"].yellow_cards == 1
