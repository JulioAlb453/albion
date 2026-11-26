from datetime import UTC, date, datetime

import pytest

from src.core.domain.errors import ErrorDominio
from src.ingresos.domain.entities.ingreso import CategoriaIngreso, Ingreso
from src.pagos.domain.entities.pago_semanal import EstadoPago, PagoSemanal, inicio_de_semana
from tests.domain.fixtures import AHORA

LUNES = date(2026, 11, 23)  # AHORA es el miércoles 25
DOMINGO = date(2026, 11, 29)


def pago(**cambios) -> PagoSemanal:
    return PagoSemanal(**({"miembro": "  Ana  ", "monto": 1_000_000, "semana": LUNES} | cambios))


class TestInicioDeSemana:
    @pytest.mark.parametrize("dia", [date(2026, 11, d) for d in range(23, 30)])
    def test_de_lunes_a_domingo_es_el_mismo_lunes(self, dia):
        assert inicio_de_semana(dia) == LUNES

    def test_el_lunes_siguiente_empieza_otra(self):
        assert inicio_de_semana(date(2026, 11, 30)) == date(2026, 11, 30)


class TestPagoSemanal:
    def test_se_crea_pendiente_y_limpia_el_nombre(self):
        p = pago()
        assert (p.miembro, p.pagado, p.fecha_pago, p.fin_semana) == ("Ana", 0, None, DOMINGO)
        assert p.estado(AHORA.date()) is EstadoPago.PENDIENTE

    @pytest.mark.parametrize(
        "cambios",
        [dict(miembro="  "), dict(monto=0), dict(semana=date(2026, 11, 24)), dict(pagado=-1)],
    )
    def test_datos_invalidos(self, cambios):
        with pytest.raises(ErrorDominio):
            pago(**cambios)

    def test_pago_parcial_y_completo(self):
        parcial = pago().registrar_pago(400_000, datetime(2026, 11, 24, 20, tzinfo=UTC))
        assert (parcial.pagado, parcial.estado(AHORA.date())) == (400_000, EstadoPago.PARCIAL)
        completo = parcial.registrar_pago(1_000_000, datetime(2026, 11, 26, tzinfo=UTC))
        assert completo.estado(AHORA.date()) is EstadoPago.PAGADO
        assert completo.fecha_pago == datetime(2026, 11, 26, tzinfo=UTC)

    def test_no_se_paga_mas_de_lo_asignado(self):
        with pytest.raises(ErrorDominio, match="asignado"):
            pago().registrar_pago(1_000_001, AHORA)

    @pytest.mark.parametrize("fecha", [datetime(2026, 11, 22, 23, 59, tzinfo=UTC), datetime(2026, 11, 30, tzinfo=UTC)])
    def test_el_pago_debe_caer_en_su_semana(self, fecha):
        with pytest.raises(ErrorDominio, match="semana"):
            pago().registrar_pago(100, fecha)

    def test_volver_a_cero_quita_la_fecha(self):
        corregido = pago().registrar_pago(400_000, AHORA).registrar_pago(0, AHORA)
        assert (corregido.pagado, corregido.fecha_pago) == (0, None)

    def test_lo_no_reclamado_al_terminar_la_semana_queda_para_el_gremio(self):
        parcial = pago().registrar_pago(400_000, AHORA)
        assert parcial.no_reclamado(DOMINGO) == 0  # el domingo todavía se puede cobrar
        lunes_siguiente = date(2026, 11, 30)
        assert parcial.estado(lunes_siguiente) is EstadoPago.NO_RECLAMADO
        assert parcial.no_reclamado(lunes_siguiente) == 600_000
        assert pago().no_reclamado(lunes_siguiente) == 1_000_000
        assert pago(pagado=1_000_000, fecha_pago=AHORA).estado(lunes_siguiente) is EstadoPago.PAGADO


class TestIngreso:
    def test_valido(self):
        ingreso = Ingreso(CategoriaIngreso.DONACION, "  de Ana ", 2_000_000, AHORA)
        assert ingreso.descripcion == "de Ana"

    def test_monto_positivo(self):
        with pytest.raises(ErrorDominio):
            Ingreso(CategoriaIngreso.DONACION, "", 0, AHORA)

    def test_otros_necesita_descripcion(self):
        with pytest.raises(ErrorDominio):
            Ingreso(CategoriaIngreso.OTROS, " ", 10, AHORA)
