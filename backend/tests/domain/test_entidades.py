from datetime import date
from decimal import Decimal

import pytest

from src.alertas.domain.entities.seguimiento import Seguimiento
from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.core.domain.errors import ErrorDominio
from src.core.domain.services.calculadora_impuestos import DesgloseVenta, calcular_desglose
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.gastos.domain.entities.gasto import CategoriaGasto, Gasto
from src.usuarios.domain.entities.usuario import Rol, Usuario
from src.ventas.domain.entities.venta import Venta
from tests.domain.fixtures import AHORA, ESPADA


class TestVenta:
    def test_registrar_calcula_desglose(self):
        venta = Venta.registrar(
            objeto=ESPADA, ciudad=Ciudad.LYMHURST, tipo=TipoVenta.ORDEN,
            cantidad=2, precio_unitario=50_000, fecha=AHORA,
        )
        assert venta.desglose.neto == 93_500
        assert venta.id is None

    def test_el_black_market_tambien_admite_orden_de_venta(self):
        venta = Venta.registrar(
            objeto=ESPADA, ciudad=Ciudad.BLACK_MARKET, tipo=TipoVenta.ORDEN,
            cantidad=2, precio_unitario=50_000, fecha=AHORA,
        )
        assert venta.desglose.neto == 93_500


class TestVentaNoAdmiteEstadosIlegales:
    """El constructor es la otra puerta de entrada (p. ej. al leer de la base de datos)."""

    def construir(self, **cambios):
        datos = dict(
            objeto=ESPADA, ciudad=Ciudad.LYMHURST, tipo=TipoVenta.ORDEN, cantidad=2,
            precio_unitario=50_000, fecha=AHORA,
            desglose=calcular_desglose(50_000, 2, TipoVenta.ORDEN),
        )
        return Venta(**(datos | cambios))

    def test_desglose_de_otro_precio(self):
        with pytest.raises(ErrorDominio):
            self.construir(precio_unitario=60_000)

    def test_venta_directa_con_tarifa(self):
        with pytest.raises(ErrorDominio):
            self.construir(tipo=TipoVenta.DIRECTA)

    def test_desglose_valido_se_acepta(self):
        assert self.construir().desglose.neto == 93_500


class TestDesgloseNoAdmiteEstadosIlegales:
    def test_neto_que_no_cuadra(self):
        with pytest.raises(ErrorDominio):
            DesgloseVenta(bruto=100, impuesto=4, tarifa_publicacion=0, neto=50)

    def test_cargo_negativo(self):
        with pytest.raises(ErrorDominio):
            DesgloseVenta(bruto=100, impuesto=-4, tarifa_publicacion=0, neto=104)


class TestGasto:
    def test_limpia_descripcion(self):
        gasto = Gasto(CategoriaGasto.REPARACIONES, "  ZvZ  ", 500, AHORA)
        assert gasto.descripcion == "ZvZ"

    def test_otros_exige_descripcion(self):
        with pytest.raises(ErrorDominio):
            Gasto(CategoriaGasto.OTROS, " ", 500, AHORA)

    def test_monto_positivo(self):
        with pytest.raises(ErrorDominio):
            Gasto(CategoriaGasto.COMPRA_EQUIPO, "", 0, AHORA)


def test_saldo_inicial_no_negativo():
    with pytest.raises(ErrorDominio):
        SaldoInicial(-1, date(2026, 11, 25))


def test_seguimiento_exige_criterio():
    with pytest.raises(ErrorDominio):
        Seguimiento(ESPADA)
    assert Seguimiento(ESPADA, porcentaje_minimo=Decimal("10")).ciudad_referencia is Ciudad.FORT_STERLING


def test_solo_admin_registra():
    assert Usuario("1", "julio", None, Rol.ADMIN).puede_registrar
    assert not Usuario("2", "general", None, Rol.GENERAL).puede_registrar
