from typing import List

from src.core.contestant.models import Contestant
from src.core.tournament.event import (
    PlayerRegistered,
    RegistrationClosed,
    RegistrationOpened,
    TournamentEvent,
)


class TournamentRegistration:
    """Manages the registration phase of a tournament."""

    def __init__(self) -> None:
        self.is_open: bool = False
        self._contestants: List[Contestant] = []

    @property
    def registered_contestants(self) -> List[Contestant]:
        return self._contestants.copy()

    def open_registration(self) -> List[TournamentEvent]:
        self.is_open = True
        return [RegistrationOpened()]

    def register(self, contestant: Contestant) -> List[TournamentEvent]:
        if not self.is_open:
            raise ValueError("Cannot register: Registration is not open.")
        if contestant in self._contestants:
            raise ValueError(
                f"Contestant {contestant.display_name} is already registered."
            )

        self._contestants.append(contestant)
        return [PlayerRegistered(contestant)]

    def close_registration(self) -> List[TournamentEvent]:
        self.is_open = False
        return [RegistrationClosed()]
