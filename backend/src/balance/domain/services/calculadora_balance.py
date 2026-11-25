from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta

from src.balance.domain.entities.punto_balance import PuntoBalance
from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.gastos.domain.entities.gasto import Gasto
from src.ventas.domain.entities.venta import Venta


def calcular_evolucion(
    saldo_inicial: SaldoInicial,
    ventas: Iterable[Venta],
    gastos: Iterable[Gasto],
    hasta: date | None = None,
) -> list[PuntoBalance]:
    """Saldo al cierre de cada día, desde la fecha del saldo inicial.

    Los movimientos anteriores a esa fecha se ignoran: ya están contados en el saldo
    inicial. Los días sin movimientos también aparecen, para que la gráfica sea continua.
    """
    inicio = saldo_inicial.fecha
    ingresos_por_dia: dict[date, int] = defaultdict(int)
    gastos_por_dia: dict[date, int] = defaultdict(int)
    for venta in ventas:
        if venta.fecha.date() >= inicio:
            ingresos_por_dia[venta.fecha.date()] += venta.desglose.neto
    for gasto in gastos:
        if gasto.fecha.date() >= inicio:
            gastos_por_dia[gasto.fecha.date()] += gasto.monto

    fin = max([inicio, *ingresos_por_dia, *gastos_por_dia])
    if hasta is not None:
        fin = max(hasta, inicio)

    puntos = []
    saldo = saldo_inicial.monto
    dia = inicio
    while dia <= fin:
        saldo += ingresos_por_dia[dia] - gastos_por_dia[dia]
        puntos.append(PuntoBalance(dia, ingresos_por_dia[dia], gastos_por_dia[dia], saldo))
        dia += timedelta(days=1)
    return puntos
