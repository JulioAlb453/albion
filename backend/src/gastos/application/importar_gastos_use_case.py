from collections.abc import Sequence

from src.core.application.importacion import ResultadoImportacion, importar
from src.core.domain.ports.i_reloj import IReloj
from src.gastos.application.datos_gasto import DatosGasto, construir_gasto
from src.gastos.domain.ports.i_gasto_repository import IGastoRepository
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin


class ImportarGastos:
    def __init__(self, gastos: IGastoRepository, reloj: IReloj):
        self._gastos = gastos
        self._reloj = reloj

    async def ejecutar(
        self, actor: Usuario, filas: Sequence[DatosGasto], fila_inicial: int = 1
    ) -> ResultadoImportacion:
        exigir_admin(actor)
        ahora = self._reloj.ahora()
        return await importar(
            filas, lambda datos: construir_gasto(datos, ahora), self._gastos.save_many, fila_inicial
        )
