from __future__ import annotations

from typing import List

from src.core.contest import Contest
from src.core.system.sports_system_engine import SportsSystemEngine
from src.core.tournament.ranking import describe_two_way_result, single_first_place
from src.sports.darts.contest.darts_contest_state import DartsContestState
from src.sports.football.contest.state import FootballContestState


def _official_winner_label(match: Contest) -> str:
    official = match.get_official_result()
    label = describe_two_way_result(official.ranking())
    if label == "remis":
        return "Remis"
    if label.startswith("wygral "):
        return label.removeprefix("wygral ")
    winner = single_first_place(official.ranking())
    return winner.name if winner else "?"


def _football_played_outcome(state: FootballContestState) -> str:
    via = state.decided_by.replace("_", " ")
    if state.was_draw:
        return "Draw"
    return f"{state.winner.name if state.winner else '?'} ({via})"


def archived_match_lines(match_id: str, match: Contest) -> List[str]:
    state = match.current_state
    lines: List[str] = []

    if isinstance(state, DartsContestState):
        desc = " vs ".join(pl.name for pl in state.players)
        lines.append(f"\nMatch: {desc} (ID: {match_id[:8]})")
        lines.append(
            f"Format: {state.config.starting_score} Up | "
            f"Best of {state.config.sets_to_win_match} Sets"
        )
        lines.append("Final Scoreboard:")
        for pl in state.players:
            lines.append(
                f"  - {pl.name}: {state.sets_won[pl.id]} Sets, "
                f"{state.legs_won[pl.id]} Legs"
            )
        return lines

    if isinstance(state, FootballContestState):
        desc = " vs ".join(t.name for t in state.teams)
        lines.append(f"\nMatch: {desc} (ID: {match_id[:8]})")
        outcome = _football_played_outcome(state)
        if match.has_official_override():
            reason = match.official_override_reason() or "override"
            lines.append(
                f"Official Result: {_official_winner_label(match)} ({reason})"
            )
            lines.append(f"Played Result: {outcome}")
        else:
            lines.append(f"Result: {outcome}")
        lines.append("Final Score:")
        for team in state.teams:
            lines.append(f"  - {team.name}: {state.scores[team.id]} goals")
        return lines

    desc = " vs ".join(c.name for c in match.contestants)
    lines.append(f"\nMatch: {desc} (ID: {match_id[:8]})")
    return lines


def archived_matches_view(engine: SportsSystemEngine) -> List[str]:
    lines = ["\n--- Match History (Archived) ---"]
    if not engine.archived_matches:
        lines.append("No matches have been completed yet.")
        return lines

    for match_id, match in engine.archived_matches.items():
        lines.extend(archived_match_lines(match_id, match))
    lines.append("--------------------------------")
    return lines


def archived_tournaments_view(engine: SportsSystemEngine) -> List[str]:
    lines = ["\n--- Tournament History ---"]
    if not engine.tournaments:
        lines.append("No tournaments have been created yet.")
        return lines

    for tournament in engine.tournaments.values():
        status = "completed" if tournament.is_completed else "in progress"
        lines.append(f"\nTournament: {tournament.name} (ID: {tournament.id[:8]})")
        lines.append(f"  Sport: {tournament.state.sport_id}")
        lines.append(f"  Format: {tournament.state.blueprint_id}")
        lines.append(f"  Status: {status}")
        champion_id = tournament.state.champion_id
        if champion_id:
            champion_name = tournament.state.contestants.get(
                champion_id, champion_id
            )
            lines.append(f"  Champion: {champion_name}")
    return lines
