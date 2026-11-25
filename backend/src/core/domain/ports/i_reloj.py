from abc import ABC, abstractmethod
from datetime import datetime


class IReloj(ABC):
    """Fuente de la hora actual. Los casos de uso no llaman a `datetime.now()`: así se prueban."""

    @abstractmethod
    def ahora(self) -> datetime:
        """Hora actual en UTC, con zona."""
