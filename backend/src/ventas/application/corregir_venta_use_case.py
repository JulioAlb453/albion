import dataclasses

from src.core.domain.errors import EntidadNoEncontrada
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin
from src.ventas.domain.entities.venta import Venta
from src.ventas.domain.ports.i_venta_repository import IVentaRepository


class CorregirVenta:
    """Corrige el encantamiento y la calidad de una venta ya registrada (lo que más se olvida).

    El precio, la cantidad y los impuestos no cambian: dependen de lo que se cobró, no del objeto.
    """

    def __init__(self, ventas: IVentaRepository):
        self._ventas = ventas

    async def ejecutar(self, actor: Usuario, venta_id: int, *, encantamiento: int, calidad: int) -> Venta:
        exigir_admin(actor)
        venta = await self._ventas.get_by_id(venta_id)
        if venta is None:
            raise EntidadNoEncontrada(f"No existe la venta {venta_id}")
        objeto = ObjetoRef(venta.objeto.base_id, encantamiento, Calidad(calidad))
        return await self._ventas.update(dataclasses.replace(venta, objeto=objeto))
