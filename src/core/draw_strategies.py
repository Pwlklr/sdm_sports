from __future__ import annotations
import random
from typing import TYPE_CHECKING

from src.core.tournament_phase import DrawStrategy

if TYPE_CHECKING:
    from src.core.contestant import Contestant

class RandomKnockoutDrawStrategy(DrawStrategy):
    """
    Randomly pairs contestants for a 1v1 knockout round.
    Requires an even number of contestants.
    """
    
    def generate_draw(self, contestants: list[Contestant]) -> list[tuple[Contestant, Contestant]]:
        if len(contestants) % 2 != 0:
            raise ValueError("Knockout draw requires an even number of contestants.")
        
        # Create a shallow copy to avoid mutating the original list
        shuffled = contestants.copy()
        random.shuffle(shuffled)
        
        matchups: list[tuple[Contestant, Contestant]] = []
        for i in range(0, len(shuffled), 2):
            matchups.append((shuffled[i], shuffled[i+1]))
            
        return matchups