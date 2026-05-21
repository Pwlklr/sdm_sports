from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.contestant import Contestant


class Team:
    team_id: str
    name: str
    members: list[Contestant]

    def __init__(self, team_id: str, name: str) -> None:
        self.team_id = team_id
        self.name = name
        self.members = []

    def add_member(self, contestant: Contestant) -> None:
        self.members.append(contestant)

    def remove_member(self, contestant: Contestant) -> None:
        if contestant in self.members:
            self.members.remove(contestant)
