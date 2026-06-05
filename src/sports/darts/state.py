from typing import List, Dict
from src.core.contest_state import ContestState
from src.core.contestant import Contestant

class DartsContestState(ContestState):
    """
    Stores the current, sport-specific state of an ongoing Darts match.
    """
    def __init__(self, players: List[Contestant], starting_score: int = 501) -> None:
        super().__init__() 
        
        self.players = players
        self.starting_score = starting_score
        
        # Use contestant_id to align with core.Contestant
        self.current_scores: Dict[str, int] = {p.contestant_id: starting_score for p in players}
        self.legs_won: Dict[str, int] = {p.contestant_id: 0 for p in players}
        self.sets_won: Dict[str, int] = {p.contestant_id: 0 for p in players}
        
        self._active_player_index = 0

    @property
    def active_player(self) -> Contestant:
        """Returns the player whose turn it currently is."""
        return self.players[self._active_player_index]

    def update_score(self, contestant_id: str, points: int) -> None:
        """Subtracts points from the specified player's current score."""
        if contestant_id in self.current_scores:
            self.current_scores[contestant_id] -= points

    def switch_turn(self) -> None:
        """Alternates the active player."""
        self._active_player_index = (self._active_player_index + 1) % len(self.players)