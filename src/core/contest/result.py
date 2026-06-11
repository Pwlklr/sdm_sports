from abc import ABC, abstractmethod


class Result(ABC):
    """Sport-specific outcome of a completed contest.

    Core code treats this as an opaque finished marker. Each sport exposes its
    own result type (scores, ranking table, winner-only, etc.); downstream
    layers interpret via isinstance / dedicated readers — not via a shared winner API.
    """

    @abstractmethod
    def is_finished(self) -> bool:
        pass
