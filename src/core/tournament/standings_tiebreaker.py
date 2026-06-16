from __future__ import annotations

from src.core.tournament.phase_state import GroupStandingRow
from src.core.tournament.sport_tournament_profile import StandingsTiebreaker


class DefaultStandingsTiebreaker(StandingsTiebreaker):
    def order(self, contestant_ids: list[str], standings: object) -> list[str]:
        if not isinstance(standings, dict):
            return contestant_ids
        rows: list[GroupStandingRow] = []
        for cid in contestant_ids:
            row = standings.get(cid)
            if isinstance(row, GroupStandingRow):
                rows.append(row)
        rows.sort(key=lambda r: (r.points, r.wins, -r.losses), reverse=True)
        return [r.contestant_id for r in rows]
