from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.ports.i_alerta_repository import IAlertaRepository


class ListarAlertas:
    def __init__(self, alertas: IAlertaRepository):
        self._alertas = alertas

    async def ejecutar(self, limite: int = 50) -> list[Alerta]:
        return await self._alertas.list_recientes(limite)
