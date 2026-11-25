from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from src.alertas.domain.entities.alerta import Alerta
from src.alertas.domain.entities.seguimiento import Seguimiento
from src.alertas.domain.services.evaluador_alertas import evaluar
from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.balance.domain.services.calculadora_balance import calcular_evolucion
from src.core.domain.errors import ErrorDominio
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto
from src.mercado.domain.services.comparador_ventas import comparar_por_ciudad, mejores_opciones
from src.ventas.domain.entities.venta import Venta
from tests.domain.fixtures import AHORA, ESPADA, precio


class TestComparador:
    def test_ordena_por_neto_y_compara_directa_contra_orden(self):
        comparaciones = comparar_por_ciudad(
            [
                precio(Ciudad.FORT_STERLING, venta=100_000, compra=90_000),
                precio(Ciudad.CAERLEON, venta=120_000, compra=95_000),
            ],
            ahora=AHORA,
        )
        assert [c.ciudad for c in comparaciones] == [Ciudad.CAERLEON, Ciudad.FORT_STERLING]
        fort = comparaciones[1]
        # orden: 100000 * 0.935 = 93500 ; directa: 90000 * 0.96 = 86400
        assert fort.diferencia_orden_vs_directa == 7_100
        assert fort.mejor.tipo is TipoVenta.ORDEN

    def test_black_market_solo_directa(self):
        [bm] = comparar_por_ciudad(
            [precio(Ciudad.BLACK_MARKET, venta=200_000, compra=150_000)], ahora=AHORA
        )
        assert bm.orden is None and bm.directa.precio_unitario == 150_000

    def test_descarta_ciudades_sin_datos(self):
        assert comparar_por_ciudad([precio(Ciudad.MARTLOCK)], ahora=AHORA) == []

    def test_marca_datos_viejos_y_los_pone_al_final(self):
        comparaciones = comparar_por_ciudad(
            [
                precio(Ciudad.THETFORD, compra=500_000, hace=timedelta(days=2)),
                precio(Ciudad.LYMHURST, compra=100_000),
            ],
            ahora=AHORA,
        )
        opciones = mejores_opciones(comparaciones)
        assert [o.ciudad for o in opciones] == [Ciudad.LYMHURST, Ciudad.THETFORD]
        assert not opciones[1].confiable

    def test_rechaza_objetos_mezclados(self):
        otra = ObjetoRef("T5_MAIN_SWORD")
        with pytest.raises(ErrorDominio):
            comparar_por_ciudad(
                [precio(Ciudad.LYMHURST, compra=1), precio(Ciudad.CAERLEON, compra=1, objeto=otra)],
                ahora=AHORA,
            )


class TestBalance:
    def test_evolucion_diaria(self):
        inicio = SaldoInicial(120_000_000, date(2026, 11, 25))
        venta = Venta.registrar(
            objeto=ESPADA, ciudad=Ciudad.LYMHURST, tipo=TipoVenta.DIRECTA,
            cantidad=1, precio_unitario=1_000_000, fecha=datetime(2026, 11, 25, 18),
        )
        gasto = Gasto.registrar(
            categoria=CategoriaGasto.REEQUIPAMIENTO_BUILDS, descripcion="",
            monto=500_000, fecha=datetime(2026, 11, 27, 9),
        )
        anterior = Gasto.registrar(
            categoria=CategoriaGasto.REPARACIONES, descripcion="",
            monto=9_999, fecha=datetime(2026, 11, 20),
        )
        puntos = calcular_evolucion(inicio, [venta], [gasto, anterior])
        assert [(p.fecha.day, p.saldo) for p in puntos] == [
            (25, 120_960_000), (26, 120_960_000), (27, 120_460_000)
        ]

    def test_sin_movimientos_hasta_fecha(self):
        inicio = SaldoInicial(120_000_000, date(2026, 11, 25))
        puntos = calcular_evolucion(inicio, [], [], hasta=date(2026, 11, 26))
        assert len(puntos) == 2 and puntos[-1].saldo == 120_000_000


class TestEvaluadorAlertas:
    PRECIOS = [
        precio(Ciudad.FORT_STERLING, compra=100_000),
        precio(Ciudad.BLACK_MARKET, compra=120_000),
    ]

    def comparaciones(self):
        return comparar_por_ciudad(self.PRECIOS, ahora=AHORA)

    def test_alerta_por_porcentaje(self):
        seg = Seguimiento(ESPADA, porcentaje_minimo=Decimal("15"), id=1)
        alerta = evaluar(seg, self.comparaciones(), ultima_alerta=None, ahora=AHORA)
        assert alerta.ciudad is Ciudad.BLACK_MARKET
        assert alerta.neto_unitario == 115_200 and alerta.neto_referencia == 96_000
        assert "20.0%" in alerta.motivo

    def test_no_alerta_bajo_el_umbral(self):
        seg = Seguimiento(ESPADA, porcentaje_minimo=Decimal("25"), id=1)
        assert evaluar(seg, self.comparaciones(), ultima_alerta=None, ahora=AHORA) is None

    def test_alerta_por_neto_minimo(self):
        seg = Seguimiento(ESPADA, neto_minimo=110_000, id=1)
        alerta = evaluar(seg, self.comparaciones(), ultima_alerta=None, ahora=AHORA)
        assert alerta.ciudad is Ciudad.BLACK_MARKET

    def test_respeta_tiempo_de_espera(self):
        seg = Seguimiento(ESPADA, neto_minimo=1, id=1)
        reciente = Alerta(1, Ciudad.LYMHURST, TipoVenta.DIRECTA, 1, None, "", AHORA - timedelta(minutes=30))
        assert evaluar(seg, self.comparaciones(), ultima_alerta=reciente, ahora=AHORA) is None

    def test_ignora_datos_viejos(self):
        viejos = [precio(Ciudad.BLACK_MARKET, compra=999_999, hace=timedelta(days=1))]
        seg = Seguimiento(ESPADA, neto_minimo=1, id=1)
        comparaciones = comparar_por_ciudad(viejos, ahora=AHORA)
        assert evaluar(seg, comparaciones, ultima_alerta=None, ahora=AHORA) is None

    def test_inactivo_no_alerta(self):
        seg = Seguimiento(ESPADA, neto_minimo=1, activo=False, id=1)
        assert evaluar(seg, self.comparaciones(), ultima_alerta=None, ahora=AHORA) is None
