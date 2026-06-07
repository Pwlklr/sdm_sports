import uuid
from typing import Dict, Optional

from src.core.contestant import Contestant, IndividualPlayer, Team
from src.core.tournament import Tournament
from src.core.contest import Contest
from src.core.commands import MatchCommand

class SportsSystemEngine:
    """
    Facade Pattern: The central entry point for the sports library.
    Maintains in-memory repositories and acts as a command dispatcher.
    """
    def __init__(self) -> None:
        # In-Memory Repositories
        self.global_players: Dict[str, Contestant] = {}
        self.tournaments: Dict[str, Tournament] = {}
        self.active_matches: Dict[str, Contest] = {}
        self.archived_matches: Dict[str, Contest] = {}

    def create_individual_player(self, name: str, metadata: Optional[Dict[str, str]] = None) -> IndividualPlayer:
        """Registers a new individual player globally in the system."""
        player = IndividualPlayer(name, metadata=metadata)
        self.global_players[player.id] = player
        return player
        
    def create_team(self, name: str, metadata: Optional[Dict[str, str]] = None) -> Team:
        """Registers a new team globally in the system."""
        team = Team(name, metadata=metadata)
        self.global_players[team.id] = team
        return team

    def create_tournament(self, name: str, tournament_id: Optional[str] = None) -> Tournament:
        """Creates and stores a new tournament aggregate."""
        # Generate a unique ID if one is not provided to satisfy the Tournament signature
        t_id = tournament_id or str(uuid.uuid4())
        tournament = Tournament(name, t_id)
        self.tournaments[tournament.id] = tournament
        return tournament

    def register_active_match(self, match: Contest) -> None:
        """Loads a match into the active memory repository."""
        self.active_matches[match.id] = match

    def get_match(self, match_id: str) -> Optional[Contest]:
        """Retrieves a match from memory by its ID."""
        return self.active_matches.get(match_id)

    def archive_match(self, match_id: str) -> None:
        """Moves a finished match from active memory to the archive repository."""
        if match_id not in self.active_matches:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
        
        match = self.active_matches.pop(match_id)
        self.archived_matches[match.id] = match

    def dispatch_match_command(self, match_id: str, command: MatchCommand) -> None:
        """
        Command Dispatcher: Finds the active match and executes the command against it.
        This prevents the UI from ever mutating match state directly.
        """
        match = self.get_match(match_id)
        if not match:
            raise ValueError(f"Match with ID '{match_id}' not found in active memory.")
            
        command.execute(match)