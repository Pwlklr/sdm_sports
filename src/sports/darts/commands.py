from src.core.commands import MatchCommand
from src.core.contest import Contest
from src.sports.darts.events import DartThrownEvent

class ThrowDartCommand(MatchCommand):
    """
    Translates a terminal intent into a domain action for Darts.
    """
    def __init__(self, player_id: str, sector: int, multiplier: int) -> None:
        self.player_id = player_id
        self.sector = sector
        self.multiplier = multiplier

    def execute(self, contest: Contest) -> None:
        """
        Creates the DartThrownEvent and pushes it into the Contest's event pipeline.
        """
        event = DartThrownEvent(
            player_id=self.player_id,
            sector=self.sector,
            multiplier=self.multiplier
        )
        contest.process_event(event)