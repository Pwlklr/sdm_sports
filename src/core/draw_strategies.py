import random
from typing import List, Tuple
from src.core.contestant import Contestant
from src.core.tournament_phase import DrawStrategy

class RandomDrawStrategy(DrawStrategy):
    """
    Pairs contestants randomly for a knockout-style bracket.
    If there is an odd number of contestants, the last one is ignored 
    (a real system would grant a 'Bye', but this simplifies the matrix).
    """
    def generate_draw(self, contestants: List[Contestant]) -> List[Tuple[Contestant, Contestant]]:
        if len(contestants) < 2:
            return []
            
        pool = list(contestants)
        random.shuffle(pool)
        
        matchups: List[Tuple[Contestant, Contestant]] = []
        for i in range(0, len(pool) - 1, 2):
            matchups.append((pool[i], pool[i+1]))
            
        return matchups


class RoundRobinDrawStrategy(DrawStrategy):
    """
    Pairs every contestant with every other contestant exactly once 
    for a Group Stage / League format.
    """
    def generate_draw(self, contestants: List[Contestant]) -> List[Tuple[Contestant, Contestant]]:
        matchups: List[Tuple[Contestant, Contestant]] = []
        
        for i in range(len(contestants)):
            for j in range(i + 1, len(contestants)):
                matchups.append((contestants[i], contestants[j]))
                
        return matchups