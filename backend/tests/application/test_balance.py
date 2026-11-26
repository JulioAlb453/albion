from datetime import UTC, date, datetime

import pytest

from src.balance.application.configurar_saldo_inicial_use_case import ConfigurarSaldoInicial
from src.balance.application.obtener_evolucion_balance_use_case import ObtenerEvolucionBalance
from src.balance.application.obtener_reportes_use_case import ObtenerReportes
from src.balance.domain.entities.saldo_inicial import SaldoInicial
from src.core.domain.errors import AccesoDenegado, EntidadNoEncontrada, ErrorDominio
from src.core.domain.value_objects.ciudad import Ciudad
from src.core.domain.value_objects.tipo_venta import TipoVenta
from src.gastos.application.datos_gasto import DatosGasto
from src.gastos.application.registrar_gasto_use_case import RegistrarGasto
from src.gastos.domain.entities.gasto import CategoriaGasto
from src.ventas.application.datos_venta import DatosVenta
from src.ventas.application.registrar_venta_use_case import RegistrarVenta
from tests.application.fakes import (
    IngresoRepoMemoria,
    PagoRepoMemoria,
    ADMIN,
    GENERAL,
    GastoRepoMemoria,
    RelojFijo,
    SaldoRepoMemoria,
    VentaRepoMemoria,
)
from tests.domain.fixtures import ESPADA

INICIO = SaldoInicial(120_000_000, date(2026, 11, 25))


def dia(numero, hora=12):
    return datetime(2026, 11, numero, hora, tzinfo=UTC)


class TestConfigurarSaldoInicial:
    def setup_method(self):
        self.repo = SaldoRepoMemoria()
        self.caso = ConfigurarSaldoInicial(self.repo)

    async def test_guarda_el_saldo(self):
        saldo = await self.caso.ejecutar(ADMIN, 120_000_000, date(2026, 11, 25))
        assert saldo == INICIO and self.repo.saldo == INICIO

    async def test_un_general_no_puede_configurarlo(self):
        with pytest.raises(AccesoDenegado):
            await self.caso.ejecutar(GENERAL, 1, date(2026, 11, 25))
        assert self.repo.saldo is None

    async def test_un_saldo_negativo_se_rechaza(self):
        with pytest.raises(ErrorDominio):
            await self.caso.ejecutar(ADMIN, -1, date(2026, 11, 25))


class Movimientos:
    """Ventas y gastos ya registrados, listos para consultar."""

    async def preparar(self, saldo=INICIO, ahora=dia(28, 10)):
        self.saldos = SaldoRepoMemoria(saldo)
        self.ventas = VentaRepoMemoria()
        self.gastos = GastoRepoMemoria()
        self.reloj = RelojFijo(ahora)
        registrar_venta = RegistrarVenta(self.ventas, self.reloj)
        registrar_gasto = RegistrarGasto(self.gastos, self.reloj)
        base = dict(objeto=ESPADA, ciudad=Ciudad.LYMHURST, tipo=TipoVenta.DIRECTA, cantidad=1)
        await registrar_venta.ejecutar(  # neto 960000
            ADMIN, DatosVenta(**base, precio_unitario=1_000_000, fecha=dia(25, 18))
        )
        await registrar_venta.ejecutar(  # neto 96000
            ADMIN, DatosVenta(**base, precio_unitario=100_000, fecha=dia(30))
        )
        await registrar_gasto.ejecutar(
            ADMIN, DatosGasto(CategoriaGasto.REEQUIPAMIENTO_BUILDS, "", 500_000, dia(27, 9))
        )
        await registrar_gasto.ejecutar(  # anterior al saldo inicial: ya está contado en él
            ADMIN, DatosGasto(CategoriaGasto.REPARACIONES, "", 9_999, dia(20))
        )


class TestObtenerEvolucionBalance(Movimientos):
    async def test_sin_saldo_inicial_no_hay_balance(self):
        await self.preparar(saldo=None)
        caso = ObtenerEvolucionBalance(self.saldos, self.ventas, self.gastos, self.reloj, IngresoRepoMemoria(), PagoRepoMemoria())
        with pytest.raises(EntidadNoEncontrada):
            await caso.ejecutar()

    async def test_evoluciona_hasta_hoy_ignorando_lo_anterior_y_lo_futuro(self):
        await self.preparar()
        caso = ObtenerEvolucionBalance(self.saldos, self.ventas, self.gastos, self.reloj, IngresoRepoMemoria(), PagoRepoMemoria())
        puntos = await caso.ejecutar()
        assert [(p.fecha.day, p.saldo) for p in puntos] == [
            (25, 120_960_000), (26, 120_960_000), (27, 120_460_000), (28, 120_460_000)
        ]

    async def test_se_puede_pedir_otra_fecha_final(self):
        await self.preparar()
        caso = ObtenerEvolucionBalance(self.saldos, self.ventas, self.gastos, self.reloj, IngresoRepoMemoria(), PagoRepoMemoria())
        puntos = await caso.ejecutar(hasta=date(2026, 11, 30))
        assert puntos[-1].saldo == 120_556_000


class TestObtenerReportes(Movimientos):
    async def test_resume_todo_el_periodo(self):
        await self.preparar()
        reportes = await ObtenerReportes(self.ventas, self.gastos, IngresoRepoMemoria(), PagoRepoMemoria()).ejecutar()
        assert reportes.ventas_netas == 1_056_000
        assert reportes.gastos_totales == 509_999
        assert reportes.ganancia_por_objeto[0].unidades == 2

    async def test_filtra_por_rango_con_fechas_sin_zona(self):
        await self.preparar()
        reportes = await ObtenerReportes(self.ventas, self.gastos, IngresoRepoMemoria(), PagoRepoMemoria()).ejecutar(
            desde=datetime(2026, 11, 26), hasta=datetime(2026, 12, 1)
        )
        assert reportes.ventas_netas == 96_000
        assert reportes.gastos_totales == 500_000
