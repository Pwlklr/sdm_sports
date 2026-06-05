from src.core.contestant import Contestant

class DartPlayer(Contestant):
    """Represents a single darts player in a contest."""
    
    def __init__(self, contestant_id: str, name: str) -> None:
        super().__init__(contestant_id=contestant_id, name=name)

    def __str__(self) -> str:
        return self.name