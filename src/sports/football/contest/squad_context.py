from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SquadContext:
    """External, tournament-level constraints applied to a single match's lineups.

    Currently carries the set of players suspended for this match (e.g. due to a
    red card or accumulated cautions in earlier matches).
    """

    suspended_player_ids: frozenset[str] = field(default_factory=frozenset)

    def is_suspended(self, player_id: str) -> bool:
        return player_id in self.suspended_player_ids
