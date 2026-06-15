from src.core.contestant import Team


class FootballTeam(Team):
    """Represents a single football side in a contest."""

    def __init__(self, contestant_id: str, name: str) -> None:
        super().__init__(name=name, contestant_id=contestant_id)

    def __str__(self) -> str:
        return self.name
