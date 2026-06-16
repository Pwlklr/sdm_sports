from __future__ import annotations

from dataclasses import dataclass

from src.core.contestant.models import Contestant


@dataclass(frozen=True, kw_only=True)
class TournamentEntry:
    contestant: Contestant
    player_ids: tuple[str, ...]
