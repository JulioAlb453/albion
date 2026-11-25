from src.alertas.domain.ports.i_seguimiento_repository import ISeguimientoRepository
from src.core.domain.errors import EntidadNoEncontrada
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin


class EliminarSeguimiento:
    def __init__(self, seguimientos: ISeguimientoRepository):
        self._seguimientos = seguimientos

    async def ejecutar(self, actor: Usuario, seguimiento_id: int) -> None:
        exigir_admin(actor)
        if await self._seguimientos.get_by_id(seguimiento_id) is None:
            raise EntidadNoEncontrada(f"No existe el seguimiento {seguimiento_id}")
        await self._seguimientos.delete(seguimiento_id)
