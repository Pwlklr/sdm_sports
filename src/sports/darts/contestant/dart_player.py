from src.core.contestant import IndividualPlayer


class DartPlayer(IndividualPlayer):
    """Represents a single darts player in a contest."""

    def __init__(self, contestant_id: str, name: str) -> None:
        super().__init__(name=name, contestant_id=contestant_id)

    def __str__(self) -> str:
        return self.name
