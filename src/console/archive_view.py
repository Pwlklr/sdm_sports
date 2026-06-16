from __future__ import annotations

from typing import List

from src.core.contest import Contest
from src.core.system.sports_system_engine import SportsSystemEngine


def archived_match_lines(
    engine: SportsSystemEngine, match_id: str, match: Contest
) -> List[str]:
    for sport in engine.get_available_sports():
        adapter = sport.adapter
        if adapter is None:
            continue
        lines = adapter.format_archived_match_lines(match_id, match)
        if lines:
            return lines
    desc = " vs ".join(c.name for c in match.contestants)
    return [f"\nMatch: {desc} (ID: {match_id[:8]})"]


def archived_matches_view(engine: SportsSystemEngine) -> List[str]:
    lines = ["\n--- Match History (Archived) ---"]
    if not engine.archived_matches:
        lines.append("No matches have been completed yet.")
        return lines

    for match_id, match in engine.archived_matches.items():
        lines.extend(archived_match_lines(engine, match_id, match))
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
            champion_name = tournament.state.contestants.get(champion_id, champion_id)
            lines.append(f"  Champion: {champion_name}")
    return lines
