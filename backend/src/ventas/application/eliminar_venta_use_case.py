from src.core.domain.errors import EntidadNoEncontrada
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin
from src.ventas.domain.ports.i_venta_repository import IVentaRepository


class EliminarVenta:
    def __init__(self, ventas: IVentaRepository):
        self._ventas = ventas

    async def ejecutar(self, actor: Usuario, venta_id: int) -> None:
        exigir_admin(actor)
        if await self._ventas.get_by_id(venta_id) is None:
            raise EntidadNoEncontrada(f"No existe la venta {venta_id}")
        await self._ventas.delete(venta_id)
