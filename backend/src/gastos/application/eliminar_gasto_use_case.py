from src.core.domain.errors import EntidadNoEncontrada
from src.gastos.domain.ports.i_gasto_repository import IGastoRepository
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin


class EliminarGasto:
    def __init__(self, gastos: IGastoRepository):
        self._gastos = gastos

    async def ejecutar(self, actor: Usuario, gasto_id: int) -> None:
        exigir_admin(actor)
        if await self._gastos.get_by_id(gasto_id) is None:
            raise EntidadNoEncontrada(f"No existe el gasto {gasto_id}")
        await self._gastos.delete(gasto_id)
