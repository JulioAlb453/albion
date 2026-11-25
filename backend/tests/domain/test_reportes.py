from datetime import UTC, datetime

from src.balance.domain.services.generador_reportes import (
    gastos_por_categoria,
    generar_reportes,
    ganancia_por_objeto,
    resumir_impuestos,
)
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto
from src.ventas.domain.entities.venta import Venta
from tests.domain.fixtures import AHORA, ESPADA

BOLSA = ObjetoRef("T4_BAG")


def venta(objeto, tipo, cantidad, precio):
    return Venta.registrar(
        objeto=objeto, ciudad=Ciudad.LYMHURST, tipo=tipo,
        cantidad=cantidad, precio_unitario=precio, fecha=AHORA,
    )


VENTAS = [
    venta(ESPADA, TipoVenta.DIRECTA, 2, 100_000),  # neto 192000
    venta(ESPADA, TipoVenta.ORDEN, 1, 100_000),    # neto 93500
    venta(BOLSA, TipoVenta.DIRECTA, 1, 50_000),    # neto 48000
]
GASTOS = [
    Gasto(CategoriaGasto.REPARACIONES, "", 10_000, AHORA),
    Gasto(CategoriaGasto.COMPRA_EQUIPO, "", 300_000, AHORA),
    Gasto(CategoriaGasto.REPARACIONES, "", 5_000, datetime(2026, 11, 26, tzinfo=UTC)),
]


def test_ganancia_por_objeto_suma_y_ordena_por_neto():
    espada, bolsa = ganancia_por_objeto(VENTAS)
    assert (espada.objeto, espada.unidades, espada.bruto) == (ESPADA, 3, 300_000)
    assert (espada.impuesto, espada.tarifa_publicacion, espada.neto) == (12_000, 2_500, 285_500)
    assert (bolsa.objeto, bolsa.neto) == (BOLSA, 48_000)


def test_un_mismo_objeto_con_otra_calidad_es_otra_fila():
    otra_calidad = ObjetoRef("T6_MAIN_SWORD", encantamiento=2)  # ESPADA es calidad Sobresaliente
    filas = ganancia_por_objeto([venta(ESPADA, TipoVenta.DIRECTA, 1, 1_000),
                                 venta(otra_calidad, TipoVenta.DIRECTA, 1, 1_000)])
    assert len(filas) == 2


def test_impuestos_separan_venta_y_publicacion():
    impuestos = resumir_impuestos(VENTAS)
    assert (impuestos.impuesto_venta, impuestos.tarifa_publicacion) == (14_000, 2_500)
    assert impuestos.total == 16_500


def test_gastos_por_categoria_de_mayor_a_menor():
    assert gastos_por_categoria(GASTOS) == {
        CategoriaGasto.COMPRA_EQUIPO: 300_000,
        CategoriaGasto.REPARACIONES: 15_000,
    }
    assert list(gastos_por_categoria(GASTOS)) == [
        CategoriaGasto.COMPRA_EQUIPO, CategoriaGasto.REPARACIONES
    ]


def test_reportes_totales():
    reportes = generar_reportes(VENTAS, GASTOS)
    assert reportes.ventas_netas == 333_500
    assert reportes.gastos_totales == 315_000
    assert reportes.resultado == 18_500


def test_reportes_sin_movimientos():
    reportes = generar_reportes([], [])
    assert reportes.ganancia_por_objeto == [] and reportes.resultado == 0
    assert reportes.impuestos.total == 0
