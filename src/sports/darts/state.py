from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional
from src.core.contest_state import ContestState
from src.sports.darts.entities import DartTurn

if TYPE_CHECKING:
    from src.core.contestant import Contestant
    from src.sports.darts.config import DartsMatchConfig

class DartsContestState(ContestState):
    """
    Manages the overarching state of a Darts match, delegating throw
    logic to the DartTurn aggregate.
    """
    def __init__(
        self,
        players: List[Contestant],
        config: Optional[DartsMatchConfig] = None,
        starting_score: int = 501,
        sets_to_win: int = 3,
        legs_to_win_set: int = 3
    ) -> None:
        super().__init__()
        if not players:
            raise ValueError("A match requires at least one contestant.")
            
        self.players = players
        
        # Hydrate from config or kwargs
        if config:
            self.starting_score = config.starting_score
            self.sets_to_win = config.sets_to_win_match
            self.legs_to_win_set = config.legs_to_win_set
            self.in_multiplier = config.in_multiplier
            self.out_multiplier = config.out_multiplier
        else:
            self.starting_score = starting_score
            self.sets_to_win = sets_to_win
            self.legs_to_win_set = legs_to_win_set
            self.in_multiplier = 1
            self.out_multiplier = 2

        # Deep State Tracking
        self.scores: Dict[str, int] = {p.id: self.starting_score for p in players}
        self.legs_won: Dict[str, int] = {p.id: 0 for p in players}
        self.sets_won: Dict[str, int] = {p.id: 0 for p in players}

        # Lifecycle Tracking
        self.leg_starting_player_idx: int = 0
        self.current_player_idx: int = 0
        self.current_turn: Optional[DartTurn] = None
        self.turn_starting_score: int = self.starting_score
        self.is_completed: bool = False

    @property
    def current_player(self) -> Contestant:
        return self.players[self.current_player_idx]

    def start_new_turn(self) -> None:
        """Initializes a new DartTurn and snapshots the score for penalty reversions."""
        self.current_turn = DartTurn()
        self.turn_starting_score = self.scores[self.current_player.id]

    def advance_player(self) -> None:
        """Passes the turn to the next player."""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def reset_for_new_leg(self) -> None:
        """Resets point scores for a new leg and rotates the starting player."""
        for p in self.players:
            self.scores[p.id] = self.starting_score
        
        # Rotate who starts the leg
        self.leg_starting_player_idx = (self.leg_starting_player_idx + 1) % len(self.players)
        self.current_player_idx = self.leg_starting_player_idx
        
        self.current_turn = None