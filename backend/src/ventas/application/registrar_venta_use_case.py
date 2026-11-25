from src.core.domain.ports.i_reloj import IReloj
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin
from src.ventas.application.datos_venta import DatosVenta, construir_venta
from src.ventas.domain.entities.venta import Venta
from src.ventas.domain.ports.i_venta_repository import IVentaRepository


class RegistrarVenta:
    def __init__(self, ventas: IVentaRepository, reloj: IReloj):
        self._ventas = ventas
        self._reloj = reloj

    async def ejecutar(self, actor: Usuario, datos: DatosVenta) -> Venta:
        exigir_admin(actor)
        return await self._ventas.save(construir_venta(datos, self._reloj.ahora()))
