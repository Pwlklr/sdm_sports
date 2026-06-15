import uuid
from typing import Any, Dict, Iterable, List, Optional

from src.core.contest import Contest
from src.core.contest.command import Command
from src.core.contest.contest_result import ContestOutcome, ContestResult
from src.core.contestant.models import Contestant, IndividualPlayer, Team
from src.core.sport.console_adapter import ConsoleAdapter
from src.core.sport.registered_sport import RegisteredSport
from src.core.sport.sport_descriptor import SportDescriptor
from src.core.sport.sport_plugin import SportPlugin
from src.core.tournament import Tournament
from src.core.tournament.event import MatchScheduled


class SportsSystemEngine:
    """Central entry point: repositories and command dispatch for the sports library."""

    def __init__(self, sports: Iterable[SportPlugin] = ()) -> None:
        self.global_players: Dict[str, Contestant] = {}
        self.tournaments: Dict[str, Tournament] = {}
        self.active_matches: Dict[str, Contest] = {}
        self.archived_matches: Dict[str, Contest] = {}
        self._sports: Dict[str, RegisteredSport] = {}
        for plugin in sports:
            self.register_plugin(plugin)

    def register_plugin(self, plugin: SportPlugin) -> None:
        self._sports[plugin.descriptor.id] = RegisteredSport(
            plugin.descriptor,
            plugin.adapter,
            plugin.match_metrics_reader,
        )

    def register_sport(
        self,
        descriptor: SportDescriptor,
        adapter: ConsoleAdapter,
        match_metrics_reader: Any = None,
    ) -> None:
        if adapter.descriptor != descriptor:
            raise ValueError(
                f"Adapter descriptor '{adapter.descriptor.id}' does not match "
                f"registered sport '{descriptor.id}'."
            )
        self._sports[descriptor.id] = RegisteredSport(
            descriptor, adapter, match_metrics_reader
        )

    def get_available_sports(self) -> List[RegisteredSport]:
        return list(self._sports.values())

    def get_sport(self, sport_id: str) -> Optional[RegisteredSport]:
        return self._sports.get(sport_id)

    def get_adapter(self, sport_id: str) -> Optional[ConsoleAdapter]:
        sport = self._sports.get(sport_id)
        return sport.adapter if sport else None

    def get_match_metrics_reader(self, sport_id: str) -> Any:
        sport = self._sports.get(sport_id)
        return sport.match_metrics_reader if sport else None

    def create_individual_player(
        self, name: str, metadata: Optional[Dict[str, str]] = None
    ) -> IndividualPlayer:
        player = IndividualPlayer(name, metadata=metadata)
        self.global_players[player.id] = player
        return player

    def create_team(self, name: str, metadata: Optional[Dict[str, str]] = None) -> Team:
        team = Team(name, metadata=metadata)
        self.global_players[team.id] = team
        return team

    def create_team_with_roster(
        self,
        name: str,
        player_names: List[str],
        metadata: Optional[Dict[str, str]] = None,
    ) -> Team:
        """Register a team whose squad lives on the roster, not in the global individuals pool."""
        team = self.create_team(name, metadata=metadata)
        for player_name in player_names:
            team.add_player(IndividualPlayer(player_name))
        return team

    def list_individual_players(self) -> List[IndividualPlayer]:
        return [
            contestant
            for contestant in self.global_players.values()
            if isinstance(contestant, IndividualPlayer)
        ]

    def list_teams(self) -> List[Team]:
        return [
            contestant
            for contestant in self.global_players.values()
            if isinstance(contestant, Team)
        ]

    def create_tournament(
        self, name: str, tournament_id: Optional[str] = None
    ) -> Tournament:
        t_id = tournament_id or str(uuid.uuid4())
        tournament = Tournament(name, t_id)
        self.tournaments[tournament.id] = tournament
        return tournament

    def register_active_match(self, match: Contest) -> None:
        self.active_matches[match.id] = match

    def get_match(self, match_id: str) -> Optional[Contest]:
        return self.active_matches.get(match_id)

    def archive_match(self, match_id: str) -> None:
        if match_id not in self.active_matches:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
        match = self.active_matches.pop(match_id)
        self.archived_matches[match.id] = match

    def dispatch_match_command(self, match_id: str, command: Command) -> None:
        match = self.get_match(match_id)
        if not match:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
        match.handle(command)

    def setup_tournament(
        self,
        tournament: Tournament,
        sport_id: str,
        config: Any,
        contestants: List[Contestant],
    ) -> List[MatchScheduled]:
        tournament.open_registration()
        for contestant in contestants:
            tournament.register_player(contestant)

        events = tournament.close_registration(sport_id, config)
        return [event for event in events if isinstance(event, MatchScheduled)]

    def complete_tournament_match(self, tournament: Tournament, match_id: str) -> None:
        match = self.get_match(match_id)
        if match is None:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
        tournament.complete_match(match)

    def override_result(
        self, match_id: str, result: ContestResult, reason: str
    ) -> None:
        """Set the official result outside the event log (walkover, commission, forfeit, etc.).

        The played outcome stays on ``Contest.result.played``; ``Contest.result`` delegates
        to the override for all official reads.
        """
        match = self.active_matches.get(match_id) or self.archived_matches.get(match_id)
        if match is None:
            raise ValueError(f"Match with ID '{match_id}' not found.")
        match.result.apply_override(result, reason)

    def award_walkover(
        self, match_id: str, winner: Optional[Contestant], reason: str = "walkover"
    ) -> None:
        """Convenience wrapper: override with a minimal walkover/forfeit outcome."""
        self.override_result(
            match_id,
            ContestOutcome(winner=winner, decided_by=reason),
            reason=reason,
        )
