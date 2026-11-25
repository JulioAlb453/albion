from src.alertas.domain.entities.seguimiento import Seguimiento
from src.alertas.domain.ports.i_seguimiento_repository import ISeguimientoRepository


class ListarSeguimientos:
    def __init__(self, seguimientos: ISeguimientoRepository):
        self._seguimientos = seguimientos

    async def ejecutar(self) -> list[Seguimiento]:
        return await self._seguimientos.list_activos()
