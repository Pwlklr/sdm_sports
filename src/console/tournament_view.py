from __future__ import annotations

from typing import List

from src.core.contest import Contest
from src.core.contest.contest_session import ContestSessionStatus, session_status_label
from src.core.tournament.phase_state import RoundRobinPhaseState
from src.core.tournament.ranking import (
    TwoWayResultKind,
    classify_two_way_result,
)
from src.core.tournament.sport_tournament_registry import SportTournamentRegistry
from src.core.tournament.tournament import Tournament


def active_matches(tournament: Tournament) -> List[Contest]:
    pending = tournament.pending_match_ids()
    matches: List[Contest] = []
    for mid in pending:
        match = tournament.get_match(mid)
        if match is not None:
            matches.append(match)
    return matches


def standings_table(tournament: Tournament) -> List[str]:
    phase_id = tournament.active_phase_id()
    if phase_id is None:
        return ["(no active phase)"]
    ps = tournament.state.phase_states.get(phase_id)
    if not isinstance(ps, RoundRobinPhaseState):
        return []
    profile = SportTournamentRegistry.get(tournament.state.sport_id)
    ordered_ids = profile.tiebreaker.order(list(ps.standings.keys()), ps)
    lines: List[str] = []
    for cid in ordered_ids:
        row = ps.standings.get(cid)
        if row is None:
            continue
        name = tournament.state.contestants.get(cid, cid)
        lines.append(
            f"{name}: {row.points}pts ({row.wins}W-{row.draws}D-{row.losses}L)"
        )
    return lines


def match_session_tag(match: Contest) -> str:
    status = match.session_status
    if status is ContestSessionStatus.NOT_STARTED:
        return ""
    return f" [{session_status_label(status)}]"


def _format_fixture_status(contest: Contest | None) -> str:
    if contest is None:
        return "pending"
    status = contest.session_status
    if status is ContestSessionStatus.SUSPENDED:
        return "suspended"
    if status is ContestSessionStatus.IN_PROGRESS:
        return "in progress"
    if status is ContestSessionStatus.FINISHED:
        return _format_final_status(contest)
    return "pending"


def _format_final_status(contest: Contest) -> str:
    if not contest.current_state.is_finished:
        return "pending"
    try:
        result = contest.get_official_result()
    except ValueError:
        return "pending"
    outcome = classify_two_way_result(result.ranking())
    if outcome.kind is TwoWayResultKind.DRAW:
        return "draw"
    if outcome.winner is not None:
        return f"won {outcome.winner.name}"
    return "finished"


def schedule_view(tournament: Tournament) -> List[str]:
    state = tournament.state
    phase_id = tournament.active_phase_id()
    if phase_id is None:
        return ["(no active phase)"]
    ps = state.phase_states.get(phase_id)
    if ps is None:
        return []
    lines: List[str] = []
    for index, fixture in enumerate(ps.fixtures, start=1):
        name_a = state.contestants.get(fixture.side_a_id, fixture.side_a_id)
        name_b = state.contestants.get(fixture.side_b_id, fixture.side_b_id)
        pairing = f"{name_a} vs {name_b}"
        contest = tournament.get_match(fixture.contest_id)
        status = _format_fixture_status(contest)
        lines.append(f"{index}. {pairing} - {status}")
    return lines
