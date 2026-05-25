from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.team import Team
    from src.core.tournament_event import TournamentEvent
    from src.core.tournament_phase import TournamentPhase
    from src.core.tournament_policy import TournamentPolicy
    from src.core.tournament_state import TournamentState


class Tournament:
    """
    The root aggregate managing participating teams and all phases of the tournament.
    """

    tournament_id: str
    teams: list[Team]
    current_state: TournamentState
    phases: list[TournamentPhase]

    def __init__(
        self,
        tournament_id: str,
        teams: list[Team],
        initial_state: TournamentState,
        policy: TournamentPolicy,
        phases: list[TournamentPhase] | None = None,
    ) -> None:
        self.tournament_id = tournament_id
        self.teams = teams
        self.current_state = initial_state
        self._policy = policy
        self.phases = phases if phases is not None else []

    def process_event(self, event: TournamentEvent) -> None:
        self._policy.handle(event, self.current_state)
