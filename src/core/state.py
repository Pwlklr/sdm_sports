from abc import ABC


class ContestState(ABC):
    """
    A structure storing the current, sport-specific state of an ongoing match.
    """

    def __init__(self) -> None:
        self.is_final: bool = False
