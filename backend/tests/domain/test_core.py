import pytest

from src.core.domain.errors import ErrorDominio
from src.core.domain.services.calculadora_impuestos import (
    TASAS_SIN_PREMIUM,
    calcular_desglose,
)
from src.core.domain.value_objects.calidad import Calidad
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.objeto_ref import ObjetoRef
from src.core.domain.value_objects.tipo_venta import TipoVenta


class TestObjetoRef:
    def test_api_id_con_y_sin_encantamiento(self):
        assert ObjetoRef("T6_MAIN_SWORD", 2).api_id == "T6_MAIN_SWORD@2"
        assert ObjetoRef("T6_MAIN_SWORD").api_id == "T6_MAIN_SWORD"

    def test_desde_api_id(self):
        ref = ObjetoRef.desde_api_id("T8_ARMOR_PLATE_SET1@3", Calidad.OBRA_MAESTRA)
        assert (ref.base_id, ref.tier, ref.encantamiento, ref.etiqueta) == (
            "T8_ARMOR_PLATE_SET1", 8, 3, "T8.3"
        )

    @pytest.mark.parametrize(
        "base_id, encantamiento",
        [("ESPADA", 0), ("T9_MAIN_SWORD", 0), ("T6_MAIN_SWORD@2", 0), ("T6_MAIN_SWORD", 5)],
    )
    def test_rechaza_invalidos(self, base_id, encantamiento):
        with pytest.raises(ErrorDominio):
            ObjetoRef(base_id, encantamiento)


class TestCiudad:
    def test_ciudades_del_gremio(self):
        assert Ciudad.FORT_STERLING.es_del_gremio
        assert not Ciudad.MARTLOCK.es_del_gremio


class TestCalculadoraImpuestos:
    def test_venta_directa_paga_solo_impuesto(self):
        d = calcular_desglose(100_000, 3, TipoVenta.DIRECTA)
        assert (d.bruto, d.impuesto, d.tarifa_publicacion, d.neto) == (300_000, 12_000, 0, 288_000)

    def test_orden_paga_impuesto_y_tarifa(self):
        d = calcular_desglose(100_000, 3, TipoVenta.ORDEN)
        assert (d.impuesto, d.tarifa_publicacion, d.neto) == (12_000, 7_500, 280_500)

    def test_reajustes_suman_tarifa(self):
        d = calcular_desglose(100_000, 1, TipoVenta.ORDEN, tarifa_extra=1_000)
        assert d.tarifa_publicacion == 3_500

    def test_sin_premium(self):
        assert calcular_desglose(100_000, 1, TipoVenta.DIRECTA, TASAS_SIN_PREMIUM).impuesto == 8_000

    def test_redondeo(self):
        # 4% de 37 = 1.48 → 1 ; 2.5% de 37 = 0.925 → 1
        d = calcular_desglose(37, 1, TipoVenta.ORDEN)
        assert (d.impuesto, d.tarifa_publicacion) == (1, 1)

    @pytest.mark.parametrize(
        "precio, cantidad, tipo, extra",
        [(0, 1, TipoVenta.DIRECTA, 0), (10, 0, TipoVenta.DIRECTA, 0), (10, 1, TipoVenta.DIRECTA, 5)],
    )
    def test_rechaza_invalidos(self, precio, cantidad, tipo, extra):
        with pytest.raises(ErrorDominio):
            calcular_desglose(precio, cantidad, tipo, tarifa_extra=extra)
