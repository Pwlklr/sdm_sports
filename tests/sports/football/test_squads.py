import pytest

from src.core.contestant.models import IndividualPlayer, Team
from src.core.shared.command_rejected import CommandRejected
from src.core.tournament.tournament_state import DisciplineState
from src.sports.football.register_tournament import FootballDisciplineCarryover
from src.sports.football.contest.commands import (
    CommitFoul,
    StartMatch,
    SubmitLineup,
    SubstitutePlayer,
)
from src.sports.football.contest.football_match_config import FootballMatchConfig
from src.core.contest import ContestFactory
from src.sports.football.descriptor import FOOTBALL_SPORT


def _match(
    max_subs: int = 3,
    *,
    players_on_pitch: int = 4,
    min_players_on_pitch: int = 2,
) -> object:
    home = Team("Home", "home")
    away = Team("Away", "away")
    for i in range(1, 7):
        home.add_player(IndividualPlayer(f"H{i}", f"h{i}"))
    for i in range(1, 3):
        away.add_player(IndividualPlayer(f"A{i}", f"a{i}"))
    match = ContestFactory.create(
        FOOTBALL_SPORT.id,
        [home, away],
        FootballMatchConfig(
            players_on_pitch=players_on_pitch,
            min_players_on_pitch=min_players_on_pitch,
            max_substitutions=max_subs,
        ),
    )
    match.handle(StartMatch())
    return match


def _submit_home_xi(match: object, count: int = 4) -> None:
    starting = tuple(f"h{i}" for i in range(1, count + 1))
    bench = tuple(f"h{i}" for i in range(count + 1, count + 3))
    match.handle(SubmitLineup(team_index=0, starting=starting, bench=bench))


def test_submit_lineup_and_substitution() -> None:
    match = _match()
    _submit_home_xi(match)
    match.handle(
        SubstitutePlayer(team_index=0, player_out="h1", player_in="h5", minute=60)
    )
    lineup = match.current_state.lineup_for("home")
    assert lineup.is_on_pitch("h5")
    assert not lineup.is_on_pitch("h1")
    assert lineup.subs_made == 1


def test_substitution_limit_enforced() -> None:
    match = _match(max_subs=1)
    _submit_home_xi(match)
    match.handle(
        SubstitutePlayer(team_index=0, player_out="h1", player_in="h5", minute=50)
    )
    with pytest.raises(CommandRejected):
        match.handle(
            SubstitutePlayer(team_index=0, player_out="h2", player_in="h4", minute=70)
        )


def test_lineup_rejects_player_not_on_roster() -> None:
    match = _match()
    with pytest.raises(CommandRejected):
        match.handle(SubmitLineup(team_index=0, starting=("ghost",), bench=()))


def test_lineup_rejects_suspended_player() -> None:
    home = Team("Home", "home")
    away = Team("Away", "away")
    for i in range(1, 7):
        home.add_player(IndividualPlayer(f"H{i}", f"h{i}"))
    for i in range(1, 3):
        away.add_player(IndividualPlayer(f"A{i}", f"a{i}"))
    match = ContestFactory.create(
        FOOTBALL_SPORT.id,
        [home, away],
        FootballMatchConfig(players_on_pitch=4),
        suspended_player_ids=frozenset({"h2"}),
    )
    match.handle(StartMatch())
    with pytest.raises(CommandRejected):
        match.handle(
            SubmitLineup(
                team_index=0,
                starting=("h1", "h2", "h3", "h4"),
                bench=("h5",),
            )
        )


def test_lineup_rejects_too_few_players() -> None:
    match = _match()
    with pytest.raises(CommandRejected, match="co najmniej"):
        match.handle(SubmitLineup(team_index=0, starting=("h1", "h2", "h3"), bench=()))


def test_insufficient_players_on_pitch_awards_walkover_to_opponent() -> None:
    match = _match(players_on_pitch=4, min_players_on_pitch=2)
    _submit_home_xi(match)
    match.handle(CommitFoul(team_index=0, minute=10, card="red", offender_id="h1"))
    match.handle(CommitFoul(team_index=0, minute=20, card="red", offender_id="h2"))
    match.handle(CommitFoul(team_index=0, minute=30, card="red", offender_id="h3"))

    assert match.current_state.is_finished
    assert match.current_state.decided_by == "walkover_insufficient_players"
    assert match.current_state.winner is match.contestants[1]
    assert match.current_state.active_players_on_pitch("home") == 1


def test_red_card_carries_over_as_suspension() -> None:
    match = _match()
    match.handle(CommitFoul(team_index=0, minute=30, card="red", offender_id="h1"))
    from dataclasses import replace

    from src.sports.football.register_tournament import FootballPhaseOutcomeInterpreter
    from src.sports.football.contest.football_result_builder import FootballResultBuilder

    state = replace(match.current_state, is_finished=True)
    result = FootballResultBuilder(config=FootballMatchConfig()).build(state)
    snapshot = FootballPhaseOutcomeInterpreter().interpret(match.id, result)
    carryover = FootballDisciplineCarryover()
    discipline = DisciplineState()
    suspensions = carryover.carryover(snapshot, discipline)
    assert ("h1", 1) in suspensions


def test_accumulated_yellows_trigger_suspension() -> None:
    from dataclasses import replace

    from src.sports.football.register_tournament import FootballPhaseOutcomeInterpreter
    from src.sports.football.contest.football_result_builder import FootballResultBuilder
    from src.sports.football.contest.player_stats import FootballPlayerStats

    carryover = FootballDisciplineCarryover()
    interpreter = FootballPhaseOutcomeInterpreter()
    builder = FootballResultBuilder(config=FootballMatchConfig())
    discipline = DisciplineState()

    match = _match()
    state = replace(match.current_state, is_finished=True)
    stats = dict(state.player_stats)
    stats["h1"] = FootballPlayerStats(player_id="h1", yellow_cards=2)
    state = replace(state, player_stats=stats)
    snap = interpreter.interpret(match.id, builder.build(state))
    suspensions = carryover.carryover(snap, discipline)
    assert ("h1", 1) in suspensions
