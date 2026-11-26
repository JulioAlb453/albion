from collections import defaultdict
from collections.abc import Iterable

from src.balance.domain.entities.reportes import GananciaObjeto, Reportes, ResumenImpuestos
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto
from src.ingresos.domain.entities.ingreso import CategoriaIngreso, Ingreso
from src.pagos.domain.entities.pago_semanal import PagoSemanal
from src.ventas.domain.entities.venta import Venta


def ganancia_por_objeto(ventas: Iterable[Venta]) -> list[GananciaObjeto]:
    por_objeto: dict[ObjetoRef, list[Venta]] = defaultdict(list)
    for venta in ventas:
        por_objeto[venta.objeto].append(venta)
    ganancias = [
        GananciaObjeto(
            objeto=objeto,
            unidades=sum(v.cantidad for v in grupo),
            bruto=sum(v.desglose.bruto for v in grupo),
            impuesto=sum(v.desglose.impuesto for v in grupo),
            tarifa_publicacion=sum(v.desglose.tarifa_publicacion for v in grupo),
            neto=sum(v.desglose.neto for v in grupo),
        )
        for objeto, grupo in por_objeto.items()
    ]
    return sorted(ganancias, key=lambda g: g.neto, reverse=True)


def resumir_impuestos(ventas: Iterable[Venta]) -> ResumenImpuestos:
    ventas = list(ventas)
    return ResumenImpuestos(
        impuesto_venta=sum(v.desglose.impuesto for v in ventas),
        tarifa_publicacion=sum(v.desglose.tarifa_publicacion for v in ventas),
    )


def gastos_por_categoria(gastos: Iterable[Gasto]) -> dict[CategoriaGasto, int]:
    totales: dict[CategoriaGasto, int] = defaultdict(int)
    for gasto in gastos:
        totales[gasto.categoria] += gasto.monto
    return dict(sorted(totales.items(), key=lambda par: par[1], reverse=True))


def ingresos_por_categoria(ingresos: Iterable[Ingreso]) -> dict[CategoriaIngreso, int]:
    totales: dict[CategoriaIngreso, int] = defaultdict(int)
    for ingreso in ingresos:
        totales[ingreso.categoria] += ingreso.monto
    return dict(sorted(totales.items(), key=lambda par: par[1], reverse=True))


def generar_reportes(
    ventas: Iterable[Venta],
    gastos: Iterable[Gasto],
    ingresos: Iterable[Ingreso] = (),
    pagos: Iterable[PagoSemanal] = (),
) -> Reportes:
    ventas, gastos = list(ventas), list(gastos)
    return Reportes(
        ganancia_por_objeto=ganancia_por_objeto(ventas),
        impuestos=resumir_impuestos(ventas),
        gastos_por_categoria=gastos_por_categoria(gastos),
        ventas_netas=sum(v.desglose.neto for v in ventas),
        gastos_totales=sum(g.monto for g in gastos),
        ingresos_por_categoria=ingresos_por_categoria(ingresos),
        pagos_semanales=sum(p.pagado for p in pagos),
    )
