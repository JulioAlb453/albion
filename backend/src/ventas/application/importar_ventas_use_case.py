from collections.abc import Sequence

from src.core.application.importacion import ResultadoImportacion, importar
from src.core.domain.ports.i_reloj import IReloj
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin
from src.ventas.application.datos_venta import DatosVenta, construir_venta
from src.ventas.domain.ports.i_venta_repository import IVentaRepository


class ImportarVentas:
    def __init__(self, ventas: IVentaRepository, reloj: IReloj):
        self._ventas = ventas
        self._reloj = reloj

    async def ejecutar(
        self, actor: Usuario, filas: Sequence[DatosVenta], fila_inicial: int = 1
    ) -> ResultadoImportacion:
        exigir_admin(actor)
        ahora = self._reloj.ahora()
        return await importar(
            filas, lambda datos: construir_venta(datos, ahora), self._ventas.save_many, fila_inicial
        )
