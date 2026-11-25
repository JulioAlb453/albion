from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.ports.i_notificador_alertas import INotificadorAlertas


class NotificadorNulo(INotificadorAlertas):
    """Sin webhook configurado: las alertas se guardan y se ven en la web, pero no se publican."""

    async def notificar(self, alerta: Alerta) -> None:
        return None
