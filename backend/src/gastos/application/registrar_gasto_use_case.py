from src.core.domain.ports.i_reloj import IReloj
from src.gastos.application.datos_gasto import DatosGasto, construir_gasto
from src.gastos.domain.entities.gasto import Gasto
from src.gastos.domain.ports.i_gasto_repository import IGastoRepository
from src.usuarios.domain.entities.usuario import Usuario
from src.usuarios.domain.services.autorizacion import exigir_admin


class RegistrarGasto:
    def __init__(self, gastos: IGastoRepository, reloj: IReloj):
        self._gastos = gastos
        self._reloj = reloj

    async def ejecutar(self, actor: Usuario, datos: DatosGasto) -> Gasto:
        exigir_admin(actor)
        return await self._gastos.save(construir_gasto(datos, self._reloj.ahora()))
