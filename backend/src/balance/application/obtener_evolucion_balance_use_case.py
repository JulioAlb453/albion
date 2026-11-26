from datetime import UTC, date, datetime, time

from src.balance.domain.entities.punto_balance import PuntoBalance
from src.balance.domain.ports.i_saldo_inicial_repository import ISaldoInicialRepository
from src.balance.domain.services.calculadora_balance import calcular_evolucion
from src.core.domain.errors import EntidadNoEncontrada
from src.core.domain.ports.i_reloj import IReloj
from src.gastos.domain.ports.i_gasto_repository import FiltroGastos, IGastoRepository
from src.ingresos.domain.ports.i_ingreso_repository import FiltroIngresos, IIngresoRepository
from src.pagos.domain.ports.i_pago_semanal_repository import FiltroPagos, IPagoSemanalRepository
from src.ventas.domain.ports.i_venta_repository import FiltroVentas, IVentaRepository


class ObtenerEvolucionBalance:
    def __init__(
        self,
        saldos: ISaldoInicialRepository,
        ventas: IVentaRepository,
        gastos: IGastoRepository,
        reloj: IReloj,
        ingresos: IIngresoRepository,
        pagos: IPagoSemanalRepository,
    ):
        self._ingresos = ingresos
        self._pagos = pagos
        self._saldos = saldos
        self._ventas = ventas
        self._gastos = gastos
        self._reloj = reloj

    async def ejecutar(self, hasta: date | None = None) -> list[PuntoBalance]:
        saldo = await self._saldos.get()
        if saldo is None:
            raise EntidadNoEncontrada("Falta configurar el saldo inicial")
        desde = datetime.combine(saldo.fecha, time.min, tzinfo=UTC)
        ventas = await self._ventas.list(FiltroVentas(desde=desde))
        gastos = await self._gastos.list(FiltroGastos(desde=desde))
        ingresos = await self._ingresos.list(FiltroIngresos(desde=desde))
        pagos = await self._pagos.list(FiltroPagos(pagado_desde=desde))
        return calcular_evolucion(
            saldo, ventas, gastos, hasta or self._reloj.ahora().date(), ingresos=ingresos, pagos=pagos
        )
