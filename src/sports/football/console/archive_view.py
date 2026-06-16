from __future__ import annotations

from src.core.contest import Contest
from src.core.tournament.ranking import TwoWayResultKind, classify_two_way_result
from src.sports.football.contest.football_contest_state import FootballContestState


def format_football_archived_match_lines(
    match_id: str, match: Contest, state: FootballContestState
) -> list[str]:
    desc = " vs ".join(t.name for t in state.teams)
    lines = [f"\nMatch: {desc} (ID: {match_id[:8]})"]
    outcome = _football_played_outcome(match, state)
    if match.has_official_override():
        reason = match.official_override_reason() or "override"
        lines.append(f"Official Result: {_official_winner_label(match)} ({reason})")
        lines.append(f"Played Result: {outcome}")
    else:
        lines.append(f"Result: {outcome}")
    lines.append("Final Score:")
    for team in state.teams:
        lines.append(f"  - {team.name}: {state.scores[team.id]} goals")
    return lines


def _official_winner_label(match: Contest) -> str:
    outcome = classify_two_way_result(match.get_official_result().ranking())
    if outcome.kind is TwoWayResultKind.DRAW:
        return "Remis"
    if outcome.winner is not None:
        return outcome.winner.name
    return "?"


def _football_played_outcome(match: Contest, state: FootballContestState) -> str:
    if state.was_draw:
        return "Draw"
    try:
        via = match.get_played_result().decided_by.replace("_", " ")
    except Exception:
        via = "regulation"
    return f"{state.winner.name if state.winner else '?'} ({via})"
