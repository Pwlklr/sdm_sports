import uuid
from typing import Dict, Optional, List

from src.core.contestant import Contestant, IndividualPlayer, Team
from src.core.tournament import Tournament
from src.core.contest import Contest
from src.core.commands import MatchCommand
from src.core.plugin import SportPlugin

class SportsSystemEngine:
    """
    Facade Pattern: The central entry point for the sports library.
    Maintains in-memory repositories and acts as a command dispatcher.
    """
    def __init__(self) -> None:
        self.global_players: Dict[str, Contestant] = {}
        self.tournaments: Dict[str, Tournament] = {}
        self.active_matches: Dict[str, Contest] = {}
        self.archived_matches: Dict[str, Contest] = {}
        self.plugins: Dict[str, SportPlugin] = {}

    def register_plugin(self, plugin: SportPlugin) -> None:
        """Registers a sport extension module into the core system."""
        self.plugins[plugin.name] = plugin

    def get_available_plugins(self) -> List[SportPlugin]:
        """Returns all registered sports."""
        return list(self.plugins.values())

    def create_individual_player(self, name: str, metadata: Optional[Dict[str, str]] = None) -> IndividualPlayer:
        player = IndividualPlayer(name, metadata=metadata)
        self.global_players[player.id] = player
        return player
        
    def create_team(self, name: str, metadata: Optional[Dict[str, str]] = None) -> Team:
        team = Team(name, metadata=metadata)
        self.global_players[team.id] = team
        return team

    def create_tournament(self, name: str, tournament_id: Optional[str] = None) -> Tournament:
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

    def dispatch_match_command(self, match_id: str, command: MatchCommand) -> None:
        match = self.get_match(match_id)
        if not match:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
        command.execute(match)