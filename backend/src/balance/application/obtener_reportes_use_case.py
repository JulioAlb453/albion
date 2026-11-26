from datetime import datetime

from src.balance.domain.entities.reportes import Reportes
from src.balance.domain.services.generador_reportes import generar_reportes
from src.core.application.fechas import a_utc_o_none
from src.gastos.domain.ports.i_gasto_repository import FiltroGastos, IGastoRepository
from src.ingresos.domain.ports.i_ingreso_repository import FiltroIngresos, IIngresoRepository
from src.pagos.domain.ports.i_pago_semanal_repository import FiltroPagos, IPagoSemanalRepository
from src.ventas.domain.ports.i_venta_repository import FiltroVentas, IVentaRepository


class ObtenerReportes:
    def __init__(
        self,
        ventas: IVentaRepository,
        gastos: IGastoRepository,
        ingresos: IIngresoRepository,
        pagos: IPagoSemanalRepository,
    ):
        self._ventas = ventas
        self._gastos = gastos
        self._ingresos = ingresos
        self._pagos = pagos

    async def ejecutar(
        self, desde: datetime | None = None, hasta: datetime | None = None
    ) -> Reportes:
        desde, hasta = a_utc_o_none(desde), a_utc_o_none(hasta)
        ventas = await self._ventas.list(FiltroVentas(desde=desde, hasta=hasta))
        gastos = await self._gastos.list(FiltroGastos(desde=desde, hasta=hasta))
        ingresos = await self._ingresos.list(FiltroIngresos(desde=desde, hasta=hasta))
        pagos = await self._pagos.list(FiltroPagos(pagado_desde=desde, pagado_hasta=hasta))
        return generar_reportes(ventas, gastos, ingresos, pagos)
