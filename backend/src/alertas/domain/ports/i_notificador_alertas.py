from abc import ABC, abstractmethod

from src.alertas.domain.entities.alerta import Alerta


class INotificadorAlertas(ABC):
    """Salida de las alertas. La implementación real publica en el canal de Discord."""

    @abstractmethod
    async def notificar(self, alerta: Alerta) -> None: ...
