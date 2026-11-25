from datetime import datetime

from src.balance.domain.entities.reportes import Reportes
from src.balance.domain.services.generador_reportes import generar_reportes
from src.core.application.fechas import a_utc_o_none
from src.gastos.domain.ports.i_gasto_repository import FiltroGastos, IGastoRepository
from src.ventas.domain.ports.i_venta_repository import FiltroVentas, IVentaRepository


class ObtenerReportes:
    def __init__(self, ventas: IVentaRepository, gastos: IGastoRepository):
        self._ventas = ventas
        self._gastos = gastos

    async def ejecutar(
        self, desde: datetime | None = None, hasta: datetime | None = None
    ) -> Reportes:
        desde, hasta = a_utc_o_none(desde), a_utc_o_none(hasta)
        ventas = await self._ventas.list(FiltroVentas(desde=desde, hasta=hasta))
        gastos = await self._gastos.list(FiltroGastos(desde=desde, hasta=hasta))
        return generar_reportes(ventas, gastos)
