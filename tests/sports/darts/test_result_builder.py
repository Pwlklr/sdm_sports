from src.core.contestant import IndividualPlayer
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
    concluded = MatchConcluded(winner_id="p1")
    state = state.apply(concluded)

    result = builder.build(state, [concluded])
    ranking = result.ranking()
    assert ranking[0].contestant == p1
    assert ranking[0].place == 1
    assert ranking[1].place == 2

    side = result.side_metrics()
    assert isinstance(side, DartsSideMetrics)


def test_build_official_with_override_changes_winner() -> None:
    """build_official with a ContestResultOverridden event uses the override winner."""
    from src.sports.darts.contest.events import ContestResultOverridden

    p1 = IndividualPlayer("A", "p1")
    p2 = IndividualPlayer("B", "p2")
    config = DartsMatchConfig()
    builder = DartsResultBuilder(config=config)
    state = create_darts_contest_state([p1, p2], config)
    concluded = MatchConcluded(winner_id="p1")
    state = state.apply(concluded)

    override = ContestResultOverridden(winner_id="p2", reason="disciplinary_forfeit")
    official = builder.build_official(state, [concluded], override)

    from src.core.tournament.ranking import single_first_place

    assert single_first_place(official.ranking()) is p2
    assert official.side_metrics().decided_by == "disciplinary_forfeit"


def test_darts_multi_player_losers_share_place_ex_aequo() -> None:
    p1 = IndividualPlayer("A", "p1")
    p2 = IndividualPlayer("B", "p2")
    p3 = IndividualPlayer("C", "p3")
    config = DartsMatchConfig()
    builder = DartsResultBuilder(config=config)
    state = create_darts_contest_state([p1, p2, p3], config)
    concluded = MatchConcluded(winner_id="p1")
    state = state.apply(concluded)

    result = builder.build(state, [concluded])
    ranking = result.ranking()
    assert len(ranking) == 3
    assert ranking[0].place == 1
    assert ranking[1].place == 2
    assert ranking[2].place == 2
    assert {entry.contestant.id for entry in ranking if entry.place == 2} == {
        "p2",
        "p3",
    }
