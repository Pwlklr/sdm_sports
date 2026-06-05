from typing import List, Dict
from src.core.contest_state import ContestState
from src.core.contestant import Contestant
from src.sports.darts.config import DartsMatchConfig

class DartsContestState(ContestState):
    def __init__(self, players: List[Contestant], config: DartsMatchConfig = DartsMatchConfig()) -> None:
        super().__init__() 
        
        self.players = players
        self.config = config
        self.is_completed = False
        self.winner_id: str | None = None
        
        # Deep Domain State Tracking
        self.current_scores: Dict[str, int] = {p.contestant_id: config.starting_score for p in players}
        self.turn_start_scores: Dict[str, int] = {p.contestant_id: config.starting_score for p in players}
        self.legs_won: Dict[str, int] = {p.contestant_id: 0 for p in players}
        self.sets_won: Dict[str, int] = {p.contestant_id: 0 for p in players}
        
        self._active_player_index = 0
        self.darts_thrown_this_turn = 0
        
        # UI Feedback hook
        self.last_action_message = "Match Started!"

    @property
    def active_player(self) -> Contestant:
        return self.players[self._active_player_index]

    def update_score(self, contestant_id: str, points: int) -> None:
        if contestant_id in self.current_scores and not self.is_completed:
            self.current_scores[contestant_id] -= points

    def reset_for_new_leg(self) -> None:
        for p in self.players:
            self.current_scores[p.contestant_id] = self.config.starting_score
            self.turn_start_scores[p.contestant_id] = self.config.starting_score
        self.darts_thrown_this_turn = 0

    def reset_for_new_set(self) -> None:
        self.reset_for_new_leg()
        for p in self.players:
            self.legs_won[p.contestant_id] = 0

    def switch_turn(self) -> None:
        if not self.is_completed:
            self._active_player_index = (self._active_player_index + 1) % len(self.players)
            self.darts_thrown_this_turn = 0
            # Synchronize the backup score for the new player's turn
            current_player_id = self.active_player.contestant_id
            self.turn_start_scores[current_player_id] = self.current_scores[current_player_id]